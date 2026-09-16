"""
Generate publication-style figures for the Fuveme erosion/accretion study.

Run after analysis/demo_synthetic_run.py and analysis/erosion_accretion_rates.py
(or, once real XBeach output exists, after pointing RESULTS_DIR /
xbeach_io.load_run at the real runs instead). Every figure carries a small
"DEMO / SYNTHETIC DATA" watermark whenever the underlying run data is
synthetic -- see literature/literature_review.md section 5. Remove the
watermark call once real XBeach output is plotted.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

import style
from xbeach_io import load_run

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
DEMO_RUNS_DIR = RESULTS_DIR / "demo_runs"
LIT_PARAMS_PATH = ROOT / "literature" / "parameters_from_literature.yaml"

style.apply_style()


def _watermark(fig, is_synthetic: bool):
    if is_synthetic:
        fig.text(0.5, 0.5, "DEMO / SYNTHETIC DATA\npipeline test only", fontsize=26,
                  color="#c3c2b7", alpha=0.35, ha="center", va="center", rotation=30,
                  fontweight="bold", zorder=0)


def _save(fig, name: str):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / name
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def load_lit():
    with open(LIT_PARAMS_PATH) as f:
        return yaml.safe_load(f)


def fig1_site_and_bathymetry(scenario: str = "baseline"):
    runs = [load_run(p) for p in sorted((DEMO_RUNS_DIR / scenario).glob("*.npz"))]
    fig, (ax_map, ax_prof) = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1, 1.4]})

    lit = load_lit()
    lat, lon = lit["site"]["approx_coords_deg"]["lat"], lit["site"]["approx_coords_deg"]["lon"]
    offsets_km = [r["alongshore_offset_m"] / 1000 for r in runs]
    ax_map.plot([0] * len(offsets_km), offsets_km, color=style.CATEGORICAL["blue"], lw=2, zorder=1)
    ax_map.scatter([0] * len(offsets_km), offsets_km, color=style.CATEGORICAL["orange"], s=60, zorder=2,
                    label="modeled transects")
    for r, o in zip(runs, offsets_km):
        ax_map.annotate(r["transect_id"], (0, o), xytext=(6, 0), textcoords="offset points", fontsize=8,
                         color=style.INK["secondary"])
    ax_map.annotate("Volta River\nmouth (updrift)", (0, -0.3), xytext=(-0.55, -0.3), fontsize=8,
                     color=style.INK["muted"], ha="center")
    ax_map.annotate("littoral drift →", (-0.4, offsets_km[-1] / 2), fontsize=8, color=style.INK["muted"], rotation=90)
    ax_map.set_xlim(-0.8, 0.8)
    ax_map.set_ylabel("alongshore distance (km)")
    ax_map.set_xticks([])
    ax_map.set_title(f"Fuveme transect layout\n(approx. {lat}°N, {lon}°E)")
    ax_map.legend(loc="upper right", frameon=False, fontsize=8)

    mid = runs[len(runs) // 2]
    ax_prof.plot(mid["x"], mid["zb"][0, :], color=style.CATEGORICAL["blue"], label="initial bed level (t=0)")
    ax_prof.axhline(0, color=style.INK["muted"], lw=0.8, ls="--", label="MSL")
    ax_prof.fill_between(mid["x"], mid["zb"][0, :], -14, color=style.CATEGORICAL["blue"], alpha=0.08)
    ax_prof.set_xlabel("cross-shore distance from seaward boundary (m)")
    ax_prof.set_ylabel("bed level (m, MSL datum)")
    ax_prof.set_title(f"Idealized initial profile — transect {mid['transect_id']}")
    ax_prof.legend(loc="lower right", frameon=False, fontsize=8)

    fig.suptitle("Figure 1. Fuveme model domain: transect layout and initial cross-shore bathymetry", y=1.03)
    _watermark(fig, mid["is_synthetic"])
    _save(fig, "fig1_site_bathymetry.png")


def fig2_wave_climate():
    lit = load_lit()
    waves = lit["waves"]
    months = np.arange(1, 13)
    hs_lo, hs_hi = waves["Hs_annual_mean_m"]
    low_m = set(waves["seasonal_cycle"]["low_months"])
    high_m = set(waves["seasonal_cycle"]["high_months"])
    hs = np.where(np.isin(months, list(high_m)), hs_hi,
                  np.where(np.isin(months, list(low_m)), hs_lo, 0.5 * (hs_lo + hs_hi)))

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bar_colors = [style.CATEGORICAL["red"] if m in high_m else style.CATEGORICAL["blue"] if m in low_m
                  else style.CATEGORICAL["aqua"] for m in months]
    ax.bar(months, hs, color=bar_colors, width=0.65)
    ax.set_xticks(months)
    ax.set_xlabel("month")
    ax.set_ylabel("significant wave height, Hs (m)")
    ax.set_title("Figure 2. Offshore wave climate used to force the model\n(Gulf of Guinea reanalysis 1979–2005)")
    from matplotlib.patches import Patch
    handles = [Patch(color=style.CATEGORICAL["blue"], label="calm season (Jan–Feb)"),
               Patch(color=style.CATEGORICAL["red"], label="high-wave season (Jul–Aug)"),
               Patch(color=style.CATEGORICAL["aqua"], label="transitional")]
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="upper left")
    ax.text(0.98, 0.02, "source: doi:10.3390/jmse10111581", transform=ax.transAxes, ha="right",
            fontsize=7, color=style.INK["muted"])
    _save(fig, "fig2_wave_climate.png")


def fig3_profile_evolution(scenarios=("baseline", "mangrove_nbs_intertidal"), transect="T03"):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for i, scen in enumerate(scenarios):
        run = load_run(DEMO_RUNS_DIR / scen / f"{transect}.npz")
        color = style.categorical(i)
        ax.plot(run["x"], run["zb"][0, :], color=style.INK["muted"], lw=1.2, ls="--",
                label="initial (t=0)" if i == 0 else None)
        ax.plot(run["x"], run["zb"][-1, :], color=color, lw=2,
                label=f"{scen.replace('_', ' ')} — after 1 yr")
    ax.axhline(0, color=style.INK["muted"], lw=0.7, ls=":")
    ax.set_xlim(run["x"].max() - 300, run["x"].max())
    ax.set_xlabel("cross-shore distance from seaward boundary (m)")
    ax.set_ylabel("bed level (m, MSL datum)")
    ax.set_title(f"Figure 3. Simulated beach-face profile evolution — transect {transect}\n"
                 "baseline erosion vs. mangrove nature-based-solution scenario")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _watermark(fig, run["is_synthetic"])
    _save(fig, "fig3_profile_evolution.png")


def fig4_shoreline_timeseries(scenario: str = "baseline"):
    paths = sorted((DEMO_RUNS_DIR / scenario).glob("*.npz"))
    fig, axes = plt.subplots(1, len(paths), figsize=(3.0 * len(paths), 3.6), sharey=True)
    from erosion_accretion_rates import shoreline_position
    for i, (p, ax) in enumerate(zip(paths, axes)):
        run = load_run(p)
        t_years = run["time_days"] / 365.0
        pos = np.array([shoreline_position(run["x"], run["zb"][k, :]) for k in range(run["zb"].shape[0])])
        pos0 = pos - pos[0]
        ax.plot(t_years, -pos0, color=style.CATEGORICAL["blue"], lw=1.4)
        slope = np.polyfit(t_years, -pos0, 1)[0]
        ax.axhline(0, color=style.INK["grid"], lw=0.8)
        ax.set_title(f"{run['transect_id']}\n{slope:+.1f} m/yr", fontsize=9)
        ax.set_xlabel("year")
        if i == 0:
            ax.set_ylabel("shoreline change (m)\n(– = retreat)")
    fig.suptitle(f"Figure 4. Modeled shoreline position change per transect — scenario: {scenario}", y=1.05)
    _watermark(fig, run["is_synthetic"])
    _save(fig, "fig4_shoreline_timeseries.png")


def fig5_volume_budget(scenario: str = "baseline"):
    df = pd.read_csv(RESULTS_DIR / "annual_rates_per_transect.csv")
    df = df[df["scenario"] == scenario].sort_values("alongshore_offset_m")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = [style.erosion_accretion_color(v) for v in df["volume_rate_m3_per_m_per_yr"]]
    ax.bar(df["transect_id"], df["volume_rate_m3_per_m_per_yr"], color=colors)
    ax.axhline(0, color=style.INK["primary"], lw=0.8)
    ax.set_ylabel("sediment volume change rate\n(m³ per running metre per year)")
    ax.set_title(f"Figure 5. Cross-shore sediment budget by transect — scenario: {scenario}")
    from matplotlib.patches import Patch
    handles = [Patch(color=style.DIVERGING_BLUE_RED["accretion"], label="accretion"),
               Patch(color=style.DIVERGING_BLUE_RED["erosion"], label="erosion")]
    ax.legend(handles=handles, frameon=False, fontsize=8)
    is_synth = bool(pd.read_csv(RESULTS_DIR / "annual_rates_per_transect.csv")["is_synthetic"].iloc[0])
    _watermark(fig, is_synth)
    _save(fig, "fig5_volume_budget.png")


def fig6_literature_comparison(scenario: str = "baseline"):
    lit = load_lit()["shoreline_change_rates_m_per_yr"]
    df = pd.read_csv(RESULTS_DIR / "annual_rates_per_transect.csv")
    df = df[df["scenario"] == scenario]
    this_study_rate = df["shoreline_rate_m_per_yr"].mean()

    bars = {
        "This study\n(Fuveme, modeled)": this_study_rate,
        "Fuveme UAV\n(Jayson-Quashigah '19)*": None,  # volumetric, not a rate; shown as annotation instead
        "Fuveme DSAS\nEPR (extreme, 2025)": lit["fuveme_dsas_2025"]["erosion_EPR"],
        "Ada Foah\naverage (Addo 2012)": lit["ada_foah"]["average_rate"],
        "Keta\naverage erosion": -abs(lit["keta"]["average_erosion"]),
        "Keta, post-seawall\n(reversal)": lit["keta"]["post_seawall"],
        "Volta estuary\neast bank": lit["volta_estuary_banks"]["east_bank"],
    }
    labels = [k for k, v in bars.items() if v is not None]
    values = [v for v in bars.values() if v is not None]

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    colors = [style.erosion_accretion_color(v) for v in values]
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color=style.INK["primary"], lw=0.8)
    ax.set_yscale("symlog", linthresh=2)
    ax.set_ylabel("shoreline change rate (m/yr, symlog scale)\n(– = erosion, + = accretion)")
    for label, v in zip(labels, values):
        ax.annotate(f"{v:+.1f}", (label, v), textcoords="offset points",
                    xytext=(0, 6 if v >= 0 else -14), ha="center", fontsize=7.5, color=style.INK["secondary"])
    ax.set_title(f"Figure 6. Modeled Fuveme shoreline rate vs. published Volta Delta rates\n(scenario: {scenario})")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
    ax.text(0.01, -0.30, "*Fuveme UAV study reports net volume change (+12,700 m³, Apr'17–Apr'18), not a shoreline rate — not directly comparable, shown in text only.",
            transform=ax.transAxes, fontsize=7, color=style.INK["muted"])
    _watermark(fig, bool(df["is_synthetic"].iloc[0]))
    _save(fig, "fig6_literature_comparison.png")


def fig7_scenario_comparison():
    df = pd.read_csv(RESULTS_DIR / "annual_rates_reach_summary.csv")
    order = ["baseline", "slr_2050_rcp45", "slr_2100_rcp85_subsidence", "mangrove_nbs_berm", "mangrove_nbs_intertidal"]
    df = df.set_index("scenario").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    colors = [style.erosion_accretion_color(v) for v in df["mean_shoreline_rate_m_per_yr"]]
    ax.bar(df["scenario"].str.replace("_", " "), df["mean_shoreline_rate_m_per_yr"], color=colors)
    ax.axhline(0, color=style.INK["primary"], lw=0.8)
    ax.set_ylabel("mean modeled shoreline change rate (m/yr)")
    ax.set_title("Figure 7. Scenario comparison: sea-level-rise vs. mangrove\nnature-based-solution scenarios at Fuveme")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right", fontsize=8)
    per_transect = pd.read_csv(RESULTS_DIR / "annual_rates_per_transect.csv")
    _watermark(fig, bool(per_transect["is_synthetic"].iloc[0]))
    _save(fig, "fig7_scenario_comparison.png")


def main():
    fig1_site_and_bathymetry()
    fig2_wave_climate()
    fig3_profile_evolution()
    fig4_shoreline_timeseries()
    fig5_volume_budget()
    fig6_literature_comparison()
    fig7_scenario_comparison()


if __name__ == "__main__":
    main()
