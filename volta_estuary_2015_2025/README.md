# Volta Estuary erosion/accretion simulation, 2015–2025

Single-file Python deliverable: `simulate_volta_estuary_2015_2025.py`. Run it
with no arguments to reproduce everything in `results/` and `figures/`:

```bash
pip install numpy scipy pandas matplotlib
python3 simulate_volta_estuary_2015_2025.py
```

Add `--write-xbeach-deck` to also generate a real, runnable XBeach 1D
surfbeat input deck per transect under `xbeach_deck/` (params.txt + grid +
JONSWAP wave + tide files) — useful once you have an actual XBeach install.

## What this covers

Seven cross-shore transects spanning the Volta River estuary mouth, from Ada
Foah (west bank, updrift) through the river mouth to Keta (east bank,
downdrift) — a superset of the single-site `xbeach_fuveme/` project
elsewhere in this repo, generalized to the whole estuary and extended to a
full decade (2015–2025) with per-year output.

## Read before citing any number

- **Real:** every source cited in the `LITERATURE` dict and each transect's
  `source` field at the top of the script, and the October 2023 Akosombo Dam
  spillage magnitude (11,616.1 m³ eroded / 1,016.0 m³ deposited at Fuveme —
  *Journal of Coastal Research* 2024, Special Issue 113,
  doi:10.2112/JCR-SI113-200.1). That event sits inside the requested
  2015–2025 window and is a real, documented perturbation, not an invented
  one — it shows up as a visible kink in every transect in Figure A and the
  tallest bar in Figure C.
- **Synthetic:** the bathymetry (idealized Dean profile), the wave/tide
  forcing (built from literature ranges, not a recorded series), and
  therefore the interannual wiggle in every year's number. The engine is
  calibrated so each transect's **decadal-average** rate matches its
  literature target (Figure B) — the year-to-year variation around that
  trend is illustrative, and the 2023→transect volume conversion in
  particular required an explicit assumption (a representative 1 km impact
  reach length) that's called out directly in the code comment next to it.
- XBeach itself was not run to produce these numbers (no compiler toolchain
  / real survey data available in the environment this was built in) — see
  `xbeach_fuveme/README.md` in this repo for the full explanation and for
  how to source real bathymetry/wave data for the region.

## Outputs

- `results/annual_rates_2015_2025.csv` — per-transect, per-year shoreline
  position, cumulative change, annual rate (m/yr), volume (m³/m), annual
  volume rate (m³/m/yr), and a flag for the 2023 event year.
- `results/decadal_summary.csv` — per-transect decadal-average rate vs. its
  literature target.
- `figures/figA_shoreline_timeseries_2015_2025.png` — shoreline change per
  transect, 2023 event annotated.
- `figures/figB_spatial_gradient.png` — modeled vs. literature rate across
  the estuary, west to east.
- `figures/figC_annual_volume_budget.png` — estuary-wide annual sediment
  budget, 2015–2025.
- `figures/figD_annual_rate_heatmap.png` — transect × year rate heatmap.
