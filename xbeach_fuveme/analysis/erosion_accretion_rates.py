"""
Compute erosion/accretion volumes and annualized rates from XBeach-style
morphodynamic output (real xboutput.nc or the demo synthetic .npz files).

Sign convention (matches the literature table in
literature/parameters_from_literature.yaml): NEGATIVE = erosion / landward
retreat, POSITIVE = accretion / seaward progradation.

Two diagnostics are computed per transect:
  1. Shoreline position change rate (m/yr): position of the zb=0 (MSL)
     contour over time, linear-regressed against time in years.
  2. Volumetric sediment budget rate (m3/m/yr): time derivative of the
     cross-shore-integrated bed volume within the active profile window,
     linear-regressed against time in years. Multiplying by alongshore
     spacing gives a reach-total annual sediment budget (m3/yr).
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats

from xbeach_io import load_run

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@dataclass
class TransectRateResult:
    scenario: str
    transect_id: str
    alongshore_offset_m: float
    shoreline_rate_m_per_yr: float
    shoreline_rate_r2: float
    volume_rate_m3_per_m_per_yr: float
    volume_rate_r2: float
    classification: str
    is_synthetic: bool


def shoreline_position(x: np.ndarray, zb: np.ndarray, contour_level: float = 0.0) -> float:
    """Cross-shore position (m) of the first zb=contour_level crossing,
    scanning from the landward end backward (finds the beach-face crossing,
    not an offshore bar crossing at the same level)."""
    zb_shift = zb - contour_level
    sign_change = np.where(np.diff(np.sign(zb_shift)) != 0)[0]
    if len(sign_change) == 0:
        return np.nan
    idx = sign_change[-1]  # landward-most crossing = the beach face / shoreline
    x0, x1 = x[idx], x[idx + 1]
    z0, z1 = zb_shift[idx], zb_shift[idx + 1]
    if z1 == z0:
        return x0
    frac = -z0 / (z1 - z0)
    return x0 + frac * (x1 - x0)


def active_profile_volume(x: np.ndarray, zb: np.ndarray, x_window: tuple[float, float] | None = None) -> float:
    """Cross-shore integral of bed level (m2 per running alongshore meter)
    over the active profile window (defaults to the full domain)."""
    if x_window is not None:
        mask = (x >= x_window[0]) & (x <= x_window[1])
        x, zb = x[mask], zb[mask]
    trapz = getattr(np, "trapezoid", None) or np.trapz
    return float(trapz(zb, x))


def linregress_rate(t_years: np.ndarray, series: np.ndarray) -> tuple[float, float]:
    res = stats.linregress(t_years, series)
    return float(res.slope), float(res.rvalue ** 2)


def analyze_run(npz_or_nc_path: Path) -> TransectRateResult:
    run = load_run(npz_or_nc_path)
    x, zb, t_days = run["x"], run["zb"], run["time_days"]
    t_years = t_days / 365.0

    shoreline_x = np.array([shoreline_position(x, zb[k, :]) for k in range(zb.shape[0])])
    shoreline_slope, shoreline_r2 = linregress_rate(t_years, shoreline_x)
    # x increases landward in this repo's convention -> a positive slope
    # (position moving landward over time) is EROSION, so negate to match
    # the literature sign convention (negative = erosion).
    shoreline_rate = -shoreline_slope

    volumes = np.array([active_profile_volume(x, zb[k, :]) for k in range(zb.shape[0])])
    volume_slope, volume_r2 = linregress_rate(t_years, volumes)

    classification = "erosion" if shoreline_rate < 0 else "accretion"

    return TransectRateResult(
        scenario=run["scenario"],
        transect_id=run["transect_id"],
        alongshore_offset_m=run["alongshore_offset_m"],
        shoreline_rate_m_per_yr=round(shoreline_rate, 3),
        shoreline_rate_r2=round(shoreline_r2, 3),
        volume_rate_m3_per_m_per_yr=round(volume_slope, 3),
        volume_rate_r2=round(volume_r2, 3),
        classification=classification,
        is_synthetic=run["is_synthetic"],
    )


def analyze_scenario_dir(scenario_dir: Path) -> pd.DataFrame:
    paths = sorted(scenario_dir.glob("*.npz")) + sorted(scenario_dir.glob("*.nc"))
    results = [analyze_run(p) for p in paths]
    return pd.DataFrame([asdict(r) for r in results])


def reach_total_budget(df: pd.DataFrame, alongshore_spacing_m: float = 500.0) -> dict:
    """Aggregate per-transect volumetric rates into a total sediment budget
    for the modeled reach, assuming each transect represents a half-spacing
    buffer on either side (standard DSAS/beach-profile aggregation)."""
    total_m3_per_yr = float((df["volume_rate_m3_per_m_per_yr"] * alongshore_spacing_m).sum())
    reach_length_m = alongshore_spacing_m * len(df)
    return {
        "total_volume_rate_m3_per_yr": round(total_m3_per_yr, 1),
        "reach_length_m": reach_length_m,
        "mean_shoreline_rate_m_per_yr": round(float(df["shoreline_rate_m_per_yr"].mean()), 3),
    }


def main():
    demo_runs_dir = RESULTS_DIR / "demo_runs"
    if not demo_runs_dir.exists():
        raise SystemExit(
            f"No runs found at {demo_runs_dir}. Run analysis/demo_synthetic_run.py "
            "first (for pipeline testing) or point this script at a directory of "
            "real xboutput.nc files."
        )

    all_rows = []
    summary_rows = []
    for scenario_dir in sorted(demo_runs_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        df = analyze_scenario_dir(scenario_dir)
        if df.empty:
            continue
        all_rows.append(df)
        budget = reach_total_budget(df)
        budget["scenario"] = scenario_dir.name
        summary_rows.append(budget)
        print(f"\nScenario: {scenario_dir.name}")
        print(df.to_string(index=False))
        print(f"  reach total volume rate: {budget['total_volume_rate_m3_per_yr']:.0f} m3/yr "
              f"over {budget['reach_length_m']:.0f} m alongshore "
              f"(mean shoreline rate {budget['mean_shoreline_rate_m_per_yr']:.2f} m/yr)")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    per_transect_df = pd.concat(all_rows, ignore_index=True)
    per_transect_df.to_csv(RESULTS_DIR / "annual_rates_per_transect.csv", index=False)
    pd.DataFrame(summary_rows).to_csv(RESULTS_DIR / "annual_rates_reach_summary.csv", index=False)
    print(f"\nWrote {RESULTS_DIR / 'annual_rates_per_transect.csv'}")
    print(f"Wrote {RESULTS_DIR / 'annual_rates_reach_summary.csv'}")
    if per_transect_df["is_synthetic"].any():
        print("\n*** NOTE: these numbers come from DEMO/SYNTHETIC data (see")
        print("    literature/literature_review.md section 5) -- they validate")
        print("    the pipeline, not the science. Re-run against real XBeach")
        print("    output before citing any rate from this CSV. ***")


if __name__ == "__main__":
    main()
