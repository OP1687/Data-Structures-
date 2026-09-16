# Literature review: erosion/accretion modeling context for Fuveme, Volta Region, Ghana

This review collects the published research and datasets that ground the XBeach setup
in this repository. It was compiled from web search of open literature; full texts of
several paywalled/registration-gated sources (ResearchGate, Frontiers, Springer, Nature,
ScienceDirect, MDPI, Zenodo, TU Delft repository) could **not** be fetched directly from
this environment (outbound access to those domains is blocked by the session's network
policy), so figures below are drawn from search-result abstracts/snippets. **Before
publication, pull the primary PDFs yourself and verify every number quoted here against
the source.**

## 1. Site context

Fuveme (also spelled Fuvemeh) is a fishing community in the Keta Municipality, Volta
Region, Ghana, on the barrier spit between the Gulf of Guinea and the Keta Lagoon,
between Anyanui and Blekusu. It sits on the down-drift (eastern) side of the Volta River
mouth, on one of the most sediment-starved and fastest-eroding stretches of the West
African coast.

- **37% of Fuveme's coastal land was lost to flooding/erosion between 2005 and 2017**;
  by 2017 roughly 80 houses and a school had been destroyed and >300 people displaced
  (Coastal Care, 2016; Dialogue Earth; UNESCO Courier — news synthesis, not a primary
  measurement).
- Fuveme is targeted by the World Bank-financed **West Africa Coastal Areas Management
  Program (WACA)**, with a ~$150M resilience investment announced in 2026.
- Coastal defense structures (revetments/groynes) elsewhere on the coast interrupt
  longshore transport and have been linked to increased erosion at adjacent,
  down-drift communities including Fuveme and Anyanui.

**Approximate location** used for figure labeling in this repo: **5.85°N, 0.83°E**
(Keta Municipality barrier spit, between Anyanui and Blekusu). Treat this as
approximate — replace with a surveyed coordinate before publication.

## 2. Process-based (XBeach) modeling precedent at this exact coast

- **Angnuureng et al., "Evaluating mangroves as nature-based solutions for coastal
  protection under current and future sea level rise scenarios"**, *Frontiers in
  Marine Science* (2025), doi:10.3389/fmars.2025.1526082. This is the closest existing
  analog to the requested work:
  - Uses **XBeach 1D, surfbeat (instationary) mode**, with the vegetation module
    active, applied to the Volta Delta coast.
  - Nearshore bathymetry sourced from the **Harmony Coast project**: repeat
    Valeport MIDAS echo-sounder transects, ~500 m alongshore spacing, covering
    3–10 m water depth; **GEBCO** global bathymetry used seaward of 10 m.
  - Baseline model validated against measured profiles with **RMSE ≈ 0.75 m**
    for sediment volume change.
  - Scenarios: no mangroves / mangroves on the berm / mangroves in the intertidal
    zone, at varying stem density, under present and future sea level.
  - Result: high-density intertidal mangroves reduced modeled erosion by **up to
    97%**; berm-planted mangroves by **~53%**.
  - A companion/related paper appears in *Discover Applied Sciences*
    (Springer, 2025, doi:10.1007/s42452-025-07623-9), same "What-If" modeling
    framing.
- **Angnuureng et al., "The State of the Lower Volta Delta Beaches in Ghana from
  Field Observations"** (Research Square preprint rs-4727110/v1; also on
  ResearchGate; dataset deposited at **Zenodo record 10554597**). Reports ~90 km
  of field survey (beach profiles, bathymetry, wave observations, grain size)
  along the Lower Volta Delta over a 5-month field campaign — this is the
  companion field dataset behind the XBeach study above and the most direct
  candidate source of **real** calibration data for a Fuveme-specific model.
  *(Could not fetch the Zenodo page from this session — check it directly for
  downloadable transect/bathymetry files.)*
