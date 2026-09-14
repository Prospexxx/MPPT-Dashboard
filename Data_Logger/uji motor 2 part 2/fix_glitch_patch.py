import os

scripts = [
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_i-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_i-v.py'
]

filter_code_old = '''
            import numpy as np
            # Remove glitch spikes (isolated drops/spikes > 5)
            rolling_pin = df_gmpp['Pin'].rolling(window=5, center=True).median()
            rolling_vin = df_gmpp['Vin'].rolling(window=5, center=True).median()
            spike_mask = (np.abs(df_gmpp['Pin'] - rolling_pin) > 5.0) | (np.abs(df_gmpp['Vin'] - rolling_vin) > 5.0)
            df_gmpp = df_gmpp[~spike_mask]
            
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)'''

filter_code_new = '''
            import numpy as np
            # Patch glitch spikes with rolling median replacement data
            for col in ['Vin', 'Iin', 'Pin']:
                rolling = df_gmpp[col].rolling(window=21, center=True, min_periods=1).median()
                threshold = 5.0 if col != 'Iin' else 0.5
                spike_mask = np.abs(df_gmpp[col] - rolling) > threshold
                df_gmpp.loc[spike_mask, col] = rolling[spike_mask]
            
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)'''

for s in scripts:
    with open(s, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace(filter_code_old, filter_code_new)
    
    with open(s, 'w', encoding='utf-8') as f:
        f.write(content)

print("Updated all scripts with patching filter.")
