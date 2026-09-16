"""
Common loader for XBeach-style morphodynamic output.

Supports two sources, returning the same plain dict schema either way:
  {
    "time_days": 1D array, days since run start,
    "x":         1D array, cross-shore coordinate (m), seaward -> landward,
    "zb":        2D array [time, x], bed level (m, + up, relative to MSL),
    "transect_id": str,
    "alongshore_offset_m": float,
    "scenario": str,
    "is_synthetic": bool,   # True for the demo pipeline-test data
  }

1. Real XBeach output: a netCDF file (xboutput.nc, written when
   `outputformat = netcdf` in params.txt) with variables `globaltime`,
   `globalx` (or `x`), and `zb`. Requires the optional `netCDF4` package.
2. Demo/synthetic output: an .npz file written by demo_synthetic_run.py.
   Always carries is_synthetic=True and is clearly for pipeline-testing only
   -- see literature/literature_review.md section 5.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np


def load_run(path: str | Path) -> dict:
    path = Path(path)
    if path.suffix == ".npz":
        return _load_synthetic(path)
    if path.suffix in (".nc", ".cdf"):
        return _load_netcdf(path)
    raise ValueError(f"Unrecognized XBeach output format: {path}")


def _load_synthetic(path: Path) -> dict:
    d = np.load(path, allow_pickle=True)
    return {
        "time_days": d["time_days"],
        "x": d["x"],
        "zb": d["zb"],
        "transect_id": str(d["transect_id"]),
        "alongshore_offset_m": float(d["alongshore_offset_m"]),
        "scenario": str(d["scenario"]),
        "is_synthetic": True,
    }


def _load_netcdf(path: Path) -> dict:
    try:
        import netCDF4
    except ImportError as e:
        raise ImportError(
            "Reading real XBeach netCDF output requires the netCDF4 package "
            "(`pip install netCDF4`)."
        ) from e
    ds = netCDF4.Dataset(path)
    time_s = ds.variables["globaltime"][:]
    x = ds.variables["globalx"][:]
    if x.ndim > 1:
        x = x[0, :]  # 1D XBeach: alongshore dim is length 1
    zb = ds.variables["zb"][:]
    if zb.ndim == 3:
        zb = zb[:, 0, :]  # [time, y, x] -> [time, x] for 1D runs
    ds.close()
    return {
        "time_days": np.asarray(time_s) / 86400.0,
        "x": np.asarray(x),
        "zb": np.asarray(zb),
        "transect_id": path.parent.name,
        "alongshore_offset_m": float("nan"),
        "scenario": path.parent.parent.name if path.parent.parent else "unknown",
        "is_synthetic": False,
    }
