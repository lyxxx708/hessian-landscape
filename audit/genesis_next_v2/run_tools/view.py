import pandas as pd
pd.set_option('display.width',250,'display.max_columns',40)
O=r'E:\GENESIS\runs\genesis_next_v2'
s=pd.read_csv(O+r'\SEED_SUMMARY.csv')
print(s[['setting_id','gamma','independent_seed_n','delta_median','delta_ci_low','delta_ci_high','null_energy_fraction_median','gradient_null_fraction_median','inverse_offdiag_fraction_median','cg_grid_k_matching_block_gain_median','cg_matching_wall_ratio_vs_block_median','cg_never_matches_block_n']].round(4).to_string())
print(pd.read_csv(O+r'\STRUCTURE_UTILITY_ASSOCIATIONS.csv').round(3).to_string())
r=pd.read_csv(O+r'\SCIENTIFIC_RESULTS.csv')
print(r[['delta','block_val_gain','full_val_gain','matched_wall_ratio_vs_block','cg_matching_wall_ratio_vs_block']].describe().round(4))
print((r.block_val_gain<0).mean(), (r.full_val_gain<0).mean(), r.original_v2_status.value_counts().to_dict())
c=pd.read_csv(O+r'\CG_COST_COMPARISON.csv')
print(c.groupby('comparator')[['gain_ratio','solve_wall_vs_block','beats_or_equals_block']].mean().round(3))
q=pd.read_csv(O+r'\NUMERICAL_QUALIFICATION.csv');print(q.status.value_counts(),q.v2_status.value_counts())
