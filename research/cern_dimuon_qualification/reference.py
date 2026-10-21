"""Independent scalar reference. Pure bytes in, values out; no file/solver access."""

import bisect
import csv
import hashlib
import math
import re
from dataclasses import dataclass
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    Underflow,
    localcontext,
)
from fractions import Fraction

from .contract import PROFILE, Hold

HEADER = tuple(
    "Run Event type1 E1 px1 py1 pz1 pt1 eta1 phi1 Q1 "
    "type2 E2 px2 py2 pz2 pt2 eta2 phi2 Q2".split()
)
NUMERIC = tuple(key for key in HEADER if key not in {"Run", "Event", "type1", "type2"})
STAGES = (
    "nonnegative_mass_squared_with_roundoff_policy",
    "source_both_abs_eta_below_2_4",
    "source_at_least_one_global_muon",
    "source_opposite_sign",
    "source_strict_mass_2_to_5_GeV",
    "analysis_both_pt_minimum",
    "analysis_strict_mass_window",
)


@dataclass
class Row:
    number: int
    tokens: dict
    invalid: str | None


def parse(raw):
    if len(raw) > 4 * 1024 * 1024:
        raise Hold("Reference input exceeds its byte ceiling.")
    try:
        text = raw.decode("ascii")
    except UnicodeError as exc:
        raise Hold("Reference input is not ASCII.") from exc
    if any(ord(c) < 32 and c not in "\r\n" for c in text):
        raise Hold("Reference input contains control characters.")
    lines = text.splitlines()
    if not 2 <= len(lines) <= 25001 or any(len(line) > 4096 for line in lines):
        raise Hold("Reference line/row policy refused input.")
    result = []
    try:
        if tuple(next(csv.reader([lines[0]], strict=True))) != HEADER:
            raise Hold("Reference header differs from the closed format.")
        for number, line in enumerate(lines[1:], 1):
            cells = next(csv.reader([line], strict=True))
            if len(cells) != len(HEADER) or any(len(cell) > 128 for cell in cells):
                raise Hold("Reference row/cell structure is invalid.")
            tokens = dict(zip(HEADER, cells))
            invalid = invalid_reason(tokens)
            result.append(Row(number, tokens, invalid))
    except csv.Error as exc:
        raise Hold("Reference CSV structure is invalid.") from exc
    return result


def invalid_reason(tokens):
    try:
        numbers = {key: float(tokens[key]) for key in NUMERIC}
    except ValueError:
        return "invalid_numeric"
    if any(not math.isfinite(n) or abs(n) > 1e6 for n in numbers.values()):
        return "nonfinite_or_out_of_range"
    ids_ok = all(
        re.fullmatch(r"[0-9]{1,19}", tokens[key]) is not None
        and int(tokens[key]) <= 2**63 - 1
        for key in ("Run", "Event")
    )
    if not ids_ok or any(
        tokens[f"type{i}"] not in ("G", "T")
        or numbers[f"Q{i}"] not in (-1, 1)
        or numbers[f"E{i}"] <= 0
        or numbers[f"pt{i}"] < 0
        for i in (1, 2)
    ):
        return "invalid_category_or_identity"
    return None


def arithmetic_context(precision):
    context = Context(prec=precision, rounding=ROUND_HALF_EVEN)
    context.traps[Underflow] = True
    return context


def evaluate(row, track="binary64"):
    try:
        return _evaluate(row, track)
    except (DecimalException, OverflowError) as exc:
        raise Hold("Reference arithmetic range refused a row.") from exc


def _evaluate(row, track):
    if track not in ("binary64", "decimal80", "decimal120"):
        raise Hold("Unknown reference arithmetic track.")
    if row.invalid:
        return {"row": row.number, "first_failure": row.invalid, "selected": False}
    with localcontext(arithmetic_context(80 if track == "decimal80" else 120)):
        cast = float if track == "binary64" else Decimal
        n = {key: cast(row.tokens[key]) for key in NUMERIC}
        e2 = (n["E1"] + n["E2"]) ** 2
        p2 = sum((n[f"{axis}1"] + n[f"{axis}2"]) ** 2 for axis in ("px", "py", "pz"))
        m2 = e2 - p2
        scale = max(e2 + p2, cast(1))
        tolerance = 64 * cast(2) ** -52 * scale
        mass = (
            math.sqrt(max(m2, 0)) if track == "binary64" else max(m2, Decimal(0)).sqrt()
        )
        tests = (
            m2 >= -tolerance,
            abs(n["eta1"]) < cast("2.4") and abs(n["eta2"]) < cast("2.4"),
            row.tokens["type1"] == "G" or row.tokens["type2"] == "G",
            n["Q1"] * n["Q2"] == -1,
            cast(2) < mass < cast(5),
            n["pt1"] >= 0 and n["pt2"] >= 0,
            cast(2) < mass < cast(5),
        )
        first = next((stage for stage, ok in zip(STAGES, tests) if not ok), None)
        return {
            "row": row.number,
            "first_failure": first,
            "selected": first is None,
            "mass": mass,
            "mass_squared": m2,
            "scale": scale,
            "roundoff_clamped": -tolerance <= m2 < 0,
        }


def ideal_edges():
    return [
        Fraction(2) + Fraction(3 * i, PROFILE["bins"])
        for i in range(PROFILE["bins"] + 1)
    ]


def checked_edges(edges):
    expected = ideal_edges()
    if (
        type(edges) is not list
        or len(edges) != len(expected)
        or any(type(x) is not float or not math.isfinite(x) for x in edges)
    ):
        raise Hold("Invalid histogram edge representation.")
    if edges[0] != 2.0 or edges[-1] != 5.0:
        raise Hold("Histogram endpoints changed.")
    if any(a >= b for a, b in zip(edges, edges[1:])):
        raise Hold("Histogram edges are not strictly increasing.")
    if any(
        abs(value - float(exact)) > math.ulp(float(exact))
        for value, exact in zip(edges, expected)
    ):
        raise Hold("Histogram edge exceeds the one-ULP criterion.")
    return edges


def bin_index(mass, edges):
    if mass < edges[0] or mass > edges[-1]:
        return None
    return min(bisect.bisect_right(edges, mass) - 1, len(edges) - 2)


def summary(values):
    if not values:
        return {key: None for key in ("minimum", "maximum", "mean", "population_std")}
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / len(values)
    return {
        "minimum": min(values),
        "maximum": max(values),
        "mean": mean,
        "population_std": math.sqrt(variance),
    }


def decimal_summary(values):
    if not values:
        return dict.fromkeys(("minimum", "maximum", "mean", "population_std"))
    with localcontext(arithmetic_context(120)):
        mean = sum(values, Decimal(0)) / len(values)
        variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / len(
            values
        )
        return {
            "minimum": min(values),
            "maximum": max(values),
            "mean": mean,
            "population_std": variance.sqrt(),
        }


def row_stream_digest(rows, evaluations):
    """Digest intermediates in source order; no claim to retain a full row dump."""
    digest = hashlib.sha256()
    for row, value in zip(rows, evaluations):
        mass = value.get("mass")
        record = (
            row.number,
            row.tokens["Run"],
            row.tokens["Event"],
            value["first_failure"],
            mass.hex() if isinstance(mass, float) else str(mass),
        )
        digest.update((repr(record) + "\n").encode("ascii"))
    return digest.hexdigest()
