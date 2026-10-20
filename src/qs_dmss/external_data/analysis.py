"""Unweighted four-vector reconstruction; source and analysis cut flows stay visible."""

from __future__ import annotations

import numpy as np

from qs_dmss.external_data.admission import AdmittedCSV
from qs_dmss.external_data.contracts import METHOD, SCHEMA, AnalysisProfile


def analyze(data: AdmittedCSV, profile: AnalysisProfile) -> dict:
    c = data.columns
    energy2 = (c["E1"] + c["E2"]) ** 2
    momentum2 = sum((c[f"{axis}1"] + c[f"{axis}2"]) ** 2 for axis in ("px", "py", "pz"))
    mass2 = energy2 - momentum2
    tolerance = 64 * np.finfo(np.float64).eps * np.maximum(energy2 + momentum2, 1.0)
    physical = mass2 >= -tolerance
    clamped = physical & (mass2 < 0)
    mass = np.sqrt(np.maximum(mass2, 0))
    valid_count = len(mass)
    stages = [{"stage": "input_rows", "remaining": data.row_count, "rejected": 0}]
    stages.append(
        {
            "stage": "valid_values",
            "remaining": valid_count,
            "rejected": data.row_count - valid_count,
        }
    )
    selected = np.ones(valid_count, dtype=bool)

    def cut(name, condition):
        nonlocal selected
        previous = int(np.count_nonzero(selected))
        selected &= condition
        remaining = int(np.count_nonzero(selected))
        stages.append(
            {"stage": name, "remaining": remaining, "rejected": previous - remaining}
        )

    cut("nonnegative_mass_squared_with_roundoff_policy", physical)
    cut(
        "source_both_abs_eta_below_2_4",
        (np.abs(c["eta1"]) < 2.4) & (np.abs(c["eta2"]) < 2.4),
    )
    cut("source_at_least_one_global_muon", (c["type1"] == "G") | (c["type2"] == "G"))
    cut("source_opposite_sign", c["Q1"] * c["Q2"] == -1)
    cut("source_strict_mass_2_to_5_GeV", (mass > 2) & (mass < 5))
    cut(
        "analysis_both_pt_minimum",
        (c["pt1"] >= profile.pt_min) & (c["pt2"] >= profile.pt_min),
    )
    cut(
        "analysis_strict_mass_window",
        (mass > profile.mass_min) & (mass < profile.mass_max),
    )
    values = mass[selected]
    counts, edges = np.histogram(
        values, bins=profile.bins, range=(profile.mass_min, profile.mass_max)
    )
    return {
        "schema_version": SCHEMA,
        "method": METHOD,
        "workflow_outcome": "COMPLETED"
        if len(values)
        else "COMPLETED_NO_SELECTED_EVENTS",
        "scientific_validation_status": "NOT_ESTABLISHED",
        "independent_scientific_review": "PENDING",
        "human_disposition": "PENDING",
        "ai_advice": None,
        "cut_flow": stages,
        "invalid_rows_first_failure": data.invalid_rows,
        "roundoff_clamped_rows_before_cuts": int(np.count_nonzero(clamped)),
        "selected_events": int(len(values)),
        "mass_summary_GeV": {
            "minimum": float(np.min(values)) if len(values) else None,
            "maximum": float(np.max(values)) if len(values) else None,
            "mean": float(np.mean(values)) if len(values) else None,
            "population_std": float(np.std(values)) if len(values) else None,
        },
        "histogram": {
            "unit": "GeV",
            "counts": counts.tolist(),
            "edges": edges.tolist(),
            "weighted": False,
        },
    }
