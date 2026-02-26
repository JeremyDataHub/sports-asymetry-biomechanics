"""
Convert Qualisys .c3d motion capture files to OpenSim-compatible .trc format.

This module handles the complete preprocessing pipeline:
1. Load 3D marker trajectories from .c3d files (Qualisys Track Manager output)
2. Apply reference frame transformation (capture → OpenSim coordinates)
3. Export to .trc format with proper header structure
4. Batch process multiple trials with error handling

Usage:
    python c3d_to_trc_transformed.py --input trial0001 --output trial0001_fixed.trc
    python c3d_to_trc_transformed.py --batch 1 38  # Process trials 1-37
"""

import numpy as np
import ezc3d
import argparse
import logging
from pathlib import Path
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def transfo_cap_to_opensim(q1: float, q2: float, q3: float) -> np.ndarray:
    """
    Compute rotation matrix for reference frame transformation.
    
    Transforms from Qualisys capture coordinate system to OpenSim reference frame
    using Euler angles (XYZ convention).
    
    Args:
        q1 (float): Rotation angle around X-axis (degrees)
        q2 (float): Rotation angle around Y-axis (degrees)
        q3 (float): Rotation angle around Z-axis (degrees)
    
    Returns:
        np.ndarray: 3x3 rotation matrix
        
    Notes:
        For this project, empirically determined transformation is:
        q1 = -90°, q2 = 0°, q3 = 0° (90° rotation around X-axis)
    """
    # Convert degrees to radians
    q1_rad, q2_rad, q3_rad = np.deg2rad([q1, q2, q3])
    
    # Individual rotation matrices
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(q1_rad), -np.sin(q1_rad)],
        [0, np.sin(q1_rad), np.cos(q1_rad)]
    ])
    
    Ry = np.array([
        [np.cos(q2_rad), 0, np.sin(q2_rad)],
        [0, 1, 0],
        [-np.sin(q2_rad), 0, np.cos(q2_rad)]
    ])
    
    Rz = np.array([
        [np.cos(q3_rad), -np.sin(q3_rad), 0],
        [np.sin(q3_rad), np.cos(q3_rad), 0],
        [0, 0, 1]
    ])
    
    return Rx @ Ry @ Rz


def c3d_to_trc(filename: str, q1: float, q2: float, q3: float, 
               output_file: str) -> bool:
    """
    Convert Qualisys .c3d file to OpenSim-compatible .trc format.
    
    Args:
        filename (str): Input .c3d file path (without extension)
        q1, q2, q3 (float): Rotation angles (degrees) for frame transformation
        output_file (str): Output .trc file path
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        FileNotFoundError: If input .c3d file doesn't exist
        ValueError: If marker data is corrupted or incomplete
    """
    try:
        input_path = Path(f"{filename}.c3d")
        
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return False
            
        logger.info(f"Reading: {input_path}")
        c3d = ezc3d.c3d(str(input_path))
        
        # Extract metadata
        points = c3d['data']['points']
        markers_names = c3d['parameters']['POINT']['LABELS']['value']
        frame_rate = c3d['parameters']['POINT']['RATE']['value'][0]
        
        n_frames = points.shape[2]
        n_markers = len(markers_names)
        
        logger.info(f"Found {n_markers} markers, {n_frames} frames @ {frame_rate} Hz")
        
        # Get transformation matrix
        R = transfo_cap_to_opensim(q1, q2, q3)
        
        # Create time vector
        time = np.arange(n_frames) / frame_rate
        
        # Write TRC file
        with open(output_file, 'w') as f:
            # Header line 1
            f.write(f"PathFileType\t4\t(X/Y/Z)\t{output_file}\n")
            
            # Header line 2
            f.write("DataRate\tCameraRate\tNumFrames\tNumMarkers\tUnits\t"
                   "OrigDataRate\tOrigDataStartFrame\tOrigNumFrames\n")
            
            # Header line 3
            f.write(f"{frame_rate:.2f}\t{frame_rate:.2f}\t{n_frames}\t{n_markers}\t"
                   f"mm\t{frame_rate:.2f}\t1\t{n_frames}\n")
            
            # Marker names header
            f.write("Frame#\tTime")
            for name in markers_names:
                f.write(f"\t{name}\t\t")
            f.write("\n")
            
            # Coordinate labels
            f.write("\t\t")
            for i in range(n_markers):
                f.write(f"X{i+1}\tY{i+1}\tZ{i+1}\t")
            f.write("\n")
            
            # Data rows
            for frame_idx in range(n_frames):
                f.write(f"{frame_idx+1}\t{time[frame_idx]:.3f}")
                
                for marker_idx in range(n_markers):
                    pos = points[:3, marker_idx, frame_idx]
                    
                    # Handle missing markers
                    if not np.any(np.isnan(pos)):
                        transformed_pos = R @ pos
                        x, y, z = transformed_pos
                    else:
                        x, y, z = 0, 0, 0
                    
                    f.write(f"\t{x:.6f}\t{y:.6f}\t{z:.6f}")
                
                f.write("\n")
        
        logger.info(f"Successfully wrote: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        return False


def batch_process(start_trial: int, end_trial: int, 
                 rotation_angles: Tuple[float, float, float] = (-90, 0, 0)) -> None:
    """
    Batch process multiple trials.
    
    Args:
        start_trial (int): First trial number (1-indexed)
        end_trial (int): Last trial number (inclusive)
        rotation_angles (Tuple[float, float, float]): (q1, q2, q3) in degrees
    """
    q1, q2, q3 = rotation_angles
    successful = 0
    failed = 0
    
    logger.info(f"Starting batch processing: trials {start_trial} to {end_trial}")
    
    for trial_num in range(start_trial, end_trial + 1):
        trial_str = str(trial_num).zfill(4)
        input_file = f'trial{trial_str}'
        output_file = f'trial{trial_str}_fixed.trc'
        
        logger.info(f"Processing trial {trial_str} ({trial_num - start_trial + 1}/"
                   f"{end_trial - start_trial + 1})")
        
        if c3d_to_trc(input_file, q1, q2, q3, output_file):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"Batch complete: {successful} successful, {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Qualisys .c3d files to OpenSim-compatible .trc format"
    )
    
    parser.add_argument('--input', type=str, help='Input .c3d file (without extension)')
    parser.add_argument('--output', type=str, help='Output .trc file')
    parser.add_argument('--batch', type=int, nargs=2, metavar=('START', 'END'),
                       help='Batch process trials START to END (inclusive)')
    parser.add_argument('--q1', type=float, default=-90, help='Rotation X (degrees)')
    parser.add_argument('--q2', type=float, default=0, help='Rotation Y (degrees)')
    parser.add_argument('--q3', type=float, default=0, help='Rotation Z (degrees)')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_process(args.batch[0], args.batch[1], (args.q1, args.q2, args.q3))
    elif args.input and args.output:
        c3d_to_trc(args.input, args.q1, args.q2, args.q3, args.output)
    else:
        parser.print_help()