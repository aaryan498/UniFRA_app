#!/usr/bin/env python3
"""
CSV Parser for FRA Data

Supports common CSV export formats from various FRA instruments.
Handles different delimiter types, header formats, and unit conversions.
"""

import csv
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class CSVParser:
    """Parser for CSV-formatted FRA data files."""
    
    def __init__(self):
        self.supported_delimiters = [',', ';', '\t', '|']
        self.frequency_keywords = ['freq', 'frequency', 'f', 'hz']
        self.magnitude_keywords = ['mag', 'magnitude', 'amp', 'amplitude', 'db', 'gain']
        self.phase_keywords = ['phase', 'ph', 'angle', 'deg', 'degrees']
    
    def detect_delimiter(self, file_path: str) -> str:
        """Auto-detect CSV delimiter by analyzing first few lines."""
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
        
        delimiter_counts = {}
        for delimiter in self.supported_delimiters:
            delimiter_counts[delimiter] = sample.count(delimiter)
        
        return max(delimiter_counts, key=delimiter_counts.get)
    
    def parse_header_metadata(self, lines: List[str]) -> Dict:
        """Extract metadata from CSV header comments."""
        metadata = {
            'asset_id': 'unknown',
            'manufacturer': 'unknown', 
            'model': 'unknown',
            'rating_MVA': 100,
            'test_date': datetime.now().isoformat(),
            'instrument': 'unknown',
            'test_voltage': 1000
        }
        
        # Look for metadata in comments (lines starting with # or %)
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith('#') or line.startswith('%') or line.startswith('//'):
                # Parse key-value pairs
                if ':' in line:
                    key_val = line[1:].split(':', 1)
                    if len(key_val) == 2:
                        key = key_val[0].strip().lower().replace(' ', '_')
                        val = key_val[1].strip()
                        
                        # Map common metadata fields
                        if 'asset' in key or 'transformer' in key or 'id' in key:
                            metadata['asset_id'] = val
                        elif 'manufacturer' in key or 'make' in key:
                            metadata['manufacturer'] = val
                        elif 'model' in key:
                            metadata['model'] = val
                        elif 'mva' in key or 'rating' in key:
                            try:
                                metadata['rating_MVA'] = float(val.replace('MVA', '').strip())
                            except:
                                pass
                        elif 'date' in key:
                            metadata['test_date'] = val
                        elif 'instrument' in key or 'device' in key:
                            metadata['instrument'] = val
                        elif 'voltage' in key and 'test' in key:
                            try:
                                metadata['test_voltage'] = float(re.findall(r'\d+', val)[0])
                            except:
                                pass
        
        return metadata
    
    def identify_columns(self, header_row: List[str]) -> Dict[str, int]:
        """Identify column indices for frequency, magnitude, and phase data."""
        columns = {}
        
        for i, col_name in enumerate(header_row):
            col_lower = col_name.lower().strip()
            
            # Check for frequency column
            if any(keyword in col_lower for keyword in self.frequency_keywords):
                columns['frequency'] = i
            
            # Check for magnitude column  
            elif any(keyword in col_lower for keyword in self.magnitude_keywords):
                columns['magnitude'] = i
            
            # Check for phase column
            elif any(keyword in col_lower for keyword in self.phase_keywords):
                columns['phase'] = i
        
        # If columns not found by keywords, assume standard order
        if 'frequency' not in columns and len(header_row) >= 2:
            columns['frequency'] = 0
            columns['magnitude'] = 1
            if len(header_row) >= 3:
                columns['phase'] = 2
        
        return columns
    
    def convert_magnitude_to_db(self, magnitudes: np.ndarray, current_unit: str) -> np.ndarray:
        """Convert magnitude values to dB if needed."""
        if current_unit.lower() in ['db', 'decibel']:
            return magnitudes
        elif current_unit.lower() in ['magnitude', 'linear', 'ratio']:
            # Convert linear magnitude to dB
            return 20 * np.log10(np.maximum(magnitudes, 1e-12))  # Avoid log(0)
        else:
            # Assume linear if unknown
            logger.warning(f"Unknown magnitude unit: {current_unit}, assuming linear")
            return 20 * np.log10(np.maximum(magnitudes, 1e-12))
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse CSV file and return canonical FRA data structure."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Read all lines
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            raise ValueError("Empty CSV file")
        
        # Extract metadata from header comments
        metadata = self.parse_header_metadata(lines)
        
        # Detect delimiter
        delimiter = self.detect_delimiter(str(file_path))
        
        # Find data start (skip comment lines)
        data_start = 0
        for i, line in enumerate(lines):
            if not (line.strip().startswith('#') or line.strip().startswith('%') or 
                   line.strip().startswith('//') or line.strip() == ''):
                data_start = i
                break
        
        # Parse CSV data
        csv_reader = csv.reader(lines[data_start:], delimiter=delimiter)
        rows = list(csv_reader)
        
        if len(rows) < 2:
            raise ValueError("Insufficient data rows in CSV file")
        
        # Identify columns
        header_row = rows[0]
        columns = self.identify_columns(header_row)
        
        if 'frequency' not in columns or 'magnitude' not in columns:
            raise ValueError("Could not identify frequency and magnitude columns")
        
        # Extract data
        frequencies = []
        magnitudes = []
        phases = []
        
        for row in rows[1:]:
            if len(row) <= max(columns.values()):
                continue
            
            try:
                freq = float(row[columns['frequency']])
                mag = float(row[columns['magnitude']])
                
                frequencies.append(freq)
                magnitudes.append(mag)
                
                if 'phase' in columns:
                    phase = float(row[columns['phase']])
                    phases.append(phase)
                    
            except (ValueError, IndexError):
                continue
        
        if len(frequencies) < 10:
            raise ValueError("Insufficient valid data points (minimum 10 required)")
        
        # Convert to numpy arrays
        frequencies = np.array(frequencies)
        magnitudes = np.array(magnitudes)
        
        # Determine magnitude unit (heuristic)
        magnitude_unit = 'dB'
        if np.all(magnitudes >= 0) and np.max(magnitudes) < 10:
            magnitude_unit = 'linear'
        
        # Convert to dB if needed
        magnitudes_db = self.convert_magnitude_to_db(magnitudes, magnitude_unit)
        
        # Build canonical structure
        canonical_data = {
            "asset_metadata": {
                "asset_id": metadata['asset_id'],
                "manufacturer": metadata['manufacturer'],
                "model": metadata['model'],
                "rating_MVA": metadata['rating_MVA'],
                "winding_config": "unknown",
                "serial": "unknown",
                "year_installed": 2020,
                "voltage_levels": [132, 33]
            },
            "test_info": {
                "test_id": f"test_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "date": metadata['test_date'],
                "technician": "unknown",
                "instrument": metadata['instrument'],
                "test_voltage": metadata['test_voltage'],
                "coupling": "capacitive",
                "ambient_temp": 25.0
            },
            "measurement": {
                "frequencies": frequencies.tolist(),
                "magnitudes": magnitudes_db.tolist(),
                "unit": "dB",
                "connection": "H1-H2",
                "resolution": len(frequencies),
                "freq_start": float(frequencies[0]),
                "freq_end": float(frequencies[-1])
            },
            "raw_file": {
                "filename": file_path.name,
                "vendor_name": "generic",
                "original_format": "csv",
                "file_size": file_path.stat().st_size,
                "parser_version": "1.0"
            }
        }
        
        # Add phase data if available
        if phases:
            canonical_data["measurement"]["phases"] = phases
            canonical_data["measurement"]["phase_unit"] = "degrees"
        
        return canonical_data


