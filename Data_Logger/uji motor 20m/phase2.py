import os
import glob

# The modes and their corresponding output files from phase 1
files = ["wode.txt", "woa.txt", "de.txt", "pno.txt", "gmpp.txt"]
threshold = 1.0  # 1.0 second threshold to detect a new run, since sampling rate is 100ms (0.1s)

for filename in files:
    if not os.path.exists(filename):
        continue
        
    with open(filename, "r") as f:
        lines = f.readlines()
        
    if not lines:
        continue
        
    run_counter = 1
    prev_time = None
    
    base_name = filename.split('.')[0]
    out_filename = f"{base_name}_{run_counter}.txt"
    out_f = open(out_filename, "w")
    
    print(f"Processing {filename}...")
    
    for line in lines:
        fields = line.strip().split('\t')
        if not fields:
            continue
            
        try:
            curr_time = float(fields[0])
        except ValueError:
            # If header or unparseable, just write and continue
            out_f.write(line)
            continue
            
        # Detect new run if time jumps by more than the threshold
        if prev_time is not None and (curr_time - prev_time) > threshold:
            out_f.close()
            run_counter += 1
            out_filename = f"{base_name}_{run_counter}.txt"
            out_f = open(out_filename, "w")
            print(f"  -> Detected new run, created {out_filename} at time {curr_time}")
            
        # Write the line, optionally we could append the run_counter to the line here
        # but creating separate files is standard. Let's also append the run_counter as a new column 
        # so they have it in the file as well!
        new_line = line.rstrip('\n') + f"\t{run_counter}\n"
        out_f.write(new_line)
        
        prev_time = curr_time
        
    out_f.close()

print("Phase 2 parsing complete.")
