"""Versioned pilot contract. New diagnostic IDs require a reviewed core change."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

MAX_FILE_BYTES = 64 * 1024
MAX_CASES = 32
MAX_GRID_CELLS = 16384
MAX_TOTAL_GRID_CELLS = 65536
MAX_BUNDLE_BYTES = 512 * 1024
CONVENTION = "fft_cell_measure_v2"
DIAGNOSTIC = "fft_plane_wave_energy_v1"
ACCEPTANCE_SUITE = "fft_plane_wave_pack_contract_v1"

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,63}$", max_length=64)]
Version = Annotated[
    str,
    Field(
        pattern=r"^(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})$",
        max_length=14,
    ),
]
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$", max_length=64)]
GridSize = Annotated[StrictInt, Field(ge=8, le=128)]
Mode = Annotated[StrictInt, Field(ge=-63, le=63)]
PositiveScale = Annotated[float, Field(ge=0.1, le=100.0)]
Tolerance = Annotated[float, Field(ge=1e-14, le=1e-9)]


class ClosedModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, allow_inf_nan=False
    )


def version_tuple(version: str) -> tuple[int, ...]:
    if (
        not isinstance(version, str)
        or re.fullmatch(
            r"(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})", version
        )
        is None
    ):
        raise ValueError("Stable three-component version required.")
    return tuple(int(part) for part in version.split("."))


class CoreVersions(ClosedModel):
    min_inclusive: Version
    max_exclusive: Version

    @model_validator(mode="after")
    def ordered(self):
        if version_tuple(self.min_inclusive) >= version_tuple(self.max_exclusive):
            raise ValueError("Core-version interval must be nonempty.")
        return self


class ResourceLimits(ClosedModel):
    max_file_bytes: Annotated[StrictInt, Field(ge=1, le=MAX_FILE_BYTES)]
    max_cases: Annotated[StrictInt, Field(ge=1, le=MAX_CASES)]
    max_grid_cells: Annotated[StrictInt, Field(ge=64, le=MAX_GRID_CELLS)]
    max_total_grid_cells: Annotated[StrictInt, Field(ge=64, le=MAX_TOTAL_GRID_CELLS)]


class Content(ClosedModel):
    path: Literal["cases.json"]
    sha256: SHA256


class PackManifest(ClosedModel):
    schema_version: Literal["qs-dmss-diagnostic-pack/v1"]
    pack_id: Identifier
    pack_type: Literal["diagnostic"]
    version: Version
    title: Annotated[str, Field(min_length=1, max_length=160)]
    description: Annotated[str, Field(min_length=1, max_length=1024)]
    supported_core_versions: CoreVersions
    required_diagnostic_conventions: tuple[Literal["fft_cell_measure_v2"]] = Field(
        strict=False
    )
    dependencies: tuple[str, ...] = Field(strict=False, max_length=0)
    license: Literal["Apache-2.0", "CC0-1.0"]
    attribution: Annotated[str, Field(min_length=1, max_length=512)]
    source: Annotated[str, Field(min_length=1, max_length=512)]
    redistribution: Literal["permitted_under_declared_license"]
    resource_limits: ResourceLimits
    evidence_schema_version: Literal["qs-dmss-diagnostic-pack-result/v1"]
    diagnostic_id: Literal["fft_plane_wave_energy_v1"]
    acceptance_suite: Literal["fft_plane_wave_pack_contract_v1"]
    content: Content


class PlaneWaveCase(ClosedModel):
    case_id: Identifier
    grid_shape: tuple[GridSize, GridSize] = Field(strict=False)
    box_size: PositiveScale
    mass: PositiveScale
    modes: tuple[Mode, Mode] = Field(strict=False)
    expected_energy: Annotated[float, Field(ge=0.0, le=1e8)]
    absolute_tolerance: Tolerance
    relative_tolerance: Tolerance

    @model_validator(mode="after")
    def resolved_modes(self):
        if any(
            2 * abs(mode) >= size for mode, size in zip(self.modes, self.grid_shape)
        ):
            raise ValueError("Modes must be strictly below Nyquist on both axes.")
        return self


class PackCases(ClosedModel):
    schema_version: Literal["qs-dmss-diagnostic-pack-cases/v1"]
    cases: tuple[PlaneWaveCase, ...] = Field(
        strict=False, min_length=1, max_length=MAX_CASES
    )

    @model_validator(mode="after")
    def unique_ids(self):
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("Case IDs must be unique.")
        return self
