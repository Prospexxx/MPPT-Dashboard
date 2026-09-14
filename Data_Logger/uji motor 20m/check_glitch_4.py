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
    plt.plot(df_gmpp['Vin'], df_gmpp['Pin'], 'ro-', markersize=2, label='Raw', alpha=0.3)
    
    # Absolute threshold filter
    df_gmpp['Pin_median_15'] = df_gmpp['Pin'].rolling(window=15, center=True, min_periods=1).median()
    df_filtered = df_gmpp[abs(df_gmpp['Pin'] - df_gmpp['Pin_median_15']) <= 6.0]
    
    plt.plot(df_filtered['Vin'], df_filtered['Pin'], 'bo-', markersize=2, label='Filter abs <= 6.0', alpha=0.9)

    plt.legend()
    plt.title(f'Run {run}')
    plt.savefig(os.path.join(base_dir, f'test_abs_filter_run{run}.png'))
    plt.close()
