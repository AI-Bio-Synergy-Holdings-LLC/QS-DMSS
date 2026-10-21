"""Closed, versioned contract for the bounded CMS educational dimuon pilot."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_ROWS = 25_000
MAX_BINS = 100
MAX_LINE_BYTES = 4096
MAX_CELL_BYTES = 128
MAX_RECORD_BYTES = 256 * 1024
MAX_RECEIPT_BYTES = 16 * 1024
MAX_BUNDLE_BYTES = MAX_INPUT_BYTES + 512 * 1024
MAX_RETAINED_BYTES = 10 * 1024 * 1024
METHOD = "cms-dimuon-four-vector-v1"
SCHEMA = "qs-dmss-external-dimuon/v1"
HEADER = (
    "Run",
    "Event",
    "type1",
    "E1",
    "px1",
    "py1",
    "pz1",
    "pt1",
    "eta1",
    "phi1",
    "Q1",
    "type2",
    "E2",
    "px2",
    "py2",
    "pz2",
    "pt2",
    "eta2",
    "phi2",
    "Q2",
)
SOURCE = {
    "record_url": "https://opendata.cern.ch/record/5203",
    "title": "J/psi to two muons from 2011",
    "creator": "Thomas McCauley",
    "license": "CC0-1.0",
    "doi": None,
    "file": "Jpsimumu.csv",
    "size_bytes": 2639302,
    "adler32": "214e4077",
    "maintainer_observed_sha256": "95bf87f7c14758b445d9cb76bc0111affc1ce70831453dde34f687310685e59f",
    "events": 20000,
    "file_version": "0afc5f87-176f-4b4b-855b-5bd568dc1b3d",
    "metadata_checked": "2026-10-20",
    "selection": "Both |eta| < 2.4; at least one global muon; opposite charges; 2 < m < 5 GeV.",
    "endorsement": "Neither CMS nor CERN endorses this derived work.",
}
LIMITATIONS = [
    "Educational, preselected dimuon data; not suitable for a full physics analysis.",
    "A peak in this selected sample is not an independent discovery or cross-section measurement.",
    "No detector calibration, efficiency correction, background fit, uncertainty model or event weights.",
    "Rounded CSV four-vectors can differ from the original selection near cut boundaries.",
    "No physical validation of QS-DMSS, graph model, continuum convergence or quantum advantage.",
    "Content hashes establish retained-byte integrity, not authorship or scientific correctness.",
    "Independent scientific review and human disposition remain pending; gate #183 is unchanged.",
]


class EvidenceError(ValueError):
    """Bounded, authored error; never interpolate raw input into its message."""


def validate_hash(value: str | None, length: int, label: str) -> None:
    if value is not None and (
        not isinstance(value, str)
        or re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None
    ):
        raise EvidenceError(f"{label} must be a full lowercase hexadecimal identity.")


@dataclass(frozen=True)
class AnalysisProfile:
    bins: int = 60
    mass_min: float = 2.0
    mass_max: float = 5.0
    pt_min: float = 0.0

    def __post_init__(self):
        if type(self.bins) is not int or not 1 <= self.bins <= MAX_BINS:
            raise EvidenceError("Histogram bins must be an integer from 1 to 100.")
        if any(
            type(value) not in (int, float)
            or (type(value) is float and not math.isfinite(value))
            for value in (self.mass_min, self.mass_max, self.pt_min)
        ):
            raise EvidenceError("Analysis thresholds must be finite numbers.")
        if (
            not 2 <= self.mass_min < self.mass_max <= 5
            or not 0 <= self.pt_min <= 10_000
        ):
            raise EvidenceError(
                "Mass window must lie within [2, 5] GeV; pt minimum within [0, 10000] GeV."
            )

    def document(self) -> dict:
        return {
            "schema_version": SCHEMA,
            "method": METHOD,
            **asdict(self),
            "units": "Natural units c=1; energy, momentum and mass in GeV; eta dimensionless; phi radians.",
            "mass_formula": "sqrt((E1+E2)^2 - (px1+px2)^2 - (py1+py2)^2 - (pz1+pz2)^2)",
            "mass_squared_roundoff": "Clamp only [-64*eps*max(E_sum^2+p_sum^2,1),0); reject more negative values.",
            "source_cuts": SOURCE["selection"],
            "analysis_cuts": "Both pt >= pt_min, then mass_min < recomputed mass < mass_max.",
            "histogram": "Unweighted counts; left-closed bins, final bin right-closed; strict selection window.",
            "invalid_rows": "Exclude with first-failure reason; never silently impute numeric data.",
        }
