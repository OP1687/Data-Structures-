# Getting real data for Fuveme

This repo ships literature-derived parameters and an idealized bathymetry —
enough to build a runnable XBeach input deck and to test the full analysis
pipeline, but **not** enough for publication-grade results. To get there,
obtain real data for these three inputs and feed them into the corresponding
script:

## 1. Bathymetry / beach topography → replaces `model/build_bathymetry.py` output

- **Harmony Coast project** nearshore bathymetry (Valeport MIDAS echo-sounder
  transects, ~500 m spacing, Volta Delta). Contact the University of Cape
  Coast Centre for Coastal Management / the authors of Angnuureng et al.
  (2025, *Frontiers in Marine Science*, 10.3389/fmars.2025.1526082) for access.
- **UAV-derived DEMs** at Fuveme specifically: Jayson-Quashigah et al. (2019,
  *Ocean & Coastal Management*) surveyed Fuveme with drones April 2017–April
  2018. Their dataset (or a successor field campaign) is the best available
  Fuveme-specific topography/beach-width record.
- **Zenodo record 10554597** ("The state of the lower Volta Delta Beaches in
  Ghana from field observations") may host downloadable transect data — this
  session could not reach zenodo.org to check; try it directly.
- **GEBCO** global bathymetry (https://www.gebco.net) for the offshore
  boundary beyond ~10 m depth, as used in the precedent study.

Once obtained, replace the Dean-profile generator in `build_bathymetry.py`
with a loader that interpolates the real transect onto the same non-equidistant
XBeach grid spacing.

## 2. Wave and water-level forcing → replaces `model/build_boundary_conditions.py` output

- **Copernicus Marine Service** (CMEMS) wave reanalysis/forecast products, or
  **ERA5** wind/wave reanalysis, extracted at an offshore point near Fuveme
  (~5.85°N, 0.83°E) for a real time series instead of the representative
  synthetic seasonal cycle used here.
- In-situ wave/tide records from the same field campaigns cited above, if
  available, are preferable to reanalysis for calibration.
- Tide: NOAA/GLOSS or Ghana Hydrographic/Survey Department tide gauge data if
  accessible; otherwise a global tide model (e.g., FES2014) extraction.

## 3. Shoreline change validation data

- Landsat/Sentinel-derived shorelines and DSAS transects from the *Scientific
  Reports* (2025, 10.1038/s41598-025-98260-0) study — useful to validate the
  modeled shoreline change rate against an independent remote-sensing record.
- CoastSat (https://github.com/kvos/CoastSat) can regenerate a fresh
  Landsat/Sentinel-2 shoreline time series for Fuveme directly from satellite
  imagery if the published transect data isn't shareable.

## Why this repo doesn't fetch these automatically

This session's outbound network access is restricted by organizational
egress policy: most academic domains (ResearchGate, Frontiers, Springer,
Nature, ScienceDirect, MDPI, Zenodo, TU Delft repository, Deltares' own
oss.deltares.nl) returned `403`/blocked on every fetch attempt during
development of this repo, even though web search summaries of those pages
were reachable. Re-attempt the direct downloads from an unrestricted network.
