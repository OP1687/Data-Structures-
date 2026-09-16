#!/usr/bin/env bash
# Build inputs for every scenario in scenarios.yaml and (if an `xbeach`
# executable is on PATH) run each one. This repository's sandbox does not
# have XBeach installed (it is a compiled Fortran model with netCDF/MPI
# dependencies -- see root README.md for install options), so this script
# is meant to be run on a machine/HPC/cluster where XBeach is available.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNS_DIR="${HERE}/runs"
mkdir -p "${RUNS_DIR}"

SCENARIOS=(baseline slr_2050_rcp45 slr_2100_rcp85_subsidence mangrove_nbs_intertidal mangrove_nbs_berm)
declare -A SLR_M=( [baseline]=0.0 [slr_2050_rcp45]=0.25 [slr_2100_rcp85_subsidence]=1.1 [mangrove_nbs_intertidal]=0.0 [mangrove_nbs_berm]=0.0 )

for scen in "${SCENARIOS[@]}"; do
  run_dir="${RUNS_DIR}/${scen}"
  mkdir -p "${run_dir}"
  echo "== building inputs for scenario: ${scen} (SLR=${SLR_M[$scen]} m) =="

  python3 "${HERE}/build_bathymetry.py" --outdir "${run_dir}/grids" --slr-m "${SLR_M[$scen]}"
  python3 "${HERE}/build_boundary_conditions.py" --outdir "${HERE}/boundary_conditions/generated" \
      --scenario-name "${scen}" --slr-m "${SLR_M[$scen]}"

  # XBeach 1D is normally run per cross-shore transect; copy params.txt plus
  # transect T01's grid and the scenario's boundary files into a runnable dir.
  transect_dir="${run_dir}/grids/T01"
  bc_dir="${HERE}/boundary_conditions/generated/${scen}"
  scen_run_dir="${run_dir}/T01"
  mkdir -p "${scen_run_dir}"
  cp "${HERE}/params.txt" "${scen_run_dir}/"
  cp "${transect_dir}"/x.grd "${transect_dir}"/y.grd "${transect_dir}"/bed.dep "${scen_run_dir}/"
  cp "${bc_dir}"/filelist.txt "${bc_dir}"/jonswap_*.txt "${bc_dir}"/tide.txt "${scen_run_dir}/" 2>/dev/null || true

  if command -v xbeach >/dev/null 2>&1; then
    echo "   xbeach found on PATH -- running scenario ${scen} (transect T01)"
    (cd "${scen_run_dir}" && xbeach params.txt)
  else
    echo "   [skip] xbeach executable not found on PATH."
    echo "   Input deck is ready at: ${scen_run_dir}"
    echo "   Install XBeach (https://github.com/xbeach/xbeach, requires gfortran + netCDF)"
    echo "   or use the Deltares-provided binary, then re-run this script."
  fi
done

echo
echo "Done. To exercise the analysis/plotting pipeline without a real XBeach"
echo "run, use: python3 ../analysis/demo_synthetic_run.py"
