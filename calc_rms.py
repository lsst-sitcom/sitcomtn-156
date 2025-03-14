from astropy.table import Table
import numpy as np
from tqdm import tqdm
import os
from lsst.ts.wep.utils import makeDense, makeSparse, convertZernikesToPsfWidth


Nvisits = 1269
path_cwd = "/sdf/data/rubin/user/scichris/WORK/AOS/"
fname = os.path.join(
    path_cwd, f"u_scichris_aosBaseline_tie_danish_zernikes_tables_{Nvisits}.npy"
)
results_visit = np.load(fname, allow_pickle=True).item()


fname = os.path.join(
    path_cwd,
    "u_scichris_aosBaseline_danish1_donutQualityTable_N_donuts_all_det_select_good_new.txt",
)
donutQualityTableSel = Table.read(fname, format="ascii")

visits_with_zks = results_visit.keys()
visits_selected = np.unique(donutQualityTableSel["visit"])
visits_calculated = [int(vis) for vis in list(visits_with_zks)]
visits_available = visits_selected[np.isin(visits_selected, visits_calculated)]


# calculation of RMS diff
Nmin = 1
NmaxValue = 10

rms_visit = {}
rms_visit_asec = {}
count = 0
for visit in tqdm(visits_available, desc="Calculating"):
    rms_diffs = {}
    rms_diffs_asec = {}
    for method in results_visit[visit].keys():
        results = results_visit[visit][method]
        rms_diffs[method] = {}
        rms_diffs_asec[method] = {}
        for i in range(9):
            zernikes_all = results[i]
            # select only those zernikes that were actually used
            zernikes = zernikes_all[zernikes_all["used"] == True]

            # read the available names of Zk mode columns
            zk_cols = [col for col in zernikes.columns if col.startswith("Z")]

            # read off which modes were fitted
            zk_modes = [int(col[1:]) for col in zk_cols]

            # select not the stored average,
            # but calculate average using all available donuts
            all_rows = zernikes[Nmin:NmaxValue]
            zk_fit_avg_nm = [np.median(all_rows[col].value) for col in zk_cols]
            zk_fit_avg_nm_dense = makeDense(zk_fit_avg_nm, zk_modes)
            zk_fit_avg_asec_dense = convertZernikesToPsfWidth(
                1e-3 * zk_fit_avg_nm_dense
            )
            zk_fit_avg_asec = makeSparse(zk_fit_avg_asec_dense, zk_modes)

            rms_diffs_per_det = []
            rms_diffs_per_det_asec = []

            # iterate over how many donut pairs to include in the average
            for Nmax in range(1, NmaxValue):

                if Nmax <= len(zernikes):
                    # Select row or a range of rows
                    rows = zernikes[Nmin : Nmin + Nmax]
                    zk_fit_median_nm = [np.median(rows[col].value) for col in zk_cols]
                    zk_fit_median_nm_dense = makeDense(zk_fit_median_nm, zk_modes)
                    zk_fit_median_asec_dense = convertZernikesToPsfWidth(
                        1e-3 * zk_fit_median_nm_dense
                    )
                    zk_fit_median_asec = makeSparse(zk_fit_median_asec_dense, zk_modes)

                    rms_diff = np.sqrt(
                        np.mean(
                            np.square(
                                np.array(zk_fit_avg_nm) - np.array(zk_fit_median_nm)
                            )
                        )
                    )

                    rms_diff_asec = np.sqrt(
                        np.mean(
                            np.square(
                                np.array(zk_fit_avg_asec) - np.array(zk_fit_median_asec)
                            )
                        )
                    )
                    rms_diffs_per_det.append(rms_diff)
                    rms_diffs_per_det_asec.append(rms_diff_asec)
            # print(i, visit, len(rms_diffs_per_det), rms_diffs_per_det[-1])
            rms_diffs[method][i] = rms_diffs_per_det
            rms_diffs_asec[method][i] = rms_diffs_per_det_asec
    # store the results for both methods per visit
    rms_visit[visit] = rms_diffs
    rms_visit_asec[visit] = rms_diffs_asec
    count += 1

Nvisits = len(visits_available)
file = f"u_scichris_aosBaseline_tie_danish_rms_visit_{Nvisits}.npy"
np.save(file, rms_visit, allow_pickle=True)
file = f"u_scichris_aosBaseline_tie_danish_rms_visit_asec_{Nvisits}.npy"
np.save(file, rms_visit_asec, allow_pickle=True)
