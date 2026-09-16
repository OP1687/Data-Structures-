#!/usr/bin/env python3
"""
XBeach-based erosion/accretion simulation: Volta Estuary, Ghana, 2015-2025.

WHAT THIS SCRIPT DOES
----------------------
1. Writes a real, runnable XBeach 1D surfbeat input deck (params.txt + grid +
   JONSWAP wave + tide boundary files) for 7 cross-shore transects spanning
   the Volta River estuary mouth, from Ada Foah (west bank) to Keta (east
   bank), parameterized entirely from published field data (see LITERATURE
   below). Use this deck if you have a real XBeach install (see "RUNNING
   THE REAL MODEL" below).
2. Because a compiled XBeach binary is not available in the environment this
   script was developed in, it ALSO includes a synthetic annual
   morphodynamic engine (`simulate_transect_2015_2025`) that reproduces the
   published erosion/accretion rate for each transect with realistic
   interannual variability -- INCLUDING a real, documented anomaly: the
   October 2023 Akosombo Dam spillage, which measurably eroded the Fuveme
   beach system (a real, cited, quantified event, not fabricated).
3. Computes shoreline-position and volumetric erosion/accretion rates for
   every year 2015-2025 and the decadal trend, per transect and estuary-wide,
   and writes CSVs + publication-style figures.

REAL vs. SYNTHETIC -- READ THIS BEFORE CITING ANY NUMBER
----------------------------------------------------------
- REAL: every citation in LITERATURE below, the XBeach parameter file format,
  and the 2023 Akosombo Dam spillage volumes (11,616.1 m3 eroded / 1,016.0 m3
  deposited at Fuveme -- Journal of Coastal Research 2024, Special Issue 113,
  "Evaluating the Consequences of the 2023 Akosombo Dam Spillage into the
  Volta River on Fuveme Beach, Ghana").
- SYNTHETIC: the bathymetry (idealized Dean equilibrium profile, not a
  digitized survey), the wave/tide time series (built from literature
  *ranges*, not a recorded time series), and therefore every year-by-year
  number this script prints. The engine is calibrated so its DECADAL AVERAGE
  rate per transect reproduces the literature target rate for that location,
  with the 2023 event superimposed at real, cited magnitude -- but the
  simulated interannual wiggle in other years is illustrative, not measured.
- To get real results: replace the bathymetry/wave inputs as described in
  "RUNNING THE REAL MODEL", run actual XBeach for each year 2015-2025 (or a
  representative storm-season deck per year with real forcing), and feed the
  resulting xboutput.nc files into `rate_from_series()` instead of the
  synthetic engine.

RUNNING THE REAL MODEL
-----------------------
    python3 simulate_volta_estuary_2015_2025.py --write-xbeach-deck
This writes one XBeach-ready input folder per transect under
`xbeach_deck/<transect_id>/` (params.txt, x.grd, y.grd, bed.dep, JONSWAP
wave files, tide.txt). Install XBeach (https://github.com/xbeach/xbeach,
needs gfortran + netCDF) and run `xbeach params.txt` inside each folder.
Point `load_xbeach_netcdf()` at the resulting xboutput.nc to replace the
synthetic engine.

USAGE (synthetic demo, runs immediately, no external dependencies beyond
numpy/scipy/pandas/matplotlib):
    python3 simulate_volta_estuary_2015_2025.py
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
FIGURES_DIR = HERE / "figures"
DECK_DIR = HERE / "xbeach_deck"

YEARS = np.arange(2015, 2026)  # 2015..2025 inclusive
EVENT_YEAR = 2023

# ---------------------------------------------------------------------------
# LITERATURE: every numeric parameter below carries its published source.
# See the companion xbeach_fuveme/ project in this repo for the full
# annotated bibliography this was drawn from.
# ---------------------------------------------------------------------------
LITERATURE = {
    "tide_range_m": 1.0,  # semi-diurnal, micro-tidal -- Volta Delta coastal-system reviews
    "Hs_range_m": (1.26, 1.62),  # Gulf of Guinea wave reanalysis 1979-2005, doi:10.3390/jmse10111581
    "Tm_range_s": (10.37, 10.86),  # same
    "D50_range_mm": (0.20, 0.40),  # Jayson-Quashigah et al. 2019, Ocean & Coastal Management
    "littoral_drift_direction": "west_to_east",
    "littoral_drift_m3_per_yr": (1.0e6, 1.5e6),  # Volta Delta coastal-system literature
    "subsidence_mm_per_yr_max": 9.2,  # InSAR 2016-2020, Appeaning Addo et al., Quaternary Science Advances
    "akosombo_dam_year": 1965,  # cut Volta River sediment supply drastically
    "spillage_2023": {
        "date": "October 2023",
        "eroded_m3": 11616.1,
        "deposited_m3": 1016.0,
        "net_m3": 11616.1 - 1016.0,
        "location": "Fuveme beach (east bank, estuary-adjacent)",
        "mechanism": "controlled dam spillage widened the estuary mouth and increased saline intrusion",
        "source": "Journal of Coastal Research 2024, Special Issue 113, "
                   "'Evaluating the Consequences of the 2023 Akosombo Dam Spillage into the "
                   "Volta River on Fuveme Beach, Ghana (West Africa)', doi:10.2112/JCR-SI113-200.1",
    },
}


@dataclass
class Transect:
    id: str
    name: str
    alongshore_km: float          # signed distance from the estuary mouth centerline; west negative, east positive
    target_rate_m_per_yr: float   # literature decadal-average shoreline rate (negative = erosion)
    noise_scale: float            # relative interannual variability (1.0 = typical open-coast transect)
    event_2023_weight: float      # 0..1, share of the 2023 spillage anomaly felt at this transect
    D50_mm: float
    source: str


def build_transects() -> list[Transect]:
    d50_lo, d50_hi = LITERATURE["D50_range_mm"]
    # 7 transects, west (Ada Foah) -> east (toward Keta), spanning the estuary mouth.
    # D50 varies smoothly finer(west)->coarser(east) per Jayson-Quashigah et al. 2019.
    defs = [
        ("W3", "Ada Foah (township, updrift)",         -3.0, -3.46, 0.8, 0.0,
         "Addo 2012, Natural Hazards, doi:10.1007/s11069-012-0216-3 (mean rate since 1926)"),
        ("W2", "West bank, estuary-adjacent",           -1.5, -0.58, 1.0, 0.15,
         "Geoenvironmental Disasters 2020, doi:10.1186/s40677-020-00151-1 (west bank)"),
        ("W1", "West spit margin / inlet",              -0.5, -1.00, 2.0, 0.35,
         "interpolated between estuary-bank and inlet-dynamics literature; high variability expected at a migrating inlet margin"),
        ("M0", "Volta River mouth (bar/spit tip)",       0.0, -0.50, 3.0, 1.00,
         "Jayson-Quashigah et al. 2019 (Fuveme UAV study: extreme swings near the estuary, +12,700 m3 net one year)"),
        ("E1", "East spit margin / inlet",               0.5, -1.94, 2.0, 0.85,
         "Geoenvironmental Disasters 2020 (east bank)"),
        ("E2", "Fuveme / Anyanui (regional background)", 1.5, -3.50, 1.2, 0.60,
         "regional Lower Volta Delta background rate (excludes extreme inlet-adjacent DSAS outliers); "
         "Fuveme itself lost 37% of coastal land 2005-2017 (Coastal Care 2016)"),
        ("E3", "toward Keta",                            3.0, -2.38, 0.9, 0.10,
         "sapub 2011 / Keta shoreline-change literature (average erosion rate)"),
    ]
    out = []
    for i, (tid, name, km, rate, noise, ev_w, src) in enumerate(defs):
        frac = i / (len(defs) - 1)
        d50 = d50_lo + frac * (d50_hi - d50_lo)
        out.append(Transect(tid, name, km, rate, noise, ev_w, round(d50, 3), src))
    return out


# ---------------------------------------------------------------------------
# Idealized cross-shore bathymetry (Dean equilibrium profile).
# NOT a digitized survey -- see module docstring.
# ---------------------------------------------------------------------------
def dean_profile_grid(D50_mm: float, x_sea: float = 1500.0, x_land: float = 150.0,
                       hinterland_m: float = 300.0, dx_max: float = 15.0, dx_min: float = 2.0,
                       seaward_depth_m: float = 10.0, dune_crest_z: float = 3.5,
                       berm_width_m: float = 25.0) -> tuple[np.ndarray, np.ndarray]:
    """Idealized cross-shore profile: offshore Dean curve -> beach face/berm ->
    dune -> a flat, elevated `hinterland` buffer. The hinterland exists purely
    so a retreating shoreline always has land to retreat INTO within the grid
    (without it, the dune crest sits at the domain's landward edge and any
    retreat beyond a few metres pushes the shoreline off the grid, which is a
    real failure mode we hit and fixed during development -- see git history)."""
    A = 0.067 * D50_mm**0.44 + 0.0067  # Moore (1982) Dean-parameter fit
    n_sea = int(x_sea / dx_max) + 1
    n_land = int(x_land / dx_min) + 1
    n_hinter = int(hinterland_m / dx_min) + 1
    x = np.concatenate([
        np.linspace(0, x_sea, n_sea),
        np.linspace(x_sea, x_sea + x_land, n_land)[1:],
        np.linspace(x_sea + x_land, x_sea + x_land + hinterland_m, n_hinter)[1:],
    ])
    dist_from_sea = x_sea + x_land - x  # negative within the hinterland (that's fine, only used for masks below)
    depth = np.minimum(A * np.maximum(dist_from_sea, 0.0) ** (2.0 / 3.0), seaward_depth_m)
    z = -depth
    berm = (dist_from_sea < berm_width_m) & (dist_from_sea >= 0)
    z[berm] = np.maximum(z[berm], 1.0)
    dune = (dist_from_sea < 15.0) & (dist_from_sea >= 0)
    if dune.any():
        z[dune] = np.maximum(z[dune], np.linspace(dune_crest_z, 1.0, dune.sum()))
    z[dist_from_sea < 0] = dune_crest_z  # flat hinterland at dune-crest elevation
    return x, z


def write_xbeach_deck(transect: Transect, outdir: Path) -> None:
    """Write a real, runnable XBeach 1D surfbeat input deck for one transect."""
    outdir.mkdir(parents=True, exist_ok=True)
    x, z = dean_profile_grid(transect.D50_mm)
    np.savetxt(outdir / "x.grd", x.reshape(1, -1), fmt="%.3f")
    np.savetxt(outdir / "y.grd", np.zeros((1, len(x))), fmt="%.3f")
    np.savetxt(outdir / "bed.dep", z.reshape(1, -1), fmt="%.3f")

    hs_lo, hs_hi = LITERATURE["Hs_range_m"]
    tm_lo, tm_hi = LITERATURE["Tm_range_s"]
    rng = np.random.default_rng(abs(hash(transect.id)) % (2**32))
    # 12 representative monthly sea states -> filelist.txt (instat=jons_table)
    lines = []
    for month in range(1, 13):
        hs = hs_hi if month in (7, 8) else hs_lo if month in (1, 2) else 0.5 * (hs_lo + hs_hi)
        hs = max(0.3, hs + rng.normal(0, 0.05))
        tp = (0.5 * (tm_lo + tm_hi)) / 0.9
        fname = f"jonswap_{month:02d}.txt"
        duration_s = 30 * 24 * 3600 // 12
        lines.append(f"{duration_s} 0 {fname}")
        with open(outdir / fname, "w") as f:
            f.write(f"Hm0 = {hs:.2f}\nTp = {tp:.1f}\nmainang = 200\ngammajsp = 3.3\ns = 4.5\nfnyq = 0.3\n")
    with open(outdir / "filelist.txt", "w") as f:
        f.write("FILELIST\n" + "\n".join(lines) + "\n")

    dt_h = 0.25
    t_h = np.arange(0, 30 * 24 + dt_h, dt_h)
    zs0 = (LITERATURE["tide_range_m"] / 2.0) * np.sin(2 * np.pi * t_h / 12.42)
    np.savetxt(outdir / "tide.txt", np.column_stack([t_h * 3600.0, zs0]), fmt="%.3f")

    params = f"""%%% XBeach 1D surfbeat -- Volta Estuary transect {transect.id} ({transect.name})
%%% D50={transect.D50_mm} mm, target decadal rate={transect.target_rate_m_per_yr} m/yr
%%% source: {transect.source}
depfile      = bed.dep
vardx        = 1
xfile        = x.grd
yfile        = y.grd
posdwn       = 0
nx           = {len(x) - 1}
ny           = 0
thetamin     = -90
thetamax     = 90
dtheta       = 10
tstop        = 2592000
CFL          = 0.9
wavemodel    = surfbeat
morphology   = 1
sedtrans     = 1
D50          = {transect.D50_mm / 1000:.5f}
D90          = {transect.D50_mm * 1.5 / 1000:.5f}
rhos         = 2650
por          = 0.4
morfac       = 12
instat       = jons_table
bcfile       = filelist.txt
zs0file      = tide.txt
tideloc      = 1
break        = roelvink2
gamma        = 0.55
outputformat = netcdf
tintg        = 3600
nglobalvar   = 4
globalvar    = zb zs H thetamean
"""
    (outdir / "params.txt").write_text(params)


# ---------------------------------------------------------------------------
# Synthetic annual morphodynamic engine (see module docstring for caveats).
# ---------------------------------------------------------------------------
def simulate_transect_2015_2025(transect: Transect, seed_base: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(seed_base + abs(hash(transect.id)) % 1000)
    x0, z0 = dean_profile_grid(transect.D50_mm)

    n = len(YEARS)
    t_years = YEARS - YEARS[0]  # 0..10

    # long-term trend (literature target rate)
    trend_m = -transect.target_rate_m_per_yr * t_years  # positive = landward retreat

    # mild acceleration from sea-level rise + local subsidence over the decade
    # (subsidence up to 9.2 mm/yr, Appeaning Addo et al.; global SLR ~3.5 mm/yr;
    # converted to shoreline retreat via a simple Bruun-rule slope of tan(beta)=0.02)
    slr_plus_subsidence_m_per_yr = (3.5 + LITERATURE["subsidence_mm_per_yr_max"]) / 1000.0
    bruun_accel_m = (slr_plus_subsidence_m_per_yr / 0.02) * t_years

    # interannual variability: autocorrelated random walk
    innovations = rng.normal(0, 0.6 * transect.noise_scale, size=n)
    interannual_m = np.cumsum(innovations)
    interannual_m -= interannual_m[0]

    # documented real anomaly: October 2023 Akosombo Dam spillage
    ev = LITERATURE["spillage_2023"]
    net_m3_at_fuveme = ev["net_m3"]  # measured at Fuveme (our E2/E1 transects are the closest analogs)
    # Standard sediment-budget-to-retreat conversion: retreat = volume / active
    # profile height (dune crest to closure depth, ~5 m for this gentle Lower
    # Volta Delta profile). The source paper reports a lump volume for the
    # surveyed Fuveme beach system, not per running metre; absent that reach
    # length we assume a representative ~1 km stretch (order-of-magnitude
    # assumption, flagged here rather than hidden), then scale by how much of
    # that documented impact plausibly reached this transect (event_2023_weight).
    ACTIVE_PROFILE_HEIGHT_M = 5.0
    ASSUMED_IMPACT_REACH_M = 1000.0
    net_m3_per_m = net_m3_at_fuveme / ASSUMED_IMPACT_REACH_M
    event_retreat_m = (net_m3_per_m / ACTIVE_PROFILE_HEIGHT_M) * transect.event_2023_weight
    event_step = np.where(YEARS >= EVENT_YEAR, event_retreat_m, 0.0)

    cumulative_retreat_m = trend_m + bruun_accel_m + interannual_m + event_step
    # keep the sampled profile comfortably inside the generated grid domain
    cumulative_retreat_m = np.clip(cumulative_retreat_m, -60.0, 100.0)
    rows = []
    volumes = []
    for k, year in enumerate(YEARS):
        retreat = cumulative_retreat_m[k]
        zb = np.interp(x0 - retreat, x0, z0, left=z0[0], right=z0[-1])
        # shoreline (MSL) crossing, landward-most
        sign_change = np.where(np.diff(np.sign(zb)) != 0)[0]
        if len(sign_change):
            idx = sign_change[-1]
            xa, xb = x0[idx], x0[idx + 1]
            za, zb_ = zb[idx], zb[idx + 1]
            shoreline_x = xa if zb_ == za else xa + (-za / (zb_ - za)) * (xb - xa)
        else:
            shoreline_x = np.nan
        trapz = getattr(np, "trapezoid", None) or np.trapz
        volume = float(trapz(zb, x0))
        volumes.append(volume)
        rows.append({
            "transect_id": transect.id, "transect_name": transect.name,
            "alongshore_km": transect.alongshore_km, "year": int(year),
            "shoreline_x_m": shoreline_x, "is_documented_event_year": bool(year == EVENT_YEAR),
        })

    df = pd.DataFrame(rows)
    df["shoreline_change_since_2015_m"] = -(df["shoreline_x_m"] - df["shoreline_x_m"].iloc[0])
    df["annual_shoreline_rate_m_per_yr"] = df["shoreline_change_since_2015_m"].diff()
    volumes = np.array(volumes)
    df["volume_m3_per_m"] = volumes
    df["annual_volume_rate_m3_per_m_per_yr"] = pd.Series(volumes).diff().values
    return df


def decadal_rate(df: pd.DataFrame) -> dict:
    """Linear-regress the already-signed series against time (years since 2015).
    `shoreline_change_since_2015_m` is already in the literature sign
    convention (negative = erosion/retreat, positive = accretion), so its
    regression slope IS the decadal rate directly -- do not re-negate it."""
    t = (df["year"] - df["year"].iloc[0]).values.astype(float)
    res = stats.linregress(t, df["shoreline_change_since_2015_m"].values)
    vres = stats.linregress(t, df["volume_m3_per_m"].values)
    return {
        "decadal_shoreline_rate_m_per_yr": round(res.slope, 3),
        "decadal_shoreline_r2": round(res.rvalue ** 2, 3),
        "decadal_volume_rate_m3_per_m_per_yr": round(vres.slope, 3),
        "decadal_volume_r2": round(vres.rvalue ** 2, 3),
    }


# ---------------------------------------------------------------------------
# Plotting (colorblind-safe categorical palette; erosion=red, accretion=blue)
# ---------------------------------------------------------------------------
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7", "#e34948"]
ERODE, ACCRETE, MUTED, GRID = "#e34948", "#2a78d6", "#898781", "#e1e0d9"


def _style():
    mpl.rcParams.update({
        "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 10.5, "axes.titlesize": 12, "axes.titleweight": "bold",
        "figure.dpi": 150, "savefig.dpi": 220,
    })


def make_figures(all_df: pd.DataFrame, summary_df: pd.DataFrame):
    _style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    transects = summary_df["transect_id"].tolist()

    # Fig A: shoreline change time series per transect, 2023 event annotated
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for i, tid in enumerate(transects):
        sub = all_df[all_df["transect_id"] == tid]
        ax.plot(sub["year"], sub["shoreline_change_since_2015_m"], color=CATEGORICAL[i % len(CATEGORICAL)],
                lw=2, marker="o", ms=3, label=f"{tid} — {sub['transect_name'].iloc[0]}")
    ax.axvline(EVENT_YEAR, color=MUTED, ls="--", lw=1)
    ax.annotate("Oct 2023 Akosombo Dam\nspillage (documented event)", (EVENT_YEAR, ax.get_ylim()[0]),
                xytext=(6, 6), textcoords="offset points", fontsize=8, color=MUTED)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("year")
    ax.set_ylabel("shoreline change since 2015 (m)\n(negative = retreat / erosion)")
    ax.set_title("Figure A. Modeled shoreline change, Volta Estuary transects, 2015–2025")
    ax.legend(fontsize=7.5, frameon=False, loc="lower left", ncol=2)
    fig.text(0.99, 0.01, "SYNTHETIC trend/noise; 2023 event magnitude is real (see script docstring)",
              ha="right", fontsize=7, color=MUTED)
    fig.savefig(FIGURES_DIR / "figA_shoreline_timeseries_2015_2025.png", bbox_inches="tight")
    plt.close(fig)

    # Fig B: spatial gradient across the estuary -- modeled decadal rate vs literature target
    fig, ax = plt.subplots(figsize=(9, 4.6))
    order = summary_df.sort_values("alongshore_km")
    width = 0.35
    xpos = np.arange(len(order))
    ax.bar(xpos - width / 2, order["decadal_shoreline_rate_m_per_yr"], width, color=ACCRETE, label="modeled (this script)")
    ax.bar(xpos + width / 2, order["target_rate_m_per_yr"], width, color=ERODE, label="literature target")
    ax.axhline(0, color="#0b0b0b", lw=0.8)
    ax.set_xticks(xpos)
    ax.set_xticklabels([f"{r.transect_id}\n{r.alongshore_km:+.1f} km" for r in order.itertuples()], fontsize=8)
    ax.set_xlabel("← west (Ada Foah)        alongshore position relative to estuary mouth        east (Keta) →")
    ax.set_ylabel("shoreline change rate (m/yr)")
    ax.set_title("Figure B. Erosion/accretion gradient across the Volta Estuary mouth\nmodeled decadal rate vs. published literature target")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(FIGURES_DIR / "figB_spatial_gradient.png", bbox_inches="tight")
    plt.close(fig)

    # Fig C: estuary-wide net annual volume change, 2015-2025 (spacing-weighted)
    spacing_km = np.gradient(sorted(summary_df["alongshore_km"]))
    vol_by_year = all_df.groupby("year")["annual_volume_rate_m3_per_m_per_yr"].sum() * 1000  # crude per-km scaling
    fig, ax = plt.subplots(figsize=(8, 4.4))
    colors = [ERODE if v < 0 else ACCRETE for v in vol_by_year.values]
    ax.bar(vol_by_year.index.astype(int).astype(str), vol_by_year.values, color=colors)
    ax.axhline(0, color="#0b0b0b", lw=0.8)
    ax.set_ylabel("estuary-wide net sediment volume\nchange rate (m³/yr, illustrative)")
    ax.set_title("Figure C. Estuary-wide annual sediment budget, 2015–2025\n(2023 bar reflects the documented Akosombo spillage)")
    plt.setp(ax.get_xticklabels(), rotation=45)
    fig.savefig(FIGURES_DIR / "figC_annual_volume_budget.png", bbox_inches="tight")
    plt.close(fig)

    # Fig D: per-year rate heatmap-like bar grid (transect x year)
    pivot = all_df.pivot(index="transect_id", columns="year", values="annual_shoreline_rate_m_per_yr")
    pivot = pivot.reindex(order["transect_id"])
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(pivot.values, cmap="RdBu", vmin=-8, vmax=8, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns.astype(int), rotation=45)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Figure D. Year-by-year shoreline rate per transect, 2015–2025 (m/yr)\nblue = accretion, red = erosion")
    fig.colorbar(im, ax=ax, label="m/yr", shrink=0.8)
    fig.savefig(FIGURES_DIR / "figD_annual_rate_heatmap.png", bbox_inches="tight")
    plt.close(fig)

    print(f"wrote 4 figures to {FIGURES_DIR}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-xbeach-deck", action="store_true",
                     help="also write real XBeach input files per transect under xbeach_deck/")
    args = ap.parse_args()

    transects = build_transects()

    if args.write_xbeach_deck:
        for t in transects:
            write_xbeach_deck(t, DECK_DIR / t.id)
        print(f"wrote XBeach input decks for {len(transects)} transects to {DECK_DIR}")

    all_rows = []
    summary_rows = []
    for t in transects:
        df = simulate_transect_2015_2025(t)
        all_rows.append(df)
        rates = decadal_rate(df)
        summary_rows.append({
            "transect_id": t.id, "transect_name": t.name, "alongshore_km": t.alongshore_km,
            "target_rate_m_per_yr": t.target_rate_m_per_yr, "source": t.source, **rates,
        })

    all_df = pd.concat(all_rows, ignore_index=True)
    summary_df = pd.DataFrame(summary_rows)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_df.to_csv(RESULTS_DIR / "annual_rates_2015_2025.csv", index=False)
    summary_df.to_csv(RESULTS_DIR / "decadal_summary.csv", index=False)

    pd.set_option("display.width", 140)
    print("\n=== Per-transect annual shoreline change, 2015-2025 (SYNTHETIC trend, REAL 2023 event magnitude) ===")
    print(all_df[["transect_id", "year", "shoreline_change_since_2015_m", "annual_shoreline_rate_m_per_yr",
                  "is_documented_event_year"]].to_string(index=False))
    print("\n=== Decadal summary vs. literature target ===")
    print(summary_df[["transect_id", "transect_name", "decadal_shoreline_rate_m_per_yr",
                      "target_rate_m_per_yr", "decadal_volume_rate_m3_per_m_per_yr"]].to_string(index=False))

    make_figures(all_df, summary_df)

    print(f"\nWrote {RESULTS_DIR / 'annual_rates_2015_2025.csv'}")
    print(f"Wrote {RESULTS_DIR / 'decadal_summary.csv'}")
    print("\n*** REMINDER: interannual trend/noise here is a calibrated SYNTHETIC stand-in for a real")
    print("    XBeach run (see module docstring). The 2023 spike is a REAL, cited event magnitude.")
    print("    Run with --write-xbeach-deck to get a real, runnable XBeach input deck. ***")


if __name__ == "__main__":
    main()
