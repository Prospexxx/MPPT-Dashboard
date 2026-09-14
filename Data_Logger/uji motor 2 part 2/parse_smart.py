import pandas as pd
import os

input_file = 'uji2part2.txt'

print(f"Reading {input_file}...")
df = pd.read_csv(input_file, sep='\t', header=None, on_bad_lines='skip')
df = df.apply(pd.to_numeric, errors='coerce').dropna(subset=[8, 0])

# Find blocks of continuous mode & continuous time
blocks = []
current_block = []
last_mode = -1
last_time = -1

for idx, row in df.iterrows():
    mode = int(row[8])
    t = row[0]
    
    # New block if mode changes or time drops (timer reset)
    if mode != last_mode or t < last_time:
        if current_block:
            blocks.append({
                'mode': last_mode,
                'start_time': current_block[0][0],
                'end_time': current_block[-1][0],
                'duration': current_block[-1][0] - current_block[0][0],
                'data': current_block
            })
        current_block = []
        last_mode = mode
        
    current_block.append(row.values)
    last_time = t

if current_block:
    blocks.append({
        'mode': last_mode,
        'start_time': current_block[0][0],
        'end_time': current_block[-1][0],
        'duration': current_block[-1][0] - current_block[0][0],
        'data': current_block
    })

# Group into runs based on GMPP (Mode 5) triggers
runs = []
current_run = {}
run_index = -1

for b in blocks:
    if b['mode'] == 5 and b['duration'] > 10:
        run_index += 1
        current_run = {}
        runs.append(current_run)
        
    if run_index >= 0:
        mode_str = str(b['mode'])
        # If this mode hasn't been added to the current run yet AND it's > 10s
        if mode_str not in current_run and b['duration'] > 10:
            current_run[mode_str] = b['data']

mode_map = {'1': 'wode', '2': 'woa', '3': 'de', '4': 'pno', '5': 'gmpp'}

# Write out the clean runs
for i, run_data in enumerate(runs):
    suffix = '' if i == 0 else str(i)
    for m, m_name in mode_map.items():
        if m in run_data:
            fname = f'{m_name}{suffix}.txt'
            print(f'Writing {fname} with {len(run_data[m])} rows')
            with open(fname, 'w') as f:
                for row in run_data[m]:
                    formatted_row = []
                    for j, x in enumerate(row):
                        if j == 0:
                            formatted_row.append(f'{x:.3f}')
                        elif j == 8:
                            formatted_row.append(str(int(x)))
                        else:
                            formatted_row.append(f'{x:.2f}')
                    f.write('\t'.join(formatted_row) + '\n')

print("Smart parsing complete. Cleaned files generated successfully.")
