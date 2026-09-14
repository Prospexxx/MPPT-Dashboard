# Standalone MPPT System Based on Hybrid WODE Algorithm & Real-Time Monitoring Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt: 6](https://img.shields.io/badge/GUI-PyQt6%20%26%20PyQtGraph-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![MCU: STM32F407](https://img.shields.io/badge/MCU-STM32F407VGT%20(ARM%20Cortex--M4)-red.svg)](https://www.st.com/en/microcontrollers-microprocessors/stm32f407vg.html)
[![Patent: DJKI](https://img.shields.io/badge/Patent-DJKI%20Indonesia%20(2026)-purple.svg)](https://dgip.go.id)
[![Copyright: HAKI](https://img.shields.io/badge/Copyright-HAKI%20Kemenkumham%20RI-orange.svg)](https://dgip.go.id)

> **Undergraduate Thesis (Tugas Akhir) — Final Project**  
> **Author:** Mustaqim Nurul Huda, S.Tr.T.  
> **Department:** Industrial Electrical Engineering (D4 Teknik Elektro Industri)  
> **Institution:** Politeknik Elektronika Negeri Surabaya (PENS), Indonesia  
> **Live Portfolio & Resume:** [https://prospexxx.github.io/MPPT-Dashboard/](https://prospexxx.github.io/MPPT-Dashboard/)

---

## 📌 Executive Summary

Under **Partial Shading Conditions (PSC)**, photovoltaic (PV) arrays exhibit non-linear power-voltage (P-V) characteristics with multiple local power peaks alongside one Global Maximum Power Point (GMPP). Conventional algorithms like Perturb & Observe (P&O) become trapped in local maxima, causing severe power losses (up to 70%) and erratic stalling in solar-powered DC submersible pumps.

This project delivers a complete hardware-firmware-software solution:
1. **Power Electronics:** A custom 50 kHz **Modified Ćuk DC-DC Converter** designed on a 2-layer PCB (EAGLE) with continuous input/output currents and isolated sensing (AMC1100, ACS712, FOD3182 gate drivers).
2. **Embedded Firmware:** A hybrid **Whale Optimization Algorithm & Differential Evolution (CTM-WODE)** running deterministically on an **STM32F407VGT** (ARM Cortex-M4 @ 168 MHz) with dynamic slew-rate limiting (2.5% step) and per-duty power averaging.
3. **Desktop Telemetry GUI:** A real-time **Python (PyQt6 + PyQtGraph)** monitoring dashboard communicating over two-way UART at 115200 baud with auto-split data logging.

---

## 📊 Experimental Results (86,790 Samples Validated)

| MPPT Algorithm | Category | Avg. Efficiency | Convergence Speed | Steady-State Ripple | GMPP Success Rate |
|---|---|---|---|---|---|
| **Hybrid WODE (Proposed)** | **Hybrid Metaheuristic** | **98.53%** | **3.67 s** | **2.28 W** | **100.0%** |
| Whale Optimization (WOA) | Metaheuristic | 96.12% | 6.14 s | 4.10 W | 95.0% |
| Differential Evolution (DE) | Evolutionary | 95.80% | 5.82 s | 3.85 W | 92.5% |
| Perturb & Observe (P&O) | Conventional Benchmark | 68.45% | 1.95 s (Local Peak) | 7.82 W | 32.0% (Trapped) |

---

## ⚡ System Architecture

```
[ PV Panel Array ] (Multi-pattern partial shading)
        │
        ▼ (Vin, Iin)
[ Modified Ćuk DC-DC Converter ] ──(PWM @ 50 kHz)── [ STM32F407VGT MCU ]
        │                                                    │
        ▼ (Vout, Iout)                                       ▼ (UART @ 115200)
[ DC Submersible Water Pump ]                       [ PyQt6 Desktop GUI ]
                                                             │
                                                             ├── Real-Time Plots
                                                             ├── 2-Way Mode Control
                                                             └── Auto-Split Logging
```

---

## 📁 Repository Structure

```
.
├── index.html                     # Live Web Portfolio & Resume (GitHub Pages)
├── portfolio.html                 # Complete Technical Portfolio Web Application
├── assets/                        # High-res diagrams, PCB schematics, certificates, PDFs
│   ├── Resume_Mustaqim_Nurul_Huda.pdf
│   ├── Technical_Portfolio_Mustaqim_Nurul_Huda.pdf
│   ├── extracted_img_p1_1.png     # Modified Ćuk Converter PCB layout (EAGLE)
│   ├── extracted_img_p2_1.png     # 3D Enclosure Render (Fusion 360)
│   ├── extracted_img_p2_2.png     # 2D Production Drawing (245.16 × 170 mm)
│   ├── extracted_img_p3_1.jpeg    # PKM-KC National Grant Award Certificate
│   ├── extracted_img_p3_2.jpeg    # Copyright Certificate (HAKI EC00202499819)
│   └── extracted_img_p4_1.png     # Internship Certificate (PT Eratex Djaja Tbk)
├── dashboard_ta.py                # Main PyQt6 Desktop Monitoring Application
├── karakteristik_i-v.py           # Experimental I-V curve plotting script
├── karakteristik_p-v.py           # Experimental P-V curve plotting script
├── ploting mppt dan duty.py       # Tracking efficiency and steady-state calculator
├── STM32_Firmware/                # Complete STM32CubeIDE C/C++ Project
│   ├── Core/Src/
│   │   ├── main.c                 # ADC-DMA sampling, TIM9 ISR, UART state machine
│   │   ├── mppt_algo.c            # Hybrid WODE, WOA, DE, P&O implementations
│   │   └── i2c_lcd.c              # Adaptive 16x2 LCD display driver
│   ├── Core/Inc/                  # Header files (mppt_algo.h, i2c_lcd.h)
│   ├── Drivers/                   # STM32 HAL & CMSIS libraries
│   ├── CMakeLists.txt             # CMake configuration
│   └── Program_TA.ioc             # STM32CubeMX hardware configuration
└── Data_Logger/                   # Over 100+ experimental test datasets & plots
```

---

## 🚀 Quick Start Guide

### 1. Python Dashboard (PC)

```bash
# Clone the repository
git clone https://github.com/Prospexxx/MPPT-Dashboard.git
cd MPPT-Dashboard

# Create virtual environment & install requirements
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install PyQt6 pyqtgraph pyserial numpy pandas matplotlib

# Run the real-time monitoring dashboard
python dashboard_ta.py
```

### 2. STM32 Firmware (Hardware)

1. Open **STM32CubeIDE** (v1.14+).
2. Import project from `STM32_Firmware/`.
3. Target device: `STM32F407VGTx` (ARM Cortex-M4 @ 168 MHz).
4. Build using `Release` configuration and flash via **ST-Link v2 / v3**.

---

## 📜 Intellectual Property & Publications

- **Simple Patent (DJKI Indonesia - 2026):**  
  *Solar Panel Maximum Power Point Tracking (MPPT) System Based on WODE Algorithm for Submersible Water Pump Control*
- **Copyright (HAKI Kemenkumham RI):**  
  *Real-Time MPPT Python PyQt6 Dashboard Monitoring Software*
- **Copyright (HAKI Kemenkumham RI - No. EC00202499819):**  
  *EcoMow Technical Manual & Mechanical Design*
- **Journal Paper (Submitted):**  
  *Indonesian Journal of Science & Technology (IJOST)*

---

## 👤 Author & Contact

**Mustaqim Nurul Huda, S.Tr.T.**  
- 🎓 Politeknik Elektronika Negeri Surabaya (PENS)  
- 📧 [mustaqimnurulhuda14@gmail.com](mailto:mustaqimnurulhuda14@gmail.com)  
- 💬 [WhatsApp (+62 851-7226-3476)](https://wa.me/6285172263476)  
- 🔗 [LinkedIn](https://linkedin.com/in/huda14) · [GitHub](https://github.com/Prospexxx) · [Linktree](https://linktr.ee/akunhudayangasli)
