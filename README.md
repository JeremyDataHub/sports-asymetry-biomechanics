# Sports Movement Asymmetry Analysis

Biomechanical assessment of bilateral asymmetries across 5 movement types using 
motion capture, inverse kinematics, and custom data processing pipelines.

**Status:** Master's research project (2024-2025)  
**Subject:** 1 competitive handball player | **Trials:** 37  
**Result:** Cross-correlation r = 0.957 (bilateral knee angle symmetry)

## Visualization

### Motion Capture → Kinematics Pipeline

<img src="visualization/qualisys_capture.gif" width="48%" alt="Qualisys motion capture"/> 
<img src="visualization/opensim_kinematics.gif" width="48%" alt="OpenSim inverse kinematics"/>

*Left: Raw 3D marker trajectories (Qualisys Track Manager). Right: Computed joint angles (OpenSim inverse kinematics).*

---

## Overview

This project investigates functional and biomechanical asymmetries in sports movements 
using a complete motion capture → analysis pipeline:
```
Raw motion capture (.c3d)
    ↓
[Python preprocessing]
    ↓
3D marker trajectories (.trc)
    ↓
[OpenSim inverse kinematics]
    ↓
3D joint angles + inverse dynamics
    ↓
Asymmetry analysis (ROM, SI, NSI, cross-correlation)
```

**Movements studied:**
- Vertical jumps (SJ, CMJ)
- Walking
- Running (2 speeds: moderate, fast)
- Cycling (2 cadences: moderate, fast)

---

## Key Technical Contributions

### 1. Qualisys ↔ OpenSim Data Pipeline

**Problem:** .c3d files require extensive manual preprocessing before OpenSim compatibility.

**Solution:** Two automated Python scripts handle the complete workflow:

**`c3d_to_trc_transformed.py`** (95 lines)
- Converts Qualisys .c3d → OpenSim-compatible .trc format
- Applies rotation matrix transformation (reference frame alignment)
- Batch processes 37 trials automatically
- Resolves Y-Z axis swap between capture and OpenSim coordinate systems

**`c3d_en_mot.py`** (157 lines)
- Extracts force plate data from .c3d files
- 4th-order Butterworth low-pass filtering (6 Hz cutoff)
- Converts moments from N·mm → N·m
- Generates OpenSim-compatible GRF XML files

**Impact:** 10x faster than manual preprocessing + reproducible, version-controlled workflows

### 2. Asymmetry Analysis Methods

Compared 4 approaches to quantify left-right differences:

| Method | When to use | Strength | Weakness |
|--------|-----------|----------|----------|
| **ROM** | Quick assessment | Simple interpretation | No temporal detail |
| **Asymmetry Index (SI)** | Static movements | Standard metric | Unstable with small denominators |
| **Normalized SI (NSI)** | Cyclic movements | Controlled range | Still somewhat arbitrary |
| **Cross-correlation** | Cycle similarity | Holistic view + temporal alignment | Misses specific phase asymmetries |

**Finding:** For cyclic movements (running, cycling), cross-correlation (r = 0.957) 
was most reliable. SI generated spurious values due to mathematical instability when right ≈ left.

---

## Results

### Range of Motion Across Movements

![ROM Squat Jump](results/ROMS_SJ.png)
*Example: Range of motion during vertical jumps. Complete ROM analysis for all movement 
conditions (SJ, CMJ, walking, running at 2 speeds, cycling at 2 cadences) available 
in the `results/` folder.*

### Asymmetry Index Analysis

![Asymmetry Index Comparison](results/asymetry_index.png)
*Relative Asymmetry Index (SI) for knee angle during cycling (Trial 28). Shows numerical 
instability in cyclic movements, with values oscillating between -75% and +100%.*

### Normalized Symmetry Index

![Normalized Symmetry Index](results/NSI_comparison.png)
*NSI stabilizes the SI values to a reasonable range (-60% to +60%), enabling reliable 
cycle-by-cycle comparison. The three panels show: (top) raw knee angles, (middle) 
normalized angles, (bottom) computed NSI.*

### Bilateral Synchronization

**Cross-correlation analysis of knee angles:**
- **Correlation coefficient:** r = 0.957 (strong bilateral similarity)
- **Temporal lag:** 0 frames (perfect synchronization)

