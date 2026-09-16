"""
DEMO / SYNTHETIC morphodynamic output generator.

This script does NOT run XBeach. It exists solely so that
erosion_accretion_rates.py and make_publication_plots.py can be exercised and
verified end-to-end in an environment where the compiled XBeach binary is not
available (see root README.md). Every output file from this script has
is_synthetic=True baked in, and every figure/table produced downstream from
it is watermarked "DEMO / SYNTHETIC DATA" -- do not present these numbers as
real modeling results.

Method: takes the idealized Dean profile from model/build_bathymetry.py and
translates it landward over a 1-year time series using a Bruun-rule-like
cumulative retreat curve, calibrated so the resulting shoreline-change-rate
diagnostic reproduces the literature "regional background rate" target for
the chosen scenario (see literature/parameters_from_literature.yaml). A
seasonal oscillation (accretion in the Jan-Feb calm season, erosion in the
Jul-Aug high-wave season, per the wave-climate literature) and transect-
dependent noise are superimposed; the transect nearest the inlet gets
amplified swings, reflecting the Jayson-Quashigah et al. (2019) finding that
Fuveme itself swings between strong erosion and accretion episodes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "model"))
from build_bathymetry import build_transect  # noqa: E402

LIT_PARAMS_PATH = Path(__file__).resolve().parent.parent / "literature" / "parameters_from_literature.yaml"
RUNS_DIR = Path(__file__).resolve().parent.parent / "results" / "demo_runs"

N_DAYS = 365
N_TRANSECTS = 5
ALONGSHORE_SPACING_M = 500.0

SCENARIO_TARGET_RATE_M_PER_YR = {
    # negative = net erosion (landward retreat), matching the literature sign
    # convention. Baseline = regional_background_rate_used_as_default_target.
    "baseline": -3.5,
    "slr_2050_rcp45": -3.5,   # + one-off Bruun-rule step from SLR, added separately
    "slr_2100_rcp85_subsidence": -3.5,
    "mangrove_nbs_intertidal": -3.5 * (1 - 0.97),
    "mangrove_nbs_berm": -3.5 * (1 - 0.53),
}
SCENARIO_SLR_M = {
    "baseline": 0.0,
    "slr_2050_rcp45": 0.25,
    "slr_2100_rcp85_subsidence": 1.1,
    "mangrove_nbs_intertidal": 0.0,
    "mangrove_nbs_berm": 0.0,
}
# SLR-driven (Bruun-rule) retreat accrues over decades, not within one
# simulated year -- each scenario's one-off retreat step is phased in over
# its horizon (years from ~now to the scenario's target date) so a single
# 1-year demo run only shows the corresponding annual increment.
SCENARIO_HORIZON_YEARS = {
    "baseline": 1.0,
    "slr_2050_rcp45": 25.0,
    "slr_2100_rcp85_subsidence": 75.0,
    "mangrove_nbs_intertidal": 1.0,
    "mangrove_nbs_berm": 1.0,
}
BEACH_SLOPE_TAN_BETA = 0.02  # typical gentle Lower Volta Delta beach slope (Fuveme reported as gentle/wide)


def seasonal_oscillation_m(day_of_year: np.ndarray, amplitude_m: float = 4.0) -> np.ndarray:
    # peak erosion (max retreat contribution) around day ~200 (mid-Jul), matches
    # high-wave season (Jul-Aug); calm-season accretion around day ~35 (early Feb)
    phase = 2 * np.pi * (day_of_year - 35) / 365.0
    return -amplitude_m / 2.0 * (1 - np.cos(phase))  # 0 at calm season, -amplitude at storm season


def build_scenario_transects(scenario: str, lit: dict, seed_base: int = 100):
    target_rate = SCENARIO_TARGET_RATE_M_PER_YR[scenario]
    slr_m = SCENARIO_SLR_M[scenario]
    horizon_years = SCENARIO_HORIZON_YEARS[scenario]
    bruun_step_total_m = slr_m / BEACH_SLOPE_TAN_BETA  # total Bruun-rule retreat by the scenario's horizon
    bruun_annual_increment_m = bruun_step_total_m / horizon_years  # this simulated year's share of it

    d50_lo, d50_hi = lit["sediment_grain_size"]["D50_mm"]
    time_days = np.arange(N_DAYS + 1)
    t_years = time_days / 365.0

    out_paths = []
    for i in range(N_TRANSECTS):
        rng = np.random.default_rng(seed_base + i)
        frac = i / max(N_TRANSECTS - 1, 1)
        d50 = d50_lo + frac * (d50_hi - d50_lo)
        transect_id = f"T{i+1:02d}"

        profile0 = build_transect(transect_id, alongshore_offset_m=i * ALONGSHORE_SPACING_M,
                                   grain_size_mm=d50, slr_m=slr_m)
        x0, zb0 = profile0["x"], profile0["zb"]

        is_inlet_adjacent = (i == 0)  # T01 = westernmost, nearest the Volta mouth
        noise_scale = 3.0 if is_inlet_adjacent else 1.0

        base_trend = (-target_rate) * t_years  # cumulative retreat (m); positive since target_rate < 0 for erosion
        bruun_ramp = bruun_annual_increment_m * t_years  # this year's share of the multi-decade Bruun-rule retreat

        seasonal = seasonal_oscillation_m(time_days % 365, amplitude_m=2.5 * noise_scale)
        seasonal = -seasonal  # convert "erosion contribution" sign into retreat-positive convention
        random_walk = np.cumsum(rng.normal(0, 0.15 * noise_scale, size=len(time_days)))

        cumulative_retreat_m = base_trend + bruun_ramp + seasonal + random_walk

        zb = np.empty((len(time_days), len(x0)))
        for k, retreat in enumerate(cumulative_retreat_m):
            zb[k, :] = np.interp(x0 - retreat, x0, zb0, left=zb0[0], right=zb0[-1])

        out_path = RUNS_DIR / scenario / f"{transect_id}.npz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            out_path,
            time_days=time_days,
            x=x0,
            zb=zb,
            transect_id=transect_id,
            alongshore_offset_m=i * ALONGSHORE_SPACING_M,
            scenario=scenario,
            is_synthetic=True,
            target_rate_m_per_yr=target_rate,
            D50_mm=d50,
        )
        out_paths.append(out_path)
    return out_paths


def main():
    with open(LIT_PARAMS_PATH) as f:
        lit = yaml.safe_load(f)

    all_paths = []
    for scenario in SCENARIO_TARGET_RATE_M_PER_YR:
        paths = build_scenario_transects(scenario, lit)
        all_paths.extend(paths)
        print(f"[DEMO/SYNTHETIC] wrote {len(paths)} transect files for scenario '{scenario}' -> {RUNS_DIR / scenario}")

    print(f"\nTotal: {len(all_paths)} synthetic run files under {RUNS_DIR}")
    print("These are NOT XBeach results. Run analysis/erosion_accretion_rates.py")
    print("and analysis/make_publication_plots.py against them to verify the")
    print("pipeline, then re-point both at real xboutput.nc files once XBeach")
    print("has actually been run (see root README.md).")


if __name__ == "__main__":
    main()
