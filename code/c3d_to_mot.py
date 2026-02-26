"""
Extract force plate data from Qualisys .c3d files and generate OpenSim-compatible outputs.

This module processes ground reaction force (GRF) data:
1. Load analog data from .c3d files (force plates)
2. Apply low-pass Butterworth filtering
3. Convert units (N·mm → N·m for moments)
4. Generate OpenSim-compatible XML format

Usage:
    python c3d_en_mot.py --input trial0001 --output trial0001_GRF.xml --ik-file IKResults_trial0001.mot
    python c3d_en_mot.py --batch 1 38 --cutoff 6.0  # Process trials 1-37
"""

import numpy as np
import ezc3d
import xml.etree.ElementTree as ET
import argparse
import logging
from pathlib import Path
from scipy import signal
from typing import Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def butterworth_filter(data: np.ndarray, cutoff_freq: float, sample_rate: float, 
                       order: int = 4) -> np.ndarray:
    """
    Apply low-pass Butterworth filter to force plate data.
    
    Args:
        data (np.ndarray): Input signal (shape: n_channels × n_samples)
        cutoff_freq (float): Cutoff frequency (Hz)
        sample_rate (float): Sampling rate (Hz)
        order (int): Filter order (default: 4)
        
    Returns:
        np.ndarray: Filtered signal
        
    Notes:
        Uses zero-phase filtering (filtfilt) to avoid phase distortion.
    """
    if data.shape[1] < 15:
        logger.warning(f"Insufficient data points for filtering (n={data.shape[1]}). "
                      "Returning unfiltered data.")
        return data
    
    nyquist = sample_rate * 0.5
    normalized_cutoff = cutoff_freq / nyquist
    
    if normalized_cutoff >= 1.0:
        logger.warning(f"Cutoff frequency ({cutoff_freq} Hz) >= Nyquist ({nyquist} Hz). "
                      "Skipping filter.")
        return data
    
    b, a = signal.butter(order, normalized_cutoff, btype='low')
    return signal.filtfilt(b, a, data, axis=1)


def extract_force_data(filename: str, cutoff_freq: float = 6.0, 
                       n_plates: int = 2) -> Tuple[List[np.ndarray], float]:
    """
    Extract and process force plate data from .c3d file.
    
    Args:
        filename (str): Input .c3d file path (without extension)
        cutoff_freq (float): Low-pass filter cutoff (Hz), default 6 Hz
        n_plates (int): Number of force plates, default 2
        
    Returns:
        Tuple[List[np.ndarray], float]: (processed_data, sample_rate)
        
    Raises:
        FileNotFoundError: If input .c3d file doesn't exist
        ValueError: If force plate data is corrupted
    """
    try:
        input_path = Path(f"{filename}.c3d")
        
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            raise FileNotFoundError(f"{input_path}")
        
        logger.info(f"Reading: {input_path}")
        c3d = ezc3d.c3d(str(input_path))
        
        # Extract metadata
        force_data = c3d['data']['analogs']
        sample_rate = c3d['parameters']['POINT']['RATE']['value'][0]
        
        logger.info(f"Sample rate: {sample_rate} Hz")
        
        processed_data = []
        
        for plate_idx in range(n_plates):
            logger.info(f"Processing force plate {plate_idx + 1}/{n_plates}")
            
            # Extract 6 DOF (Fx, Fy, Fz, Mx, My, Mz)
            start_idx = plate_idx * 6
            end_idx = start_idx + 6
            
            forces = force_data[0][start_idx:end_idx].copy()
            
            # Convert moments from N·mm to N·m
            forces[3:6] = forces[3:6] / 1000.0
            
            # Apply low-pass filter
            forces = butterworth_filter(forces, cutoff_freq, sample_rate)
            
            processed_data.append(forces)
        
        logger.info(f"Successfully extracted force data from {n_plates} plates")
        return processed_data, sample_rate
        
    except Exception as e:
        logger.error(f"Error extracting force data from {filename}: {str(e)}")
        raise


