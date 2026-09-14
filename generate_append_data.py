import math
import sys
import os
from datetime import datetime, timedelta

def get_sin_factor(dt):
    hours = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    # Sunrise 6 AM, Sunset 6 PM
    angle = (hours - 6.0) / 12.0 * math.pi
    if angle < 0: angle = 0
    if angle > math.pi: angle = math.pi
    val = math.sin(angle)
    return max(val, 0.01)

class Row:
    def __init__(self, line):
        self.original_line = line
        parts = line.split(']')
        self.dt_str = parts[0][1:]
        self.dt = datetime.strptime(self.dt_str, "%Y-%m-%d %H:%M:%S")
        data = parts[1].strip().split()
        self.t = float(data[0])
        self.vin = float(data[1])
        self.iin = float(data[2])
        self.pin = float(data[3])
        self.vout = float(data[4])
        self.iout = float(data[5])
        self.pout = float(data[6])
        self.eff = float(data[7])
        self.mode = data[8]
        self.duty = data[9]
        self.sin_f = get_sin_factor(self.dt)

    def generate_scaled_string(self, target_dt, target_t, t_offset=0):
        target_f = get_sin_factor(target_dt)
        multiplier = target_f / self.sin_f
        
        iin_new = self.iin * multiplier
        pin_new = self.pin * multiplier
        iout_new = self.iout * multiplier
        pout_new = self.pout * multiplier
        
        final_t = target_t + t_offset
        
        dt_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{dt_str}] {final_t:.3f}\t{self.vin:.2f}\t{iin_new:.2f}\t{pin_new:.2f}\t{self.vout:.2f}\t{iout_new:.2f}\t{pout_new:.2f}\t{self.eff:.2f}\t{self.mode}\t{self.duty}\n"
        
    def get_original_string_with_offset(self, t_offset=0):
        final_t = self.t + t_offset
        dt_str = self.dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{dt_str}] {final_t:.3f}\t{self.vin:.2f}\t{self.iin:.2f}\t{self.pin:.2f}\t{self.vout:.2f}\t{self.iout:.2f}\t{self.pout:.2f}\t{self.eff:.2f}\t{self.mode}\t{self.duty}\n"

def process():
    input_file = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\run_20260628_110119\data_mppt_MASTER_20260628_110119.txt"
    output_file = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\run_20260628_110119\data_mppt_MASTER_20260628_110119_manipulated.txt"
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r') as f:
        raw_lines = f.readlines()
        
    rows = []
    for line in raw_lines:
        line = line.strip()
        if line and len(line.split()) >= 10:
            try:
                rows.append(Row(line))
            except Exception:
                pass
                
    if not rows:
        print("No valid rows found.")
        return
        
    start_dt = rows[0].dt
    end_dt = rows[-1].dt
    t_start = rows[0].t
    t_end = rows[-1].t
    N = len(rows)
    
    dt_avg = (t_end - t_start) / (N - 1)
    
    def ping_pong(start_idx, start_dir):
        idx = start_idx
        d = start_dir
        while True:
            yield rows[idx]
            idx += d
            if idx >= N:
                idx = N - 2
                d = -1
            elif idx < 0:
                idx = 1
                d = 1

    # 1. Generate backwards from 11:01 down to 07:00
    target_start = datetime(start_dt.year, start_dt.month, start_dt.day, 7, 0, 0)
    
    # Pre-calculate what the earliest 't' will be so we can find the offset
    curr_dt_test = start_dt - timedelta(seconds=dt_avg)
    curr_t_test = t_start - dt_avg
    while curr_dt_test >= target_start:
        curr_dt_test -= timedelta(seconds=dt_avg)
        curr_t_test -= dt_avg
    
    # curr_t_test is now the minimum t value (which is negative)
    # We want the file to start at t = 0.000
    t_offset = abs(curr_t_test) if curr_t_test < 0 else 0
    
    print(f"Calculated time offset to prevent negative values: +{t_offset:.3f}")

    synthetic_before = []
    gen_before = ping_pong(1, 1)
    curr_dt = start_dt - timedelta(seconds=dt_avg)
    curr_t = t_start - dt_avg
    
    print("Generating synthetic data backwards to 7:00 AM...")
    while curr_dt >= target_start:
        orig_row = next(gen_before)
        synthetic_before.append(orig_row.generate_scaled_string(curr_dt, curr_t, t_offset))
        curr_dt -= timedelta(seconds=dt_avg)
        curr_t -= dt_avg
        
    synthetic_before.reverse()
    
    # 2. Original data
    print("Preserving original data (shifting t)...")
    original_strings = [r.get_original_string_with_offset(t_offset) for r in rows]
    
    # 3. Generate forwards from 11:28 up to 15:00
    target_end = datetime(end_dt.year, end_dt.month, end_dt.day, 15, 0, 0)
    synthetic_after = []
    gen_after = ping_pong(N - 2, -1)
    curr_dt = end_dt + timedelta(seconds=dt_avg)
    curr_t = t_end + dt_avg
    
    print("Generating synthetic data forwards to 3:00 PM...")
    while curr_dt <= target_end:
        orig_row = next(gen_after)
        synthetic_after.append(orig_row.generate_scaled_string(curr_dt, curr_t, t_offset))
        curr_dt += timedelta(seconds=dt_avg)
        curr_t += dt_avg
        
    print("Writing all data to file...")
    with open(output_file, 'w') as out:
        out.writelines(synthetic_before)
        out.writelines(original_strings)
        out.writelines(synthetic_after)
        
    print(f"Done! Created file with {len(synthetic_before)} prepended lines, {len(original_strings)} original lines, and {len(synthetic_after)} appended lines.")
    print(f"Total lines: {len(synthetic_before) + len(original_strings) + len(synthetic_after)}")

if __name__ == "__main__":
    process()
