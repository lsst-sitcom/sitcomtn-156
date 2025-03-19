from astropy.table import Table
import numpy as np
import os

results_timing = {}

for method in ['tie', 'danish']:
    for binning in [1, 2, 4]:

        input_fname = f"DM-49211_u_scichris_aosBaseline_binning_{binning}_{method}_timing.npy"
        clean_fname = f'DM-49211_u_scichris_aosBaseline_binning_{binning}_{method}_timing_table.txt'
        if os.path.exists(clean_fname):
            print(f"File {clean_fname} already exists; nothing to do")
            continue
        else
            if os.path.exists(input_fname):
                results_timing = np.load(input_fname, allow_pickle=True).item()
                print(f"Reading from {input_fname}")
            else:
                print(f"Need to first execute python read_runtime.py in the technote github repository")

        visit_table = Table(data=[  results_timing['NobjMeas'], 
                                    results_timing['NobjSel'],
                                    results_timing['NobjCalc'],
                                    results_timing['cwfsTime'],
                                    results_timing['visit'],
                                    results_timing['detector'],
                                 ],
                            names=['NobjMeas', 'NobjSel', 'NobjCalc', 'cwfsTime', 'visit', 'detector']
                           )
        
        # Step 1: Group by "visit"
        grouped = visit_table.group_by('visit')
        
        # Step 2: Remove duplicate "detector" entries within each group
        unique_rows = []
        for group in grouped.groups:
            _, unique_indices = np.unique(group['detector'], return_index=True)
            unique_rows.extend(group[unique_indices])
        
        # Step 3: Reassemble into a new table
        cleaned_table = Table(rows=unique_rows, names=visit_table.colnames)
        
        # Store the cleaned table so that each visit / detector is represented once
        
        cleaned_table.write(clean_fname, format='ascii')
