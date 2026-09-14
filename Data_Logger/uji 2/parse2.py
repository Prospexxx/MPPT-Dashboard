import os

input_file = 'ujimotor2.txt'

mode_map = {
    '1': 'wode',
    '2': 'woa',
    '3': 'de',
    '4': 'pno',
    '5': 'gmpp'
}

run_counts = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
last_mode = None
files = {}

with open(input_file, 'r') as f:
    for line in f:
        fields = line.strip().split('\t')
        if len(fields) >= 9:
            mode = fields[8]
            if mode in mode_map:
                if mode != last_mode:
                    run_counts[mode] += 1
                    last_mode = mode
                    
                    suffix = '' if run_counts[mode] == 1 else str(run_counts[mode] - 1)
                    fname = f"{mode_map[mode]}{suffix}.txt"
                    print(f'Writing to {fname}')
                    
                    if mode in files:
                        files[mode].close()
                    files[mode] = open(fname, 'w')
                    
                files[mode].write(line)

for f in files.values():
    f.close()

print("Parsing complete. Files generated successfully.")
