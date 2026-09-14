import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

base_dir = os.path.dirname(__file__)
nama_file = os.path.join(base_dir, 'gmpp_1.txt')

kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty', 'Run_Num']
df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom, on_bad_lines='skip')
df = df.apply(pd.to_numeric, errors='coerce').dropna()
df_gmpp = df[df['Mode'] == 5]
if df_gmpp.empty: df_gmpp = df
df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)

# Plot raw
plt.plot(df_gmpp['Vin'], df_gmpp['Pin'], label='Raw')

# Filter
df_gmpp['Pin_median'] = df_gmpp['Pin'].rolling(window=15, center=True, min_periods=1).median()
df_gmpp_filtered = df_gmpp[df_gmpp['Pin'] >= df_gmpp['Pin_median'] - 10]

# Plot filtered
plt.plot(df_gmpp_filtered['Vin'], df_gmpp_filtered['Pin'], label='Filtered')
plt.legend()
plt.savefig(os.path.join(base_dir, 'glitch_test.png'))
print(f"Original points: {len(df_gmpp)}, Filtered points: {len(df_gmpp_filtered)}")
