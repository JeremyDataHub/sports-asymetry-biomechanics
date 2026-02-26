# Sports Movement Asymmetry Analysis

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Qualisys](https://img.shields.io/badge/Qualisys-motion_capture-green.svg)](https://www.qualisys.com/)
[![OpenSim](https://img.shields.io/badge/OpenSim-biomechanics-purple.svg)](https://opensim.stanford.edu/)
[![SciPy](https://img.shields.io/badge/SciPy-signal_processing-orange.svg)](https://scipy.org/)

> Complete pipeline for assessing bilateral movement asymmetries using motion capture, inverse kinematics, and custom data processing. Demonstrates practical workflow from capture to biomechanical interpretation.

## Visualization

### Capture → Kinematics Workflow

<img src="visualization/qualisys_capture.gif" width="48%" alt="Qualisys motion capture"/> 
<img src="visualization/opensim_kinematics.gif" width="48%" alt="OpenSim inverse kinematics"/>

*Left: Raw 3D marker trajectories (Qualisys). Right: Computed joint angles (OpenSim).*

## Results

### Range of Motion Across Movements

![ROM Vertical Jumps](results/ROM_SJ.png)
*Example: ROM during vertical jumps. Complete ROM analysis for all conditions (SJ, CMJ, walking, running at 2 speeds, cycling at 2 cadences) in `results/` folder.*

### Asymmetry Index Instability & Solution

![Asymmetry Index Problem](results/asymetry_index.png)
*Left: Relative Asymmetry Index (SI) shows mathematical instability in cyclic movements, oscillating between -75% and +100%.*

![Normalized Symmetry Index Solution](results/NSI_comparison.png)
*Right: Normalized Symmetry Index (NSI) stabilizes values to -60% to +60%, enabling reliable cycle-by-cycle analysis.*

### Bilateral Synchronization

**Cross-correlation analysis (knee angles):**
- **r = 0.957** — strong bilateral similarity
- **lag = 0 frames** — perfect temporal alignment

Indicates excellent bilateral coordination despite small amplitude asymmetries.

## Pipeline

```
16 Qualisys cameras (120 Hz)
        │
        ▼
Qualisys Track Manager
 ├── Manual marker labeling (trial 1)
 ├── Automatic template labeling (trials 2-37)
 ├── Interpolation (missing markers)
 └── Export to .c3d format
        │
        ▼
c3d_to_trc.py
 ├── 3D coordinate extraction
 ├── Reference frame transformation
 ├── Missing marker handling
 └── .trc output
        │
        ▼
OpenSim
 ├── Model scaling
 ├── Inverse kinematics
 ├── Joint angle computation
 └── Inverse dynamics
        │
        ▼
c3d_to_mot.py
 ├── Force plate extraction
 ├── Butterworth filtering (6 Hz)
 ├── Unit conversion (N·mm → N·m)
 └── GRF XML generation
        │
        ▼
Asymmetry Analysis
 ├── ROM computation
 ├── Asymmetry Index (SI, NSI)
 └── Cross-correlation
```

## Scripts

### `c3d_to_trc.py` — Qualisys to OpenSim Conversion

Converts .c3d → .trc format with reference frame transformation. Handles missing markers via interpolation and batch processes all trials.

**Usage:**
```bash
python c3d_to_trc.py --batch 1 37
python c3d_to_trc.py --input trial0001 --output trial0001_fixed.trc
```

### `c3d_to_mot.py` — Force Plate Data Extraction

Extracts GRF data from .c3d files with 4th-order Butterworth filtering (6 Hz). Converts moments N·mm → N·m and generates OpenSim-compatible XML.

**Usage:**
```bash
python c3d_to_mot.py --batch 1 37
python c3d_to_mot.py --input trial0001 --output trial0001_GRF.xml
```

Both scripts include professional logging, type hints, complete docstrings, CLI arguments, and robust error handling.

## Tech Stack

| Category | Tools |
|----------|-------|
| Motion Capture | Qualisys (16 cameras, optoelectronic) |
| Preprocessing | Python 3.12 + ezc3d + scipy |
| Biomechanics | OpenSim (scaling, IK, inverse dynamics) |
| Force Analysis | AMTI + Kistler force plates (1000 Hz) |
| Visualization | Matplotlib, Qualisys Track Manager |

## Limitations

- Single subject proof-of-concept (small sample size)
- No ground-truth validation against marker-based gold standard
- SI metric unsuitable for cyclic analysis (mathematical singularities)
- Force plate analysis not extensively explored in this analysis

## Installation & Setup

Requirements:
1. **Qualisys Track Manager** (commercial software)
2. **OpenSim** (free, open-source)
3. Python dependencies:
```bash
pip install -r requirements.txt
```

## Academic Reference

> Birba, J., Giot, B., Le Gall, M. (2024). Emerging technologies and methods for assessing asymmetry during sports movements. Master 2, Digital Sciences and Sports (EUR Digisport), Rennes 2 University.

## Technical Note

Motion capture data processed using M2S Laboratory musculoskeletal model (Rennes 2 University). Model files proprietary to M2S Lab. Full implementation code available for preprocessing pipeline; Qualisys Track Manager and OpenSim required for reproduction.

*Jérémy Birba — [LinkedIn](https://linkedin.com/in/birba-jeremy) | [GitHub](https://github.com/JeremyDataHub)*
