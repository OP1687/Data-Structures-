# Fuveme (Volta Region, Ghana) coastal erosion/accretion modeling with XBeach

An XBeach-based process modeling project for **Fuveme**, a fishing community on
the Keta Municipality barrier spit (Volta Region, Ghana) that is losing land to
coastal erosion at some of the highest rates documented on the West African
coast. This repo provides: a literature-grounded XBeach input deck, a
Python pipeline to compute erosion/accretion rates per year from model output,
and a set of publication-style figures in the style used by the coastal
geomorphology literature for this exact coast.

## Read this first: what's real vs. what's a placeholder

This session's sandboxed environment has two hard constraints that shape what
could actually be delivered:

1. **No internet access to most academic sources.** WebSearch worked, but
   direct fetches of ResearchGate, Frontiers, Springer, Nature, ScienceDirect,
   MDPI, Zenodo, TU Delft's repository, and Deltares' own oss.deltares.nl were
   all blocked by this session's network egress policy. So the **literature
   review is real** (see `literature/literature_review.md`, built from actual
   search-result abstracts with citations) but was not verified against full
   original PDFs — do that before you cite anything from it.
2. **XBeach itself cannot be installed/run in this sandbox.** XBeach is a
   compiled Fortran model (gfortran + netCDF, optionally MPI) distributed via
   GitHub source or Deltares binaries; building/validating it here wasn't
   practical in this environment. So **the actual hydrodynamic/morphodynamic
   simulation has not been run** as part of this delivery.

To keep those two limitations from silently becoming "fake results," the repo
is split cleanly:

| Real | Placeholder / synthetic |
|---|---|
| Literature review & every cited number (`literature/`) | The bathymetry grid (idealized Dean profile, not a survey — `model/build_bathymetry.py`) |
| XBeach input file format & physical parameterization (`model/params.txt`) | The wave/tide forcing (representative seasonal cycle built from literature ranges, not a real recorded time series) |
| The rate-calculation and plotting methodology (works on any XBeach output) | The demo model **output** used to test that methodology (`analysis/demo_synthetic_run.py` — watermarked "DEMO/SYNTHETIC" on every figure it feeds) |

**Bottom line: this is a complete, working pipeline ready to produce real
results the moment (a) real bathymetry/wave data replace the placeholders and
(b) it's run through an actual XBeach installation.** See `data/README.md` for
where to get (a), and the next section for (b).

## Repository layout

```
xbeach_fuveme/
  literature/
    literature_review.md              # annotated bibliography, real citations
    parameters_from_literature.yaml   # machine-readable version, used by the scripts below
  model/
    build_bathymetry.py               # idealized Dean-profile grid generator
    build_boundary_conditions.py      # JONSWAP wave + tide boundary files
    params.txt                        # XBeach 1D surfbeat parameter file (template)
    scenarios.yaml                    # baseline / SLR / mangrove-NbS scenario matrix
    run_xbeach.sh                     # builds all scenario inputs; runs `xbeach` if it's on PATH
  analysis/
    style.py                          # shared colorblind-safe plotting palette
    xbeach_io.py                      # loader: real xboutput.nc OR demo .npz, same schema
    erosion_accretion_rates.py        # shoreline-position + volumetric rate calculator
    make_publication_plots.py         # generates the 7 figures below
    demo_synthetic_run.py             # DEMO ONLY: fabricates labeled placeholder output
  data/README.md                      # how to get real bathymetry/wave/shoreline data
  figures/                            # generated PNGs (see below)
  results/                            # generated CSVs + demo run files
```

## How to actually run this for real results

1. **Get real data** — follow `data/README.md` (Harmony Coast bathymetry,
   Fuveme UAV DEMs, ERA5/Copernicus waves, DSAS shoreline transects).
2. **Replace the placeholders**: point `model/build_bathymetry.py` at the real
   survey transects instead of the Dean-profile generator, and
   `model/build_boundary_conditions.py` at a real extracted wave/tide time
   series instead of the representative seasonal cycle.
