import math
import sys
import os
import random
from datetime import datetime, timedelta

def get_sin_factor(dt):
    hours = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    # Sunrise 6 AM, Sunset 6 PM
    angle = (hours - 6.0) / 12.0 * math.pi
    if angle < 0: angle = 0
    if angle > math.pi: angle = math.pi
    return max(math.sin(angle), 0.01)

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
        self.base_pin = self.pin / self.sin_f if self.sin_f > 0 else self.pin

    def generate_organic_string(self, target_dt, target_t, cloud_factor, t_offset=0):
        target_f = get_sin_factor(target_dt)
        
        # small high frequency noise
        noise = random.uniform(0.98, 1.02)
        multiplier = (target_f / self.sin_f) * cloud_factor * noise
        
        iin_new = self.iin * multiplier
        pin_new = self.pin * multiplier
        iout_new = self.iout * multiplier
        pout_new = self.pout * multiplier
        
        # Add tiny noise to voltages to make them look alive
        vin_new = self.vin * random.uniform(0.995, 1.005)
        vout_new = self.vout * random.uniform(0.995, 1.005)
        
        final_t = target_t + t_offset
        dt_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"[{dt_str}] {final_t:.3f}\t{vin_new:.2f}\t{iin_new:.2f}\t{pin_new:.2f}\t{vout_new:.2f}\t{iout_new:.2f}\t{pout_new:.2f}\t{self.eff:.2f}\t{self.mode}\t{self.duty}\n"
        
    def get_original_string_with_offset(self, t_offset=0):
        final_t = self.t + t_offset
        dt_str = self.dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{dt_str}] {final_t:.3f}\t{self.vin:.2f}\t{self.iin:.2f}\t{self.pin:.2f}\t{self.vout:.2f}\t{self.iout:.2f}\t{self.pout:.2f}\t{self.eff:.2f}\t{self.mode}\t{self.duty}\n"

class FractalNoiseCloud:
    def __init__(self):
        # Generate random frequencies and phases for 6 octaves of noise
        self.octaves = []
        # We want very slow moving clouds (low freq) and some fast details
        # f=0.0005 means a full cycle takes 2000 seconds (about 33 minutes)
        base_freq = random.uniform(0.0001, 0.0005)
        for i in range(6):
            freq = base_freq * (1.8 ** i) 
            phase = random.uniform(0, 2 * math.pi)
            amplitude = 1.0 / (1.5 ** i)
            self.octaves.append((freq, phase, amplitude))
            
    def get_value(self, t_sec):
        val = 0
        max_amp = 0
        for freq, phase, amp in self.octaves:
            val += math.sin(t_sec * freq + phase) * amp
            max_amp += amp
            
        # val is roughly between -max_amp and +max_amp. Normalize to -1 to 1.
        val = val / max_amp
        
        # We treat val > 0.2 as a cloud. The higher val is, the thicker the cloud.
        # This gives a nice organic thresholded look (clear skies most of the time, then varied cloud banks)
        cloud_threshold = 0.1
        if val > cloud_threshold:
            # Map [cloud_threshold, 1.0] to [0.0, 1.0] (cloud intensity)
            cloud_intensity = (val - cloud_threshold) / (1.0 - cloud_threshold)
            
            # The thicker the cloud, the lower the multiplier drops (down to 15% power)
            # Power drop isn't strictly linear in reality, but this works well
            multiplier = 1.0 - cloud_intensity * 0.85
            
            # Inside a cloud, solar irradiance gets extra jagged and noisy
            # We simulate this with extra high-frequency noise
            jaggedness = random.uniform(0.9, 1.1)
            multiplier *= jaggedness
            
            return max(0.1, min(1.0, multiplier))
        else:
            # Clear sky, multiplier is 1.0
            return 1.0

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
        return
        
    # Find "clear sky" rows to use as a base for generation (avoiding the huge dips in original data)
    max_pin = max(r.base_pin for r in rows)
    clear_sky_rows = [r for r in rows if r.base_pin > max_pin * 0.85]
    if len(clear_sky_rows) < 100:
        clear_sky_rows = rows # fallback
        
    start_dt = rows[0].dt
    end_dt = rows[-1].dt
    t_start = rows[0].t
    t_end = rows[-1].t
    N = len(rows)
    dt_avg = (t_end - t_start) / (N - 1)
    
    # 1. Calculate offset
    target_start = datetime(start_dt.year, start_dt.month, start_dt.day, 7, 0, 0)
    curr_dt_test = start_dt - timedelta(seconds=dt_avg)
    curr_t_test = t_start - dt_avg
    while curr_dt_test >= target_start:
        curr_dt_test -= timedelta(seconds=dt_avg)
        curr_t_test -= dt_avg
    t_offset = abs(curr_t_test) if curr_t_test < 0 else 0

    cloud_sim = FractalNoiseCloud()

    # Generate backwards
    synthetic_before = []
    idx = random.randint(0, len(clear_sky_rows)-1)
    
    curr_dt = start_dt - timedelta(seconds=dt_avg)
    curr_t = t_start - dt_avg
    
    while curr_dt >= target_start:
        idx = (idx + random.choice([-1, 0, 1])) % len(clear_sky_rows)
        row = clear_sky_rows[idx]
        cf = cloud_sim.get_value(curr_t)
        
        synthetic_before.append(row.generate_organic_string(curr_dt, curr_t, cf, t_offset))
        curr_dt -= timedelta(seconds=dt_avg)
        curr_t -= dt_avg
        
    synthetic_before.reverse()
    
    # Original data
    original_strings = [r.get_original_string_with_offset(t_offset) for r in rows]
    
    # Generate forwards
    synthetic_after = []
    idx = random.randint(0, len(clear_sky_rows)-1)
    curr_dt = end_dt + timedelta(seconds=dt_avg)
    curr_t = t_end + dt_avg
    target_end = datetime(end_dt.year, end_dt.month, end_dt.day, 15, 0, 0)
    
    while curr_dt <= target_end:
        idx = (idx + random.choice([-1, 0, 1])) % len(clear_sky_rows)
        row = clear_sky_rows[idx]
        cf = cloud_sim.get_value(curr_t)
        
        synthetic_after.append(row.generate_organic_string(curr_dt, curr_t, cf, t_offset))
        curr_dt += timedelta(seconds=dt_avg)
        curr_t += dt_avg
        
    with open(output_file, 'w') as out:
        out.writelines(synthetic_before)
        out.writelines(original_strings)
        out.writelines(synthetic_after)
        
    print("Fractal organic data generated.")

if __name__ == "__main__":
    process()