def write_opensim_grf_xml(filename: str, processed_data: List[np.ndarray], 
                         sample_rate: float, output_xml: str, ik_file: str) -> bool:
    """
    Write OpenSim-compatible external loads XML file.
    
    Args:
        filename (str): Original .c3d filename (for reference)
        processed_data (List[np.ndarray]): Processed force plate data
        sample_rate (float): Sampling rate (Hz)
        output_xml (str): Output XML file path
        ik_file (str): IK results file path (for reference in OpenSim)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Writing OpenSim XML: {output_xml}")
        
        # Create root element
        root = ET.Element("OpenSimDocument", Version="40000")
        external_loads = ET.SubElement(root, "ExternalLoads", 
                                      name=f"{filename}_ExternalLoads")
        
        # Add file references
        ET.SubElement(external_loads, "datafile").text = output_xml.replace('.xml', '_data.xml')
        ET.SubElement(external_loads, "external_loads_model_kinematics_file").text = ik_file
        ET.SubElement(external_loads, "lowpass_cutoff_frequency_for_load_kinematics").text = "-1"
        
        # Add external force definitions
        objects = ET.SubElement(external_loads, "objects")
        
        for plate_idx in range(len(processed_data)):
            ext_force = ET.SubElement(objects, "ExternalForce")
            foot = "foot_r" if plate_idx == 0 else "foot_l"
            
            ET.SubElement(ext_force, "applied_to_body").text = foot
            ET.SubElement(ext_force, "force_expressed_in_body").text = "ground"
            ET.SubElement(ext_force, "point_expressed_in_body").text = "ground"
            ET.SubElement(ext_force, "force_identifier").text = f"ground_force_vx_{plate_idx + 1}"
            ET.SubElement(ext_force, "point_identifier").text = f"ground_force_px_{plate_idx + 1}"
            ET.SubElement(ext_force, "torque_identifier").text = f"ground_torque_x_{plate_idx + 1}"
        
        # Add empty groups element
        ET.SubElement(external_loads, "groups")
        ET.SubElement(root, "MiscModelComponents")
        
        # Write XML file
        tree = ET.ElementTree(root)
        tree.write(output_xml, encoding="utf-8", xml_declaration=True)
        
        logger.info("External loads XML generated successfully")
        
        # Also generate data file
        _write_grf_data_xml(processed_data, sample_rate, 
                           output_xml.replace('.xml', '_data.xml'))
        
        return True
        
    except Exception as e:
        logger.error(f"Error writing XML: {str(e)}")
        return False


def _write_grf_data_xml(processed_data: List[np.ndarray], sample_rate: float, 
                        output_file: str) -> None:
    """
    Generate GRF data in OpenSim-compatible XML format.
    
    Internal helper function for OpenSim format compliance.
    """
    logger.info(f"Writing GRF data: {output_file}")
    
    time = np.arange(processed_data[0].shape[1]) / sample_rate
    
    root = ET.Element("OpenSimDocument", Version="40000")
    table = ET.SubElement(root, "DataTable")
    
    # Column labels
    col_labels = ET.SubElement(table, "ColumnLabels")
    col_labels_list = ['time']
    
    for plate_idx in range(len(processed_data)):
        for axis in ['x', 'y', 'z']:
            col_labels_list.append(f"ground_force_v{axis}_{plate_idx + 1}")
    
    for plate_idx in range(len(processed_data)):
        for axis in ['x', 'y', 'z']:
            col_labels_list.append(f"ground_force_p{axis}_{plate_idx + 1}")
    
    for plate_idx in range(len(processed_data)):
        for axis in ['x', 'y', 'z']:
            col_labels_list.append(f"ground_torque_{axis}_{plate_idx + 1}")
    
    for label in col_labels_list:
        ET.SubElement(col_labels, "Label").text = label
    
    # Data rows
    for frame_idx, t in enumerate(time):
        row = ET.SubElement(table, "Row", index=str(frame_idx))
        ET.SubElement(row, "time").text = f"{t:.8f}"
        
        for plate_idx in range(len(processed_data)):
            for val in processed_data[plate_idx][:, frame_idx]:
                ET.SubElement(row, "value").text = f"{val:.8f}"
    
    # Write file
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    
    logger.info("GRF data XML generated successfully")


def batch_process(start_trial: int, end_trial: int, cutoff_freq: float = 6.0) -> None:
    """
    Batch process GRF extraction for multiple trials.
    
    Args:
        start_trial (int): First trial number (1-indexed)
        end_trial (int): Last trial number (inclusive)
        cutoff_freq (float): Filter cutoff frequency (Hz)
    """
    successful = 0
    failed = 0
    
    logger.info(f"Starting batch GRF extraction: trials {start_trial} to {end_trial}")
    
    for trial_num in range(start_trial, end_trial + 1):
        trial_str = str(trial_num).zfill(4)
        input_file = f'trial{trial_str}'
        output_xml = f'trial{trial_str}_GRF.xml'
        ik_file = f"IKResults_trial{trial_str}.mot"
        
        logger.info(f"Processing trial {trial_str} ({trial_num - start_trial + 1}/"
                   f"{end_trial - start_trial + 1})")
        
        try:
            processed_data, sample_rate = extract_force_data(input_file, cutoff_freq)
            if write_opensim_grf_xml(input_file, processed_data, sample_rate, 
                                    output_xml, ik_file):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Trial {trial_str}: {str(e)}")
            failed += 1
    
    logger.info(f"Batch complete: {successful} successful, {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract force plate data from .c3d and generate OpenSim-compatible outputs"
    )
    
    parser.add_argument('--input', type=str, help='Input .c3d file (without extension)')
    parser.add_argument('--output', type=str, help='Output XML file')
    parser.add_argument('--ik-file', type=str, default='IKResults.mot',
                       help='IK results file path for OpenSim reference')
    parser.add_argument('--batch', type=int, nargs=2, metavar=('START', 'END'),
                       help='Batch process trials START to END (inclusive)')
    parser.add_argument('--cutoff', type=float, default=6.0,
                       help='Low-pass filter cutoff frequency (Hz)')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_process(args.batch[0], args.batch[1], args.cutoff)
    elif args.input and args.output:
        try:
            processed_data, sample_rate = extract_force_data(args.input, args.cutoff)
            write_opensim_grf_xml(args.input, processed_data, sample_rate, 
                                 args.output, args.ik_file)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
    else:
        parser.print_help()
