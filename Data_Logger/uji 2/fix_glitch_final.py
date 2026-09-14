import os

scripts = [
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji motor 2 part 2\karakteristik_i-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_p-v.py',
    r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\uji 2\karakteristik_i-v.py'
]

filter_code_old = '''
            import numpy as np
            # Patch glitch spikes with rolling median replacement data
            for col in ['Vin', 'Iin', 'Pin']:
                rolling = df_gmpp[col].rolling(window=21, center=True, min_periods=1).median()
                threshold = 5.0 if col != 'Iin' else 0.5
                spike_mask = np.abs(df_gmpp[col] - rolling) > threshold
                df_gmpp.loc[spike_mask, col] = rolling[spike_mask]
            
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)'''

filter_code_new = '''
            import numpy as np
            df_gmpp = df_gmpp.reset_index(drop=True)
            
            # 1. Truncate at Duty reset (end of sweep tail)
            duty_diff = df_gmpp['Duty'].diff()
            reset_idx = duty_diff[duty_diff < -10].index
            if len(reset_idx) > 0:
                df_gmpp = df_gmpp.iloc[:reset_idx[0]]
            
            # 2. Patch glitch spikes with rolling median replacement data
            for col in ['Vin', 'Iin', 'Pin']:
                rolling = df_gmpp[col].rolling(window=21, center=True, min_periods=1).median()
                threshold = 5.0 if col != 'Iin' else 0.5
                spike_mask = np.abs(df_gmpp[col] - rolling) > threshold
                df_gmpp.loc[spike_mask, col] = rolling[spike_mask]
            
            df_gmpp = df_gmpp.sort_values(by='Vin').reset_index(drop=True)'''

for s in scripts:
    with open(s, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if filter_code_old in content:
        content = content.replace(filter_code_old, filter_code_new)
        with open(s, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {s}")
    else:
        print(f"Could not find target code in {s}")
