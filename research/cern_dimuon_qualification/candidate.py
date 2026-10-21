"""Read-only candidate adapter; diagnostic row views are not new CMS datasets."""

import csv
import hashlib
import importlib
import io
import subprocess
import zipfile
from pathlib import Path

from .contract import COMMIT, INPUT_SHA256, PROFILE, WHEEL_SHA256, Hold

MODULES = (
    "contracts",
    "storage",
    "admission",
    "analysis",
    "reporting",
    "evidence",
    "cli",
)
IDENTITY_MODULES = {
    f"qs_dmss.external_data.{name}": f"qs_dmss/external_data/{name}.py"
    for name in MODULES
}
IDENTITY_MODULES.update(
    {"qs_dmss.cli": "qs_dmss/cli.py", "qs_dmss": "qs_dmss/__init__.py"}
)


def wheel_identity(path, repository):
    from .retention import read_regular

    data = read_regular(Path(path), 1024 * 1024)
    if hashlib.sha256(data).hexdigest() != WHEEL_SHA256:
        raise Hold("Candidate wheel does not match the approved SHA-256.")
    identities = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for module_name, member_path in IDENTITY_MODULES.items():
            member = archive.getinfo(member_path)
            if member.file_size > 256 * 1024:
                raise Hold("Candidate module exceeds its identity-read ceiling.")
            saved = archive.read(member)
            module = importlib.import_module(module_name)
            # Trusted code introspection only (editable installs may use a
            # Documents junction). Caller wheel/output paths remain literal.
            actual = read_regular(
                Path(module.__file__).resolve(strict=True), 256 * 1024
            )
            if saved != actual:
                raise Hold("Imported candidate bytes differ from the qualified wheel.")
            try:
                blob = subprocess.run(
                    ["git", "show", f"{COMMIT}:src/{member_path}"],
                    cwd=repository,
                    capture_output=True,
                    check=True,
                    timeout=10,
                ).stdout
            except (OSError, subprocess.SubprocessError) as exc:
                raise Hold("Pinned Git module identity could not be checked.") from exc
            if blob != saved:
                raise Hold("Qualified wheel module differs from the pinned Git bytes.")
            identities[member_path] = hashlib.sha256(actual).hexdigest()
    return {
        "wheel_sha256": WHEEL_SHA256,
        "candidate_commit": COMMIT,
        "module_sha256": identities,
        "commit_assertion": "exact module bytes checked against pinned Git objects",
    }


def probe(raw, kind="synthetic"):
    # Imports belong only in this adapter, never in the independent reference.
    from qs_dmss.external_data.admission import AdmittedCSV, admit_csv
    from qs_dmss.external_data.analysis import analyze
    from qs_dmss.external_data.contracts import AnalysisProfile

    if kind not in {"synthetic", "cms-record-5203"}:
        raise Hold("Unknown adapter input kind.")
    if hashlib.sha256(raw).hexdigest() == INPUT_SHA256 and kind != "cms-record-5203":
        raise Hold("Actual CMS bytes must not be relabelled synthetic.")
    admitted = admit_csv(raw, kind)
    if any(admitted.invalid_rows.values()):
        raise Hold(
            "Row-view adapter cannot infer identities of rejected admission rows."
        )
    rows = list(csv.reader(io.StringIO(raw.decode("ascii"))))[1:]
    if len(rows) != admitted.row_count:
        raise Hold("Candidate row mapping differs from the admitted snapshot.")
    names = list(csv.reader(io.StringIO(raw.decode("ascii"))))[0]
    profile = AnalysisProfile(**PROFILE)
    complete = analyze(admitted, profile)
    views = []
    for index, cells in enumerate(rows):
        original = dict(zip(names, cells))
        for name, column in admitted.columns.items():
            expected = (
                original[name] if name.startswith("type") else float(original[name])
            )
            if column[index] != expected:
                raise Hold("Candidate array/source-row correspondence failed.")
        view = AdmittedCSV(
            {key: value[index : index + 1] for key, value in admitted.columns.items()},
            1,
            dict(admitted.invalid_rows),
            admitted.source,
        )
        result = analyze(view, profile)
        first = next(
            (item["stage"] for item in result["cut_flow"] if item["rejected"]), None
        )
        bins = result["histogram"]["counts"]
        views.append(
            {
                "row": index + 1,
                "selected": result["selected_events"] == 1,
                "first_failure": first,
                "mass": result["mass_summary_GeV"]["minimum"],
                "bin": next((i for i, count in enumerate(bins) if count), None),
            }
        )
    if sum(item["selected"] for item in views) != complete["selected_events"]:
        raise Hold("Candidate row views disagree with the whole-run selection.")
    rebuilt = [sum(item["bin"] == i for item in views) for i in range(PROFILE["bins"])]
    if rebuilt != complete["histogram"]["counts"]:
        raise Hold("Candidate row views disagree with the whole-run histogram.")
    return complete, views
