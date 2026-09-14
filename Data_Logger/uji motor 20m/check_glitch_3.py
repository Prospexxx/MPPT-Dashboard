import os
import pandas as pd
import numpy as np

base_dir = os.path.dirname(__file__)

run = 3
nama_file = os.path.join(base_dir, f'gmpp_{run}.txt')
kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']
df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
df = df.apply(pd.to_numeric, errors='coerce').dropna()
df_gmpp = df[df['Mode'] == 5]
if df_gmpp.empty: df_gmpp = df

df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)

df_gmpp['Vin_bin'] = df_gmpp['Vin'].round(1)
idx_max = df_gmpp.groupby('Vin_bin')['Pin'].idxmax().dropna()
df_gmpp = df_gmpp.loc[idx_max].sort_values(by='Vin').reset_index(drop=True)

changed = True
while changed:
    changed = False
    to_drop = []
    for i in range(1, len(df_gmpp) - 1):
        v_prev, p_prev = df_gmpp.loc[i-1, 'Vin'], df_gmpp.loc[i-1, 'Pin']
        v_next, p_next = df_gmpp.loc[i+1, 'Vin'], df_gmpp.loc[i+1, 'Pin']
        v_curr, p_curr = df_gmpp.loc[i, 'Vin'], df_gmpp.loc[i, 'Pin']
        
        if v_next != v_prev:
            p_expected = p_prev + (p_next - p_prev) * (v_curr - v_prev) / (v_next - v_prev)
        else:
            p_expected = max(p_prev, p_next)
            
        if p_curr < p_expected - 2.0:
            to_drop.append(i)
            
    if to_drop:
        deepest = max(to_drop, key=lambda x: (df_gmpp.loc[x-1, 'Pin'] + df_gmpp.loc[x+1, 'Pin'])/2 - df_gmpp.loc[x, 'Pin'])
        df_gmpp = df_gmpp.drop(deepest).reset_index(drop=True)
        changed = True

# Let's print out the sequence of Vin and Pin to see the shape
print(f"Final points for Run 3: {len(df_gmpp)}")
pd.set_option('display.max_rows', None)
print(df_gmpp[['Vin', 'Pin', 'Iin']])

