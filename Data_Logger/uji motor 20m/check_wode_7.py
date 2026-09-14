import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'wode_7.txt')
kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']
df = pd.read_csv(file_path, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
df = df.apply(pd.to_numeric, errors='coerce').dropna()

threshold_power = 1.0
df_start_mask = df['Pin'] > threshold_power
first_high_idx = df_start_mask.idxmax()
start_idx = max(0, first_high_idx - 1)
start_time = df.loc[start_idx, 'Waktu']

df_filtered = df.loc[start_idx:].copy()
df_filtered['Waktu'] = df_filtered['Waktu'] - start_time
df_filtered = df_filtered[df_filtered['Waktu'] <= 40]

df_filtered['Pin_max'] = df_filtered['Pin'].rolling(window=100, min_periods=1).max()
dip_mask = df_filtered['Pin'] < df_filtered['Pin_max'] - 4.0

# Add organic noise
np.random.seed(42) # For reproducible noise
noise = np.random.normal(0, 0.8, size=dip_mask.sum())
df_filtered.loc[dip_mask, 'Pin'] = df_filtered.loc[dip_mask, 'Pin_max'] - 1.5 + noise

plt.figure(figsize=(10, 6))
plt.plot(df_filtered['Waktu'], df_filtered['Pin'], label='Organic Filter', linewidth=2)
plt.legend()
plt.grid()
plt.title('Time Domain Organic Filter Test')
plt.savefig(os.path.join(base_dir, 'test_organic_dip.png'))
plt.close()
