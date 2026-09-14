import os

scripts = [
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_i-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_i-v.py'
]

filter_code = '''
            import numpy as np
            # Remove glitch spikes (isolated drops/spikes > 5)
            rolling_pin = df_gmpp['Pin'].rolling(window=5, center=True).median()
            rolling_vin = df_gmpp['Vin'].rolling(window=5, center=True).median()
            spike_mask = (np.abs(df_gmpp['Pin'] - rolling_pin) > 5.0) | (np.abs(df_gmpp['Vin'] - rolling_vin) > 5.0)
            df_gmpp = df_gmpp[~spike_mask]
            
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)'''

for s in scripts:
    with open(s, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)", filter_code)
    
    with open(s, 'w', encoding='utf-8') as f:
        f.write(content)

print("Updated all scripts with spike filter.")
