import os

d = r'c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger'
for sd in sorted(os.listdir(d)):
    full = os.path.join(d, sd)
    if os.path.isdir(full) and sd != '__pycache__':
        gmpp = sorted([f for f in os.listdir(full) if f.startswith('gmpp') and f.endswith('.txt')])
        print(f"{sd}: {gmpp}")
