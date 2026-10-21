"""Fixed-criterion comparisons; no source I/O, retuning or status promotion."""

import math
from decimal import Decimal, localcontext

from .contract import SCIENTIFIC, Hold, json_bytes
from .reference import (
    STAGES,
    arithmetic_context,
    bin_index,
    checked_edges,
    decimal_summary,
    evaluate,
    ideal_edges,
    row_stream_digest,
    summary,
)


def compare(rows, result, views):
    if (
        result.get("schema_version") != "qs-dmss-external-dimuon/v1"
        or result.get("method") != "cms-dimuon-four-vector-v1"
    ):
        raise Hold("Candidate diagnostic convention differs from the protocol.")
    if any(row.invalid for row in rows):
        raise Hold(
            "Event mapping requires zero admission exclusions; audit invalid controls separately."
        )
    if len(rows) != len(views) or [view["row"] for view in views] != [
        row.number for row in rows
    ]:
        raise Hold("Candidate event identities are incomplete or reordered.")
    if any(
        key not in result or result[key] != value for key, value in SCIENTIFIC.items()
    ):
        raise Hold("Candidate scientific-status fields differ from the contract.")
    edges = checked_edges(result["histogram"]["edges"])
    histogram = result["histogram"]
    if (
        histogram.get("unit") != "GeV"
        or histogram.get("weighted") is not False
        or len(histogram["counts"]) != 60
        or any(type(value) is not int or value < 0 for value in histogram["counts"])
    ):
        raise Hold("Candidate histogram violates the unweighted count contract.")
    tracks = {name: [] for name in ("binary64", "decimal80", "decimal120")}
    failures = []
    counts = [0] * 60
    selected = []
    exclusions = []
    for row, candidate in zip(rows, views):
        values = []
        for name in tracks:
            value = evaluate(row, name)
            tracks[name].append(value)
            values.append(value)
        binary, d80, d120 = values
        reasons = []
        if (
            binary["first_failure"] != candidate["first_failure"]
            or binary["selected"] != candidate["selected"]
        ):
            reasons.append("candidate_binary64_selection_disagreement")
        if any(
            value["first_failure"] != binary["first_failure"]
            or value["selected"] != binary["selected"]
            for value in (d80, d120)
        ):
            reasons.append("higher_precision_selection_disagreement")
        with localcontext(arithmetic_context(120)):
            for key in ("mass", "mass_squared", "scale"):
                with localcontext(arithmetic_context(50)):
                    if +d80[key] != +d120[key]:
                        reasons.append("decimal_precision_instability")
            if candidate["selected"]:
                mass = candidate["mass"]
                if type(mass) is not float or not math.isfinite(mass):
                    raise Hold("Candidate selected mass is not a finite float.")
                difference = abs(Decimal.from_float(mass) ** 2 - d120["mass_squared"])
                allowance = 64 * Decimal(2) ** -52 * d120["scale"]
                if difference > allowance:
                    reasons.append("mass_squared_threshold_exceeded")
            decimal_edges = [Decimal.from_float(edge) for edge in edges]
            exact_edges = [
                Decimal(edge.numerator) / Decimal(edge.denominator)
                for edge in ideal_edges()
            ]
            if binary["selected"]:
                index = bin_index(binary["mass"], edges)
                counts[index] += 1
                selected.append(binary["mass"])
                if candidate["bin"] != index:
                    reasons.append("candidate_binary64_bin_disagreement")
                if any(
                    bin_index(value["mass"], decimal_edges) != index
                    for value in (d80, d120)
                ):
                    reasons.append("higher_precision_bin_disagreement")
                if bin_index(d120["mass"], exact_edges) != index:
                    reasons.append("ideal_edge_bin_disagreement")
        if not binary["selected"]:
            with localcontext(arithmetic_context(120)):
                lower = str(d120["mass"] - Decimal(2))
                upper = str(Decimal(5) - d120["mass"])
            exclusions.append(
                {
                    "data_row": row.number,
                    "physical_line": row.number + 1,
                    "Run": row.tokens["Run"],
                    "Event": row.tokens["Event"],
                    "first_failure": binary["first_failure"],
                    "tokens": row.tokens,
                    "mass_binary64": repr(binary["mass"]),
                    "mass_decimal120": str(d120["mass"]),
                    "mass_margin_lower_GeV": lower,
                    "mass_margin_upper_GeV": upper,
                }
            )
        if reasons:
            record = {
                "data_row": row.number,
                "Run": row.tokens["Run"],
                "Event": row.tokens["Event"],
                "reasons": reasons,
                "candidate": candidate,
                "reference_mass": {
                    "binary64": repr(binary["mass"]),
                    "decimal80": str(d80["mass"]),
                    "decimal120": str(d120["mass"]),
                },
            }
            if len(json_bytes(record)) > 4096:
                raise Hold("Counterexample exceeds its reserved record ceiling.")
            failures.append(record)
        # Retain every collection for this row before either unchanged guard
        # stops evaluation, including a disagreement on the triggering exclusion.
        if len(exclusions) == 33 or len(failures) == 33:
            return {
                "comparison_outcome": "HOLD",
                "complete": False,
                "reason": "exclusion_detail_limit_reached"
                if len(exclusions) == 33
                else "counterexample_limit_reached",
                "processed_rows": row.number,
                "exclusions": exclusions,
                "counterexamples": failures,
                **SCIENTIFIC,
            }
    global_failures = []
    if (
        result["selected_events"] != len(selected)
        or result["histogram"]["counts"] != counts
    ):
        global_failures.append("aggregate_histogram_or_selection_mismatch")
    if result["roundoff_clamped_rows_before_cuts"] != sum(
        value["roundoff_clamped"] for value in tracks["binary64"]
    ):
        global_failures.append("roundoff_accounting_mismatch")
    expected_flow = [
        {"stage": "input_rows", "remaining": len(rows), "rejected": 0},
        {"stage": "valid_values", "remaining": len(rows), "rejected": 0},
    ]
    remaining = len(rows)
    for stage in STAGES:
        rejected = sum(value["first_failure"] == stage for value in tracks["binary64"])
        remaining -= rejected
        expected_flow.append(
            {"stage": stage, "remaining": remaining, "rejected": rejected}
        )
    if result["cut_flow"] != expected_flow or any(
        result["invalid_rows_first_failure"].values()
    ):
        global_failures.append("cut_flow_or_admission_accounting_mismatch")
    summaries = {
        "binary64": summary(selected),
        "decimal120": decimal_summary(
            [value["mass"] for value in tracks["decimal120"] if value["selected"]]
        ),
    }
    with localcontext(arithmetic_context(120)):
        for track, statistics in summaries.items():
            for key, expected in statistics.items():
                actual = result["mass_summary_GeV"].get(key)
                if expected is None:
                    ok = actual is None
                elif type(actual) not in (int, float) or not math.isfinite(actual):
                    ok = False
                else:
                    expected_decimal = (
                        Decimal.from_float(expected)
                        if isinstance(expected, float)
                        else expected
                    )
                    actual_decimal = (
                        Decimal.from_float(actual)
                        if isinstance(actual, float)
                        else Decimal(actual)
                    )
                    ok = abs(actual_decimal - expected_decimal) <= Decimal(
                        "1e-10"
                    ) + Decimal("1e-12") * abs(expected_decimal)
                if not ok:
                    global_failures.append(track + "_summary_" + key + "_mismatch")
    boundary_hold = any(
        any(
            reason.startswith(("higher_precision", "ideal_edge", "decimal_precision"))
            for reason in item["reasons"]
        )
        for item in failures
    )
    return {
        "comparison_outcome": "HOLD"
        if boundary_hold
        else "MISMATCH"
        if failures or global_failures
        else "MATCH",
        "complete": True,
        "input_rows": len(rows),
        "selected": len(selected),
        "histogram_counts": counts,
        "summary_reference_GeV": {
            track: {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in values.items()
            }
            for track, values in summaries.items()
        },
        "exclusions": exclusions,
        "counterexamples": failures,
        "aggregate_failures": global_failures,
        "intermediate_retention": "Source-order digest, summaries, exclusions and counterexamples; not a full per-row value dump",
        "reference_stream_sha256": {
            name: row_stream_digest(rows, values) for name, values in tracks.items()
        },
        **SCIENTIFIC,
    }
