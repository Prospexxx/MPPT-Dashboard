import os

d = r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger'
folders = ['uji 2', 'uji jam 2', 'uji motor 2 part 2', 'uji resistor', 'ujimotor']

for sd in folders:
    fp = os.path.join(d, sd, 'gmpp.txt')
    with open(fp) as f:
        line = f.readline().strip()
    cols = line.split()
    print(f"{sd}: {len(cols)} cols -> {cols}")