- **Jayson-Quashigah, Angnuureng et al., "Assessment of short-term beach sediment
  change in the Volta Delta coast in Ghana using data from Unmanned Aerial
  Vehicles (Drone)"**, *Ocean & Coastal Management* (2019, ScienceDirect
  S0964569118309578). UAV-derived DEMs at three sites: Old Ningo (west), **Fuveme
  (central)**, Keta (east), April 2017–April 2018.
  - Fuvemeh gained **~12,700 m³ net sediment volume** over that one-year window —
    illustrating that Fuveme swings between strong erosion and strong accretion
    episodes rather than eroding monotonically (attributed to its proximity to
    the Volta estuary mouth).
  - Grain size: broader Lower Volta Delta beaches are mostly **medium sand
    (0.3–0.4 mm)**, with ~43% classed as fine sand (0.20–0.29 mm); west (Old
    Ningo) side finer than east.
  - Fuveme is described as one of the **gentlest and widest** beaches on the
    Lower Volta Delta.

## 3. Shoreline change rates (remote sensing / DSAS studies)

| Source | Method / period | Location | Erosion rate | Accretion rate |
|---|---|---|---|---|
| Scientific Reports (2025), doi:10.1038/s41598-025-98260-0 | Landsat 5/7/8/9 1986–2024, DSAS EPR & LRR, CoastSat | **Fuveme** | EPR −107.6 m/yr, LRR −75.7 m/yr (localized transects near the inlet — extreme values, likely spit-breach related, not a stretch-average) | EPR +28.5 m/yr, LRR +33.6 m/yr |
| Springer Nat. Hazards (2012), doi:10.1007/s11069-012-0216-3 | 1926–present | Ada Foah, 77 km stretch | mean retreat 280.5 m since 1926 (≈3.46 m/yr average); max EPR −5.01, LRR −6.13 m/yr | max EPR +3.77, LRR +3.11 m/yr |
| sapub (2011) / follow-on studies | Medium-res satellite | Keta | avg erosion 2.38 m/yr (range 0.1–9.3) | avg accretion 2.5 m/yr (range 0.1–19, locally to ~18–19 m/yr) |
| Keta Sea Defence project literature (ASCE / World Bank case study) | Before/after 2000 seawall+groynes | Keta town | pre-project −1.6 m/yr | post-project +1.0 m/yr |
| Geoenvironmental Disasters (2020), doi:10.1186/s40677-020-00151-1 | Volta estuary mouth shorelines | East bank / West bank | East bank −1.94 m/yr | West bank −0.58 m/yr (i.e. also erosion, but slower) |

**Interpretation for modeling:** Fuveme's satellite-derived end-point rates are
extreme outliers driven by the adjacent inlet/spit dynamics (the -107.6/+28.5 m/yr
pair sitting side by side on the same short stretch is itself diagnostic of a
migrating inlet or breach, not uniform shoreline retreat). The **regional
background rate for the open, non-inlet-adjacent Lower Volta Delta beaches is on
the order of −2 to −6 m/yr net retreat**, consistent with Ada Foah (−3.46 m/yr
average) and Keta (−2.38 m/yr average) once accretion at protected/updrift
sections is excluded. This repo's default scenario is parameterized to reproduce
that regional background rate at Fuveme; the extreme DSAS values are retained
in `parameters_from_literature.yaml` for the literature-comparison figure.

## 4. Physical forcing parameters used to build the model

