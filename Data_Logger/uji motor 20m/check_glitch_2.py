import os
import pandas as pd
import matplotlib.pyplot as plt

base_dir = os.path.dirname(__file__)

for run in [2, 3]:
    nama_file = os.path.join(base_dir, f'gmpp_{run}.txt')
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']
    df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    df_gmpp = df[df['Mode'] == 5]
    if df_gmpp.empty: df_gmpp = df

    df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)

    plt.figure()
    plt.plot(df_gmpp['Vin'], df_gmpp['Pin'], label='Raw', alpha=0.3)
    
    # New Anti-Glitch Algorithm:
    # 1. Take upper envelope by binning
    df_gmpp['Vin_bin'] = df_gmpp['Vin'].round(1)
    idx_max = df_gmpp.groupby('Vin_bin')['Pin'].idxmax()
    df_env = df_gmpp.loc[idx_max].sort_values(by='Vin').reset_index(drop=True)
    
    # 2. Iteratively remove local minimums (dips)
    # A point is a dip if it is significantly lower than the interpolation between its neighbors.
    changed = True
    while changed:
        changed = False
        to_drop = []
        for i in range(1, len(df_env) - 1):
            # linear interpolation between left and right neighbor
            v_prev, p_prev = df_env.loc[i-1, 'Vin'], df_env.loc[i-1, 'Pin']
            v_next, p_next = df_env.loc[i+1, 'Vin'], df_env.loc[i+1, 'Pin']
            v_curr, p_curr = df_env.loc[i, 'Vin'], df_env.loc[i, 'Pin']
            
            # expected power at v_curr
            if v_next != v_prev:
                p_expected = p_prev + (p_next - p_prev) * (v_curr - v_prev) / (v_next - v_prev)
            else:
                p_expected = max(p_prev, p_next)
                
            # If the actual power is significantly lower than the straight line connecting neighbors (a dip)
            if p_curr < p_expected - 2.0:  # 2W threshold for a dip
                to_drop.append(i)
                
        if to_drop:
            # Only drop the deepest dip in this pass to avoid destroying the curve
            deepest = max(to_drop, key=lambda x: (df_env.loc[x-1, 'Pin'] + df_env.loc[x+1, 'Pin'])/2 - df_env.loc[x, 'Pin'])
            df_env = df_env.drop(deepest).reset_index(drop=True)
            changed = True
            
    plt.plot(df_env['Vin'], df_env['Pin'], label='No Dips Envelope', alpha=0.9)

    plt.legend()
    plt.title(f'Run {run}')
    plt.savefig(os.path.join(base_dir, f'test_dip_run{run}.png'))
    plt.close()
