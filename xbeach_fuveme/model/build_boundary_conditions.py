"""
Build XBeach wave and water-level boundary condition files for the Fuveme
setup, from the literature-derived wave/tide/SLR ranges in
literature/parameters_from_literature.yaml.

Produces, per scenario:
  - jonswap.txt     : one JONSWAP spectrum block per forcing interval (bcfile
                       for instat=jons_table / jons)
  - waves_timeseries.csv : the Hs/Tp/dir/duration sequence in human-readable form
  - tide.txt        : zs0 water level time series (M2 semi-diurnal tide + SLR
                       offset + storm surge perturbation)

Scientific basis:
  - Hs, Tm ranges and seasonal cycle: Gulf of Guinea wave reanalysis
    (doi:10.3390/jmse10111581)
  - Tidal range ~1 m, semi-diurnal: regional Volta Delta reviews
  - SLR scenarios: Appeaning Addo et al. subsidence/SLR study

This produces a REPRESENTATIVE annual forcing sequence (not a real recorded
time series) used together with a morphological acceleration factor (morfac,
set in params.txt) to simulate a year of morphological change from a
compressed sequence of representative sea states -- a standard technique in
process-based coastal modeling when a full high-resolution multi-year wave
record isn't available.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

LIT_PARAMS_PATH = Path(__file__).resolve().parent.parent / "literature" / "parameters_from_literature.yaml"

M2_PERIOD_HOURS = 12.42


def build_seasonal_wave_sequence(lit: dict, n_per_month: int = 4, seed: int = 7) -> pd.DataFrame:
    waves = lit["waves"]
    hs_lo, hs_hi = waves["Hs_annual_mean_m"]
    tm_lo, tm_hi = waves["Tm_mean_period_s"]
    low_months = set(waves["seasonal_cycle"]["low_months"])
    high_months = set(waves["seasonal_cycle"]["high_months"])
    dir_lo, dir_hi = waves["dominant_direction_deg_from"]

    rng = np.random.default_rng(seed)
    rows = []
    hours_per_block = 24 * 30 / n_per_month  # split each month into n_per_month blocks
    t_hours = 0.0
    for month in range(1, 13):
        if month in high_months:
            hs_mean = hs_hi
        elif month in low_months:
            hs_mean = hs_lo
        else:
            hs_mean = 0.5 * (hs_lo + hs_hi)
        for _ in range(n_per_month):
            hs = max(0.3, rng.normal(hs_mean, 0.15))
            tm = float(np.clip(rng.normal(0.5 * (tm_lo + tm_hi), 0.4), tm_lo - 0.5, tm_hi + 0.5))
            wave_dir = float(rng.uniform(dir_lo, dir_hi))
            duration_h = hours_per_block
            rows.append(dict(month=month, t_start_h=t_hours, duration_h=duration_h,
                              Hs_m=round(hs, 2), Tp_s=round(tm / 0.9, 1),  # Tp ~ Tm/0.9 (JONSWAP)
                              dir_deg=round(wave_dir, 1)))
            t_hours += duration_h
    return pd.DataFrame(rows)


def write_jonswap_bc(df: pd.DataFrame, outdir: Path, gamma: float = 3.3, directional_spread_deg: float = 20.0) -> None:
    """Write XBeach non-stationary spectral boundary condition files:
    a filelist.txt referencing one jonswap.txt-per-interval, per XBeach
    instat = jons_table convention (simplified single-file table form)."""
    outdir.mkdir(parents=True, exist_ok=True)
    lines = [f"{len(df)}"]
    for _, r in df.iterrows():
        # filelist.txt row format for instat=jons_table:
        # duration(s) rampup fname
        fname = f"jonswap_{int(r.t_start_h):05d}.txt"
        lines.append(f"{r.duration_h*3600:.0f} 0 {fname}")
        with open(outdir / fname, "w") as f:
            f.write(f"Hm0 = {r.Hs_m}\n")
            f.write(f"Tp = {r.Tp_s}\n")
            f.write(f"mainang = {r.dir_deg}\n")
            f.write(f"gammajsp = {gamma}\n")
            f.write(f"s = {90.0/directional_spread_deg:.1f}\n")
            f.write("fnyq = 0.3\n")
    with open(outdir / "filelist.txt", "w") as f:
        f.write("FILELIST\n")
        f.write("\n".join(lines[1:]) + "\n")
    df.to_csv(outdir / "waves_timeseries.csv", index=False)


def build_tide_series(lit: dict, total_hours: float, slr_m: float = 0.0, surge_events: int = 2, seed: int = 3) -> pd.DataFrame:
    tide_range = lit["tide"]["range_m"]
    amp = tide_range / 2.0
    dt_h = 0.25
    t = np.arange(0, total_hours + dt_h, dt_h)
    omega = 2 * np.pi / M2_PERIOD_HOURS
    zs = amp * np.sin(omega * t) + slr_m

    rng = np.random.default_rng(seed)
    for _ in range(surge_events):
        center = rng.uniform(0, total_hours)
        surge_amp = rng.uniform(0.2, 0.5)
        width_h = rng.uniform(12, 36)
        zs += surge_amp * np.exp(-0.5 * ((t - center) / (width_h / 2.355)) ** 2)

    return pd.DataFrame({"t_s": t * 3600.0, "zs0_m": np.round(zs, 3)})


def write_tide_file(df: pd.DataFrame, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    np.savetxt(outdir / "tide.txt", df[["t_s", "zs0_m"]].values, fmt="%.2f")
    df.to_csv(outdir / "tide_timeseries.csv", index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent / "boundary_conditions" / "generated")
    ap.add_argument("--slr-m", type=float, default=0.0, help="add this SLR offset to the tide/water level series")
    ap.add_argument("--scenario-name", default="baseline")
    args = ap.parse_args()

    with open(LIT_PARAMS_PATH) as f:
        lit = yaml.safe_load(f)

    wave_df = build_seasonal_wave_sequence(lit)
    outdir = args.outdir / args.scenario_name
    write_jonswap_bc(wave_df, outdir)

    total_hours = wave_df["t_start_h"].iloc[-1] + wave_df["duration_h"].iloc[-1]
    tide_df = build_tide_series(lit, total_hours=total_hours, slr_m=args.slr_m)
    write_tide_file(tide_df, outdir)

    print(f"scenario '{args.scenario_name}': {len(wave_df)} wave intervals over {total_hours/24:.1f} days "
          f"(compressed representative year), SLR offset={args.slr_m} m -> {outdir}")


if __name__ == "__main__":
    main()
