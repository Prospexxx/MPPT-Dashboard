import os

input_file = "data_mppt_MASTER.txt"
output_files = {
    "1": "wode.txt",
    "2": "woa.txt",
    "3": "de.txt",
    "4": "pno.txt",
    "5": "gmpp.txt"
}

# Open output files
file_handles = {}
for mode, filename in output_files.items():
    file_handles[mode] = open(filename, "w")

try:
    with open(input_file, "r") as f:
        for line in f:
            fields = line.strip().split('\t')
            if len(fields) >= 9:
                mode = fields[8]
                if mode in file_handles:
                    file_handles[mode].write(line)
finally:
    for f in file_handles.values():
        f.close()

print("Parsing complete. Files generated successfully.")
