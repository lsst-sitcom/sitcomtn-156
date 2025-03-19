from astropy.table import Table
import astropy.units as u
from lsst.daf.butler import Butler
import numpy as np
from tqdm import tqdm
import os

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

# Setup butler
butler = Butler("/repo/main")

results_visit_mags = {}
for visit in tqdm(visits_available, desc="Processing"):

    results_mags = {}
    for detector in range(9):

        dataId = {"instrument": "LSSTComCam", "detector": detector, "visit": visit}
        donutTableExtra = butler.get(
            "donutTable", dataId=dataId, collections=["u/brycek/aosBaseline_step1a"]
        )
        donutQualityTable = butler.get(
            "donutQualityTable",
            dataId=dataId,
            collections=["u/scichris/aosBaseline_tie_binning_1"],
        )

        extraDonuts = donutQualityTable[donutQualityTable["DEFOCAL_TYPE"] == "extra"]
        extraDonuts["index"] = np.arange(len(extraDonuts))

        extraIndices = extraDonuts[extraDonuts["FINAL_SELECT"]]["index"]
        idxExtra = np.array(extraIndices.data, dtype=int)

        donutTableExtraSelect = donutTableExtra[idxExtra]
        mags = (donutTableExtra[idxExtra]["source_flux"].value * u.nJy).to_value(
            u.ABmag
        )

        results_mags[detector] = {"donutStampsExtraMag": mags}
    results_visit_mags[visit] = results_mags


Nvisits = len(visits_available)
file = f"u_scichris_aosBaseline_tie_danish_mag_visit_{Nvisits}.npy"
np.save(file, results_visit_mags, allow_pickle=True)