| Parameter | Value used | Source |
|---|---|---|
| Offshore significant wave height, Hs (annual/seasonal mean) | 1.26–1.62 m | Gulf of Guinea wave climate reanalysis (1979–2005), doi:10.3390/jmse10111581 |
| Mean wave period, Tm | 10.4–10.9 s | same |
| Seasonal cycle | lowest Jan–Feb, highest Jul–Aug (SW monsoon swell season) | same |
| Dominant offshore wave direction | S–SW swell | same; Volta Delta coastal system reports (Roest 2018, TU Delft) |
| End-of-century Hs projection | up to ~1.72 m (+0.1 to +0.4 m) | same reanalysis/projection study |
| Tidal regime | semi-diurnal, micro-tidal, range ≈ 1 m | multiple sources (Volta Delta reviews) |
| Net longshore sediment transport | 1.0–1.5 × 10⁶ m³/yr, west→east | Volta Delta coastal-system literature; among the highest unidirectional littoral drift rates recorded globally |
| Sediment supply disruption | Akosombo Dam (1965) cut Volta River sediment discharge to a small fraction of pre-dam levels | Volta Delta reviews |
| Median grain size, D50 | 0.2–0.4 mm (fine–medium sand) | Jayson-Quashigah et al. 2019 |
| Nearshore bathymetric slope / depth range | 3–10 m over ~500 m-spaced transects (Harmony Coast survey design) | Angnuureng et al. 2025 |
| Vertical land subsidence | up to −9.2 mm/yr (InSAR 2016–2020) | Appeaning Addo et al., doi:10.1016/j.qsa.2024.100175 |
| Sea level rise scenarios | RCP2.6/4.5/8.5-based local projections; >20% (up to ~45% with subsidence) of Delta districts below MSL by 2100 | same |

These values are encoded in `parameters_from_literature.yaml` and consumed by the
scripts in `model/` to build the XBeach input deck.

## 5. What is, and is not, real in this repository

- **Real:** all citations, extracted numeric parameters, and the physical
  reasoning above.
- **Synthetic/idealized:** the actual bathymetry grid and wave/tide time series
  files generated by `model/build_bathymetry.py` and
  `model/build_boundary_conditions.py`. They are an **idealized equilibrium
  (Dean) profile and a representative wave/tide climate constructed from the
  literature ranges in the table above** — not a digitized survey. XBeach
  itself is not run in this environment (see repo root `README.md` for why),
  so `analysis/demo_synthetic_run.py` also fabricates a labeled
  **DEMO/SYNTHETIC** morphodynamic output purely to exercise and validate the
  analysis and plotting pipeline end-to-end.
- **To get publication-grade results**, replace:
  1. the bathymetry grid with the real Harmony Coast/UAV-DEM survey (request
     from the University of Cape Coast / Centre for Coastal Management
     research group behind the papers above, or the Zenodo record once
     accessible), and
  2. the wave/water-level boundary conditions with a real reanalysis extraction
     (e.g., Copernicus Marine ERA5/WAVEWATCH III at the Fuveme offshore point)
     or the in-situ wave record from the same field campaign,
  then run actual XBeach (see root `README.md`) and re-run
  `analysis/erosion_accretion_rates.py` / `make_publication_plots.py` on the
  real `xboutput.nc`.

## Sources (as returned by web search; verify against primary PDFs)

- Coastal Care (2016), Dialogue Earth, UNESCO Courier — Fuveme erosion news coverage
- Ghana Business News / GBC (2026) — WACA/Fuveme government response coverage
- Angnuureng et al. (2025), *Frontiers in Marine Science*, 10.3389/fmars.2025.1526082
- (companion) *Discover Applied Sciences* (2025), 10.1007/s42452-025-07623-9
- Angnuureng et al., "The State of the Lower Volta Delta Beaches..." Research Square rs-4727110/v1; Zenodo 10554597
- Jayson-Quashigah et al. (2019), *Ocean & Coastal Management*, S0964569118309578
- *Scientific Reports* (2025), 10.1038/s41598-025-98260-0 — eastern Ghana shoreline change/DSAS
- Addo (2012), *Natural Hazards*, 10.1007/s11069-012-0216-3 — Ada Foah
- sapub (2011) Keta shoreline change; Keta Sea Defence case studies (ASCE, World Bank)
- Geoenvironmental Disasters (2020), 10.1186/s40677-020-00151-1 — Volta estuary shorelines
- Appeaning Addo et al., *Quaternary Science Advances*, 10.1016/j.qsa.2024.100175 — subsidence/SLR
- Gulf of Guinea wave climate study, 10.3390/jmse10111581
- Roest (2018), TU Delft MSc thesis, "The coastal system of the Volta delta, Ghana"