3. **Install XBeach** on a machine that can compile it — clone
   https://github.com/xbeach/xbeach and follow its build instructions
   (requires gfortran and netCDF; MPI optional), or use a Deltares-provided
   binary/container if you have access. This sandbox could not do this step.
4. **Run it**: `bash model/run_xbeach.sh` builds every scenario's input deck
   and runs `xbeach params.txt` per scenario/transect if `xbeach` is found on
   `PATH`.
5. **Analyze real output**: point `analysis/erosion_accretion_rates.py` and
   `analysis/make_publication_plots.py` at the resulting `xboutput.nc` files
   (via `analysis/xbeach_io.load_run`, which already supports netCDF) instead
   of `results/demo_runs/`. Remove the `_watermark(...)` calls in
   `make_publication_plots.py` once the data is real.

## How to exercise the pipeline right now (synthetic demo)

```bash
pip install -r requirements.txt
cd analysis
python3 demo_synthetic_run.py         # fabricates labeled placeholder output
python3 erosion_accretion_rates.py    # -> results/annual_rates_per_transect.csv, annual_rates_reach_summary.csv
python3 make_publication_plots.py     # -> figures/fig1..fig7*.png
```

This has already been run once in this repo, so `results/` and `figures/`
are populated — regenerate any time with the three commands above.

## The erosion/accretion rate methodology

For each cross-shore transect, `erosion_accretion_rates.py` computes:

- **Shoreline change rate (m/yr)**: cross-shore position of the MSL (z=0)
  contour at every output time step, linear-regressed against time in years.
  Sign convention matches the literature: negative = erosion (retreat),
  positive = accretion (progradation).
- **Volumetric sediment budget rate (m³/m/yr)**: time derivative of the
  cross-shore-integrated bed volume within the active profile, also
  linear-regressed. Multiplying by alongshore transect spacing gives a
  reach-total annual sediment budget in m³/yr.

These are exactly the two diagnostics used in the DSAS/EPR-LRR shoreline
studies and UAV volumetric studies cited in the literature review, so modeled
output is directly comparable to the published Ada Foah / Keta / Fuveme
numbers (see Figure 6).

## Figures produced

1. **Site & bathymetry** — transect layout + initial cross-shore profile
2. **Wave climate** — seasonal Hs cycle used to force the model
3. **Profile evolution** — baseline vs. mangrove-NbS scenario, one transect
4. **Shoreline time series** — per-transect position change with trend/rate
5. **Sediment volume budget** — per-transect m³/m/yr, erosion vs. accretion
6. **Literature comparison** — modeled rate vs. published Ada Foah/Keta/Fuveme rates
7. **Scenario comparison** — baseline vs. SLR2050/2100 vs. mangrove NbS scenarios

## Key literature-derived facts driving this setup

- Fuveme lost **37% of its coastal land between 2005 and 2017**; is targeted
  by the World Bank's $150M WACA resilience program.
- The only prior XBeach study on this exact coast (Angnuureng et al. 2025,
  *Frontiers in Marine Science*) used **1D surfbeat mode with the vegetation
  module**, validated to **RMSE ≈ 0.75 m**, and found high-density intertidal
  mangroves cut modeled erosion by **up to 97%** — this repo's scenario matrix
  mirrors that study directly.
- Regional (non-inlet) background shoreline retreat is **≈ −2 to −6 m/yr**
  (Ada Foah −3.46 m/yr avg, Keta −2.38 m/yr avg); Fuveme's own DSAS-derived
  extreme values (−107.6/+28.5 m/yr) reflect an actively migrating inlet, not
  a uniform trend — see `literature/literature_review.md` §3 for the full
  reasoning and table of sources.

See `literature/literature_review.md` for full citations and
`literature/parameters_from_literature.yaml` for every numeric input used.
