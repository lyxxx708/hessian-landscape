import pandas as pd
r=pd.read_csv(r'E:\GENESIS\runs\genesis_next_v2\SCIENTIFIC_RESULTS.csv');q=pd.read_csv(r'E:\GENESIS\runs\genesis_next_v2\NUMERICAL_QUALIFICATION.csv')
print(r[['gradient_weighted_n99','effective_gain_directions','full_matvecs','gradient_null_fraction','null_energy_fraction','inverse_offdiag_fraction','nullity']].agg(['min','median','max']).round(5).to_string())
print(q[['operator_crosscheck_max','grad_crosscheck','full_direction_relative_error','dense_delta_error','full_true_residual']].max())
