from lsst.daf.butler import Butler
from astropy.time import Time
import astropy.units as u
import numpy as np
from tqdm import tqdm
import os
import sys


def calcTaskRuntime(metadata):
    t1 = Time(metadata["quantum"]["prepUtc"].split("+")[0], format="isot", scale="utc")
    t2 = Time(metadata["quantum"]["endUtc"].split("+")[0], format="isot", scale="utc")
    return (t2 - t1).to_value(u.second)


butlerRootPath = "/repo/main"
butler = Butler(butlerRootPath)

registry = butler.registry
results_timing = {}

binning = 2
method = "tie"
fname = f"DM-49211_u_scichris_aosBaseline_binning_{binning}_{method}_timing.npy"
if os.path.exists(fname):
    print(f"File {fname} already exists ")
    sys.exit("Exiting the program, nothing to do")

else:
    print(f"Reading {binning} for {method}")
    results = {
        "NobjMeas": [],
        "NobjSel": [],
        "NobjCalc": [],
        "cwfsTime": [],
        "visit": [],
        "detector": [],
    }
    output_collection = f"u/scichris/aosBaseline_{method}_binning_{binning}"

    # get the available refs from the processed visits
    datasetRefs = list(
        registry.queryDatasets(
            "zernikes",
            collections=[output_collection],
        ).expanded()
    )
    for ref in tqdm(datasetRefs, desc="Processing"):

        # Check log from donut detection
        logDetect = butler.get(
            "generateDonutDirectDetectTask_log",
            dataId=ref.dataId,
            collections=["u/brycek/aosBaseline_step1a"],
        )

        # Message 'Selected 17/30 sources'
        for iDetect in [-1, -2, -3, -4]:
            msg = logDetect[iDetect].message
            if msg.startswith("Selected"):
                measuredSources = int(msg.split(" ")[1].split("/")[1])
                selectedSources = int(msg.split(" ")[1].split("/")[0])

                # Only if there were any sources selected, check log from Zernike estimation
                logCalc = butler.get(
                    "calcZernikesTask_log",
                    dataId=ref.dataId,
                    collections=[output_collection],
                )
                # Message 'Selected 6/17 donut stamps'
                for iCalc in [-1, -2, -3, -4]:
                    msg = logCalc[iCalc].message
                    if msg.startswith("Selected"):

                        # Only if Zernikes were calculated does it make sense to consider this
                        calculatedSources = int(msg.split(" ")[1].split("/")[0])

                        # Record visit number and detector
                        results["visit"].append(ref.dataId["visit"])
                        results["detector"].append(ref.dataId["detector"])

                        # Store timing
                        results["NobjMeas"].append(measuredSources)
                        results["NobjSel"].append(selectedSources)
                        results["NobjCalc"].append(calculatedSources)

                        # Store Estimation time which is always available, even if task was not run
                        # due to no donutStampsExtra, donutStampsIntra
                        metaCalc = butler.get(
                            "calcZernikesTask_metadata",
                            dataId=ref.dataId,
                            collections=[output_collection],
                        )
                        results["cwfsTime"].append(calcTaskRuntime(metaCalc))

                    else:
                        continue

    print(f"Saving  as {fname}")
    np.save(
        fname,
        results,
    )
