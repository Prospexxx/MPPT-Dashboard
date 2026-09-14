import pandas as pd
import numpy as np

input_file = 'test.txt'

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
current_run = {'gmpp': None, 'wode_blocks': []}

for b in blocks:
    if b['mode'] == 5 and b['duration'] > 10:
        if current_run['gmpp'] is not None:
            runs.append(current_run)
        current_run = {'gmpp': b['data'], 'wode_blocks': []}
        
    elif b['mode'] == 1 and b['duration'] > 5 and current_run['gmpp'] is not None:
        current_run['wode_blocks'].append(b['data'])

runs.append(current_run)

# Evaluate and save the best WODE block for each run
for i, run_data in enumerate(runs):
    if not run_data['gmpp'] or not run_data['wode_blocks']:
        continue
        
    gmpp_df = pd.DataFrame(run_data['gmpp'])
    gmpp_max = gmpp_df[3].max()
    target_power = 0.95 * gmpp_max
    
    best_wode = None
    best_score = -float('inf')
    best_tt = float('inf')
    
    for j, w in enumerate(run_data['wode_blocks']):
        w_df = pd.DataFrame(w)
        w_max = w_df[3].max()
        
        above_target = w_df[w_df[3] >= target_power]
        if not above_target.empty:
            tt = above_target.iloc[0, 0] - w_df.iloc[0, 0]
        else:
            tt = float('inf')
            
        # We only consider blocks that actually track successfully (unless none do)
        # To avoid picking a block from a different irradiance condition (e.g. 120W when GMPP was 60W),
        # we penalize powers that are ridiculously higher than GMPP max (e.g. > 1.5x)
        if w_max > 1.5 * gmpp_max:
            continue
            
        # Score: We heavily weight reaching the target (finite tt)
        # If both reach target, we prefer higher power. If powers are similar, prefer faster tt.
        score = w_max
        if tt == float('inf'):
            score -= 1000  # huge penalty for not reaching target
            
        if score > best_score:
            best_score = score
            best_wode = w
            best_tt = tt
        elif abs(score - best_score) < 1.0 and tt < best_tt:
            # If power is very similar (within 1W), pick the one with faster tracking time
            best_score = score
            best_wode = w
            best_tt = tt
            
    if best_wode is not None:
        suffix = '' if i == 0 else str(i)
        fname = f'wode{suffix}.txt'
        print(f'Run {i}: GMPP Max={gmpp_max:.2f}W. Picked WODE with Max={pd.DataFrame(best_wode)[3].max():.2f}W, TT={best_tt:.2f}s -> Saved to {fname}')
        
        with open(fname, 'w') as f:
            for row in best_wode:
                formatted_row = []
                for j, x in enumerate(row):
                    if j == 0:
                        formatted_row.append(f'{x:.3f}')
                    elif j == 8:
                        formatted_row.append(str(int(x)))
                    else:
                        formatted_row.append(f'{x:.2f}')
                f.write('\t'.join(formatted_row) + '\n')

print("WODE parsing complete.")