# Test function
def test_csv_parser():
    """Test the CSV parser with a sample file."""
    parser = CSVParser()
    
    # Create a test CSV file
    test_data = """# Asset ID: TR001
# Manufacturer: ABB
# Model: TDOC 300MVA
# Rating: 300 MVA
# Test Date: 2024-01-15
# Instrument: Omicron FRAnalyzer
# Test Voltage: 1000V
Frequency (Hz),Magnitude (dB),Phase (deg)
20000,45.2,5.1
25000,44.8,4.9
30000,44.1,4.5
40000,43.2,3.8
50000,42.1,3.2
75000,40.5,2.1
100000,38.9,1.2
150000,36.8,-0.5
200000,34.2,-2.1
300000,31.5,-4.2
500000,28.1,-7.8
750000,24.3,-12.1
1000000,20.8,-18.5
1500000,16.2,-28.2
2000000,12.1,-38.9
3000000,7.8,-55.2
5000000,2.1,-78.5
7500000,-3.2,-95.1
10000000,-8.9,-118.2
12000000,-15.2,-142.8"""
    
    # Write test file
    test_file = Path("/tmp/test_fra.csv")
    test_file.write_text(test_data)
    
    # Parse and print result
    try:
        result = parser.parse_file(str(test_file))
        print("CSV Parser Test Successful!")
        print(f"Asset ID: {result['asset_metadata']['asset_id']}")
        print(f"Manufacturer: {result['asset_metadata']['manufacturer']}")
        print(f"Data points: {len(result['measurement']['frequencies'])}")
        print(f"Frequency range: {result['measurement']['freq_start']:.0f} - {result['measurement']['freq_end']:.0f} Hz")
        return result
    except Exception as e:
        print(f"CSV Parser Test Failed: {e}")
        return None
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_csv_parser()
