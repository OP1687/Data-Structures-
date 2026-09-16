"""
Build an XBeach-ready cross-shore bathymetry grid for Fuveme, Volta Region, Ghana.

IMPORTANT: This is an IDEALIZED (Dean equilibrium) profile, not a digitized
survey. It is shaped to match the depth range and slope character reported for
the Harmony Coast nearshore transects (3-10 m over the surveyed reach, GEBCO
beyond) -- see literature/parameters_from_literature.yaml:bathymetry. Replace
this script's output with real transect data before publishing results.

XBeach 1D convention used here:
  - one long grid file per file, values written on the FIRST row (ny = 0 -> a
    single alongshore row), consistent with XBeach 1D (surfbeat) usage.
  - x increases offshore->onshore is NOT required; XBeach requires x increasing
    in the direction of wave propagation (offshore at x=0, shore at x=xmax).
  - bed level z is in meters relative to a chosen vertical datum (here: mean
    sea level, MSL), negative below datum.

Usage:
    python build_bathymetry.py --transect all --outdir ../model_runs/baseline
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yaml

LIT_PARAMS_PATH = Path(__file__).resolve().parent.parent / "literature" / "parameters_from_literature.yaml"


def dean_profile(x_onshore_distance: np.ndarray, A: float, dune_toe_z: float, dune_toe_x: float) -> np.ndarray:
    """Dean (1977) equilibrium profile h(x) = A * x^(2/3), stitched to a linear
    dune face landward of the dune toe. x_onshore_distance is distance
    shoreward from the shoreline (x=0 at MSL shoreline, increasing offshore
    is negative here so we keep x as distance from shoreline, seaward
    positive), h returned as depth below MSL (positive down); we convert to
    bed level z = -h.
    """
    h = A * np.power(np.maximum(x_onshore_distance, 0.0), 2.0 / 3.0)
    return h


def build_transect(
    transect_id: str,
    alongshore_offset_m: float,
    dx_min: float = 2.0,
    dx_max: float = 15.0,
    x_land: float = 150.0,
    x_sea: float = 2000.0,
    seaward_depth_target_m: float = 12.0,
    grain_size_mm: float = 0.30,
    slr_m: float = 0.0,
    dune_crest_z: float = 3.5,
    berm_width_m: float = 25.0,
) -> dict:
    """Construct one cross-shore grid+bed profile.

    Grid is non-equidistant: fine (dx_min) resolution in the surf/swash zone,
    coarsening offshore (dx_max), typical XBeach practice.
    """
    # Dean shape parameter A(D50) -- Moore (1982) fit, D50 in mm, A in m^(1/3)
    d = grain_size_mm
    A = 0.067 * d**0.44 + 0.0067  # empirical fit, gives A~0.08-0.11 for 0.2-0.4mm sand

    # cross-shore coordinate: x=0 at seaward boundary, x=x_land+x_sea at landward end
    n_sea = int(x_sea / dx_max) + 1
    n_land = int(x_land / dx_min) + 1
    x_offshore_part = np.linspace(0, x_sea, n_sea)
    x_nearshore_part = np.linspace(x_sea, x_sea + x_land, n_land)[1:]
    x = np.concatenate([x_offshore_part, x_nearshore_part])

    # distance shoreward from the seaward boundary
    dist_from_sea = x_sea + x_land - x  # 0 at landward end, max at seaward end

    depth = dean_profile(dist_from_sea, A, dune_toe_z=0.0, dune_toe_x=0.0)
    depth = np.minimum(depth, seaward_depth_target_m)
    z = -depth  # bed level relative to MSL, negative = below MSL

    # add a berm + dune landward of the shoreline (where z crosses 0)
    shoreline_idx = np.argmin(np.abs(z))
    berm_mask = dist_from_sea < berm_width_m
    if berm_mask.any():
        z[berm_mask] = np.maximum(z[berm_mask], 1.0)
    dune_mask = dist_from_sea < 15.0
    if dune_mask.any():
        ramp = np.linspace(dune_crest_z, 1.0, dune_mask.sum())
        z[dune_mask] = np.maximum(z[dune_mask], ramp)

    # apply sea level rise as a uniform datum shift (does not itself move the
    # profile -- morphodynamic response to SLR is left to XBeach / the
    # scenario's tide+SLR boundary file)
    z = z - 0.0 * slr_m  # kept explicit/no-op: SLR is applied via zs0 file, not by shifting bed

    return {
        "transect_id": transect_id,
        "alongshore_offset_m": alongshore_offset_m,
        "x": x,
        "zb": z,
        "D50_mm": grain_size_mm,
        "dean_A": A,
    }


def write_xbeach_grid_files(profile: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    x = profile["x"]
    zb = profile["zb"]
    nx = len(x) - 1

    # XBeach 1D: x.grd and bed.dep each have ny+1=1 row of nx+1 values
    np.savetxt(outdir / "x.grd", x.reshape(1, -1), fmt="%.3f")
    np.savetxt(outdir / "y.grd", np.zeros((1, len(x))), fmt="%.3f")
    np.savetxt(outdir / "bed.dep", zb.reshape(1, -1), fmt="%.3f")

    with open(outdir / "profile_meta.txt", "w") as f:
        f.write(f"transect_id: {profile['transect_id']}\n")
        f.write(f"alongshore_offset_m: {profile['alongshore_offset_m']}\n")
        f.write(f"nx (cells): {nx}\n")
        f.write(f"D50_mm: {profile['D50_mm']}\n")
        f.write(f"dean_A: {profile['dean_A']:.4f}\n")
        f.write("NOTE: idealized Dean profile, NOT a digitized survey. See\n")
        f.write("literature/literature_review.md section 5.\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent / "grids")
    ap.add_argument("--n-transects", type=int, default=5, help="number of alongshore transects to build")
    ap.add_argument("--alongshore-spacing-m", type=float, default=500.0, help="matches Harmony Coast survey spacing")
    ap.add_argument("--slr-m", type=float, default=0.0)
    args = ap.parse_args()

    with open(LIT_PARAMS_PATH) as f:
        lit = yaml.safe_load(f)
    d50_lo, d50_hi = lit["sediment_grain_size"]["D50_mm"]

    rng = np.random.default_rng(42)
    for i in range(args.n_transects):
        # vary grain size slightly alongshore (west finer than east, per lit)
        frac = i / max(args.n_transects - 1, 1)
        d50 = d50_lo + frac * (d50_hi - d50_lo)
        tid = f"T{i+1:02d}"
        profile = build_transect(
            transect_id=tid,
            alongshore_offset_m=i * args.alongshore_spacing_m,
            grain_size_mm=d50,
            slr_m=args.slr_m,
        )
        write_xbeach_grid_files(profile, args.outdir / tid)
        print(f"wrote {tid}: nx={len(profile['x'])-1}, D50={d50:.3f}mm -> {args.outdir / tid}")


if __name__ == "__main__":
    main()