This indicates excellent bilateral coordination with synchronized movement patterns 
despite small amplitude asymmetries in specific joints.

---

## Technical Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| **Motion Capture** | Qualisys (16 cameras, optoelectronic) | 3D marker trajectories |
| **Data Processing** | Python 3.12 + ezc3d + scipy | .c3d conversion, filtering |
| **Biomechanics** | OpenSim | Scaling, IK, inverse dynamics |
| **Force Analysis** | AMTI + Kistler force plates | Ground reaction forces |
| **Visualization** | Matplotlib, Qualisys Track Manager | Results & diagnostics |

---

## Methodology

### Capture Protocol

- **Subject:** Competitive handball player, 80 kg, male
- **Marker set:** 49 full-body markers (M2S Lab model) + 5 custom markers
- **Frame rate:** 120 Hz (motion capture), 1000 Hz (force plates)
- **Trials:** 37 validated captures (2 rejected due to marker loss)

### Data Processing Pipeline

1. **Qualisys Track Manager (QTM)**
   - Manual marker labeling on first trial
   - Automatic template-based labeling for subsequent trials
   - Polynomial + relational interpolation for missing markers
   - Export to .c3d format

2. **Python Preprocessing** (custom scripts)
   - Extract 3D marker coordinates from .c3d
   - Apply calibration-based rotation matrix
   - Generate OpenSim-compatible .trc files
   - Extract force plate data → GRF XML files

3. **OpenSim Analysis**
   - Scale musculoskeletal model to subject anthropometry
   - Inverse kinematics: markers → 3D joint angles
   - Inverse dynamics: angles + GRF → joint torques

### Asymmetry Quantification

**Metrics used:**
- **ROM (Range of Motion):** Peak flexion differences between left and right joints
- **Asymmetry Index (SI):** SI% = [(R-L)/(R+L)/2] × 100
- **Normalized SI (NSI):** Stabilized version for cyclic data
- **Cross-correlation:** Cycle-to-cycle similarity + phase lag detection

---

## Files

**Scripts:**
- `c3d_to_trc_transformed.py` — Qualisys .c3d to OpenSim .trc conversion
- `c3d_en_mot.py` — Force plate data extraction and GRF generation

**Visualizations:**
- `results/` — Publication-quality ROM and asymmetry analysis figures
- `visualization/` — GIFs showing capture to kinematics pipeline

---

## Key Insights

1. **ROM alone is insufficient for cyclic movements.** Temporal information is critical for understanding asymmetry evolution across movement phases.

2. **SI generates spurious values in cyclic analysis** when denominators approach zero (classic numerical instability). NSI partially addresses this but remains somewhat arbitrary.

3. **Cross-correlation is most robust** for assessing bilateral coordination in cyclic movements. The r = 0.957 result indicates excellent bilateral symmetry in this athlete.

4. **Custom preprocessing is essential.** Qualisys → OpenSim conversion is non-trivial and benefits from automated, version-controlled scripts.

---

## Technical Note

Motion capture data was processed using the M2S Laboratory's musculoskeletal model 
(Université Rennes 2). Visualizations are from OpenSim analyses conducted during 
this Master's project. Model files are proprietary to the M2S Lab and not included 
in this repository.

---

## Project Context

This was a Master 2 coursework project (2024-2025) investigating emerging technologies 
for asymmetry assessment in sports. While academic in scope, it demonstrates:

- ✅ Complete motion capture workflow (capture → analysis → interpretation)
- ✅ Technical problem-solving (Python pipelines for real bottlenecks)
- ✅ Biomechanical expertise (protocol design, metric selection, interpretation)
- ✅ Scientific rigor (method comparison, limitations discussion, reproducibility)

**Code quality note:** These are research scripts (not production software). For 
deployment, they would require unit tests, error handling improvements, and validation 
against reference systems.

---

## Author

**Jérémy Birba**  
Master 2 Digital Sciences and Sports | EUR Digisport, Université Rennes 2

[LinkedIn](https://linkedin.com/in/birba-jeremy) | 
[GitHub](https://github.com/JeremyDataHub)

---

*This project demonstrates the intersection of data science, signal processing, 
and biomechanical expertise — combining technical depth with domain knowledge 
to solve real research questions.*
