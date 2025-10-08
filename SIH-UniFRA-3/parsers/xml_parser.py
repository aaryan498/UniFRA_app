#!/usr/bin/env python3
"""
XML Parser for FRA Data

Supports XML export formats from various FRA instruments.
Handles different XML schemas and namespaces.
"""

import xml.etree.ElementTree as ET
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import re
import logging

logger = logging.getLogger(__name__)

class XMLParser:
    """Parser for XML-formatted FRA data files."""
    
    def __init__(self):
        self.common_namespaces = {
            'fra': 'http://fra.schema/v1.0',
            'omicron': 'http://omicron.com/fra',
            'doble': 'http://doble.com/fra',
            'megger': 'http://megger.com/fra'
        }
    
    def find_element_by_names(self, root: ET.Element, names: List[str]) -> Optional[ET.Element]:
        """Find XML element by trying multiple possible tag names."""
        for name in names:
            # Try direct find
            elem = root.find(name)
            if elem is not None:
                return elem
            
            # Try case-insensitive search
            for child in root.iter():
                if child.tag.lower().endswith(name.lower()):
                    return child
        return None
    
    def extract_text_or_attr(self, element: ET.Element, attr_names: List[str] = None) -> str:
        """Extract text content or attribute value from XML element."""
        if element is None:
            return "unknown"
        
        # Try text content first
        if element.text and element.text.strip():
            return element.text.strip()
        
        # Try attributes
        if attr_names:
            for attr in attr_names:
                if attr in element.attrib:
                    return element.attrib[attr]
        
        return "unknown"
    
    def parse_frequency_data(self, root: ET.Element) -> Dict[str, List[float]]:
        """Extract frequency, magnitude, and phase data from XML."""
        data = {'frequencies': [], 'magnitudes': [], 'phases': []}
        
        # Common XML structures to try
        data_paths = [
            './/MeasurementData',
            './/Data',
            './/FrequencyResponse',
            './/FRA_Data',
            './/Measurements',
            './/Points',
            './/Samples'
        ]
        
        measurement_elem = None
        for path in data_paths:
            measurement_elem = root.find(path)
            if measurement_elem is not None:
                break
        
        if measurement_elem is None:
            # Try to find any element with frequency data
            for elem in root.iter():
                if any(tag in elem.tag.lower() for tag in ['freq', 'data', 'measurement']):
                    measurement_elem = elem
                    break
        
        if measurement_elem is None:
            raise ValueError("Could not find measurement data in XML")
        
        # Try different data point structures
        point_elements = [
            measurement_elem.findall('.//Point'),
            measurement_elem.findall('.//DataPoint'),
            measurement_elem.findall('.//Sample'),
            measurement_elem.findall('.//Measurement')
        ]
        
        points = None
        for point_list in point_elements:
            if point_list:
                points = point_list
                break
        
        if points:
            # Parse individual data points
            for point in points:
                try:
                    # Try multiple field names for frequency
                    freq_elem = self.find_element_by_names(point, ['Frequency', 'Freq', 'F', 'Hz'])
                    mag_elem = self.find_element_by_names(point, ['Magnitude', 'Mag', 'Amplitude', 'dB', 'Gain'])
                    phase_elem = self.find_element_by_names(point, ['Phase', 'Angle', 'Degrees', 'Deg'])
                    
                    if freq_elem is not None and mag_elem is not None:
                        freq = float(self.extract_text_or_attr(freq_elem, ['value']))
                        mag = float(self.extract_text_or_attr(mag_elem, ['value']))
                        
                        data['frequencies'].append(freq)
                        data['magnitudes'].append(mag)
                        
                        if phase_elem is not None:
                            phase = float(self.extract_text_or_attr(phase_elem, ['value']))
                            data['phases'].append(phase)
                            
                except (ValueError, TypeError):
                    continue
        
        else:
            # Try array-based data structure
            freq_arrays = [
                measurement_elem.find('.//Frequencies'),
                measurement_elem.find('.//FrequencyArray'),
                measurement_elem.find('.//F_Array')
            ]
            
            mag_arrays = [
                measurement_elem.find('.//Magnitudes'),
                measurement_elem.find('.//MagnitudeArray'), 
                measurement_elem.find('.//Mag_Array')
            ]
            
            freq_array = next((arr for arr in freq_arrays if arr is not None), None)
            mag_array = next((arr for arr in mag_arrays if arr is not None), None)
            
            if freq_array is not None and mag_array is not None:
                # Parse comma or space separated values
                freq_text = freq_array.text or ""
                mag_text = mag_array.text or ""
                
                # Try different separators
                for separator in [',', ';', ' ', '\t', '\n']:
                    if separator in freq_text:
                        freq_values = [float(x.strip()) for x in freq_text.split(separator) if x.strip()]
                        mag_values = [float(x.strip()) for x in mag_text.split(separator) if x.strip()]
                        
                        if len(freq_values) == len(mag_values) and len(freq_values) > 10:
                            data['frequencies'] = freq_values
                            data['magnitudes'] = mag_values
                            break
        
        if len(data['frequencies']) < 10:
            raise ValueError("Insufficient frequency data points found in XML")
        
        return data
    
    def parse_metadata(self, root: ET.Element) -> Dict:
        """Extract metadata from XML structure."""
        metadata = {
            'asset_id': 'unknown',
            'manufacturer': 'unknown',
            'model': 'unknown', 
            'rating_MVA': 100,
            'test_date': datetime.now().isoformat(),
            'instrument': 'unknown',
            'test_voltage': 1000
        }
        
        # Try to find asset/transformer information
        asset_paths = ['.//Asset', './/Transformer', './/Equipment', './/Device']
        asset_elem = None
        for path in asset_paths:
            asset_elem = root.find(path)
            if asset_elem is not None:
                break
        
        if asset_elem is not None:
            # Extract asset metadata
            id_elem = self.find_element_by_names(asset_elem, ['ID', 'AssetID', 'SerialNumber', 'Name'])
            if id_elem is not None:
                metadata['asset_id'] = self.extract_text_or_attr(id_elem)
            
            mfg_elem = self.find_element_by_names(asset_elem, ['Manufacturer', 'Make', 'Brand'])
            if mfg_elem is not None:
                metadata['manufacturer'] = self.extract_text_or_attr(mfg_elem)
            
            model_elem = self.find_element_by_names(asset_elem, ['Model', 'Type', 'ModelNumber'])
            if model_elem is not None:
                metadata['model'] = self.extract_text_or_attr(model_elem)
            
            rating_elem = self.find_element_by_names(asset_elem, ['Rating', 'MVA', 'Power', 'Capacity'])
            if rating_elem is not None:
                try:
                    rating_text = self.extract_text_or_attr(rating_elem)
                    metadata['rating_MVA'] = float(re.findall(r'[\d.]+', rating_text)[0])
                except:
                    pass
        
        # Try to find test information
        test_paths = ['.//Test', './/TestInfo', './/Measurement', './/TestConditions']
        test_elem = None
        for path in test_paths:
            test_elem = root.find(path)
            if test_elem is not None:
                break
        
        if test_elem is not None:
            date_elem = self.find_element_by_names(test_elem, ['Date', 'TestDate', 'DateTime', 'Timestamp'])
            if date_elem is not None:
                metadata['test_date'] = self.extract_text_or_attr(date_elem)
            
            instrument_elem = self.find_element_by_names(test_elem, ['Instrument', 'Device', 'Analyzer', 'Equipment'])
            if instrument_elem is not None:
                metadata['instrument'] = self.extract_text_or_attr(instrument_elem)
            
            voltage_elem = self.find_element_by_names(test_elem, ['Voltage', 'TestVoltage', 'ExcitationVoltage'])
            if voltage_elem is not None:
                try:
                    voltage_text = self.extract_text_or_attr(voltage_elem)
                    metadata['test_voltage'] = float(re.findall(r'[\d.]+', voltage_text)[0])
                except:
                    pass
        
        return metadata
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse XML file and return canonical FRA data structure."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"XML file not found: {file_path}")
        
        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")
        
        # Extract metadata and measurement data
        metadata = self.parse_metadata(root)
        data = self.parse_frequency_data(root)
        
        # Convert to numpy arrays for processing
        frequencies = np.array(data['frequencies'])
        magnitudes = np.array(data['magnitudes'])
        
        # Determine magnitude unit (heuristic)
        magnitude_unit = 'dB'
        if np.all(magnitudes >= 0) and np.max(magnitudes) < 10:
            magnitude_unit = 'linear'
            # Convert to dB
            magnitudes = 20 * np.log10(np.maximum(magnitudes, 1e-12))
        
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
                "magnitudes": magnitudes.tolist(),
                "unit": "dB",
                "connection": "H1-H2",
                "resolution": len(frequencies),
                "freq_start": float(frequencies[0]),
                "freq_end": float(frequencies[-1])
            },
            "raw_file": {
                "filename": file_path.name,
                "vendor_name": "generic",
                "original_format": "xml",
                "file_size": file_path.stat().st_size,
                "parser_version": "1.0"
            }
        }
        
        # Add phase data if available
        if data['phases']:
            canonical_data["measurement"]["phases"] = data['phases']
            canonical_data["measurement"]["phase_unit"] = "degrees"
        
        return canonical_data


# Test function
def test_xml_parser():
    """Test the XML parser with a sample file."""
    parser = XMLParser()
    
    # Create a test XML file
    test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<FRA_Measurement xmlns="http://fra.schema/v1.0">
    <Asset>
        <ID>TR002</ID>
        <Manufacturer>Siemens</Manufacturer>
        <Model>GEAFOL 200MVA</Model>
        <Rating>200 MVA</Rating>
    </Asset>
    <Test>
        <Date>2024-01-20T10:30:00Z</Date>
        <Instrument>Doble M4000</Instrument>
        <Voltage>800V</Voltage>
    </Test>
    <MeasurementData>
        <Point>
            <Frequency>20000</Frequency>
            <Magnitude>42.1</Magnitude>
            <Phase>3.2</Phase>
        </Point>
        <Point>
            <Frequency>30000</Frequency>
            <Magnitude>41.8</Magnitude>
            <Phase>2.9</Phase>
        </Point>
        <Point>
            <Frequency>50000</Frequency>
            <Magnitude>40.9</Magnitude>
            <Phase>2.1</Phase>
        </Point>
        <Point>
            <Frequency>75000</Frequency>
            <Magnitude>39.2</Magnitude>
            <Phase>1.2</Phase>
        </Point>
        <Point>
            <Frequency>100000</Frequency>
            <Magnitude>37.8</Magnitude>
            <Phase>0.1</Phase>
        </Point>
        <Point>
            <Frequency>150000</Frequency>
            <Magnitude>35.1</Magnitude>
            <Phase>-1.2</Phase>
        </Point>
        <Point>
            <Frequency>200000</Frequency>
            <Magnitude>32.9</Magnitude>
            <Phase>-2.8</Phase>
        </Point>
        <Point>
            <Frequency>300000</Frequency>
            <Magnitude>29.1</Magnitude>
            <Phase>-5.1</Phase>
        </Point>
        <Point>
            <Frequency>500000</Frequency>
            <Magnitude>24.8</Magnitude>
            <Phase>-9.2</Phase>
        </Point>
        <Point>
            <Frequency>750000</Frequency>
            <Magnitude>19.9</Magnitude>
            <Phase>-15.1</Phase>
        </Point>
        <Point>
            <Frequency>1000000</Frequency>
            <Magnitude>15.2</Magnitude>
            <Phase>-22.8</Phase>
        </Point>
        <Point>
            <Frequency>1500000</Frequency>
            <Magnitude>9.8</Magnitude>
            <Phase>-35.2</Phase>
        </Point>
        <Point>
            <Frequency>2000000</Frequency>
            <Magnitude>4.1</Magnitude>
            <Phase>-48.9</Phase>
        </Point>
        <Point>
            <Frequency>3000000</Frequency>
            <Magnitude>-2.1</Magnitude>
            <Phase>-68.2</Phase>
        </Point>
        <Point>
            <Frequency>5000000</Frequency>
            <Magnitude>-9.8</Magnitude>
            <Phase>-95.1</Phase>
        </Point>
    </MeasurementData>
</FRA_Measurement>'''
    
    # Write test file
    test_file = Path("/tmp/test_fra.xml")
    test_file.write_text(test_xml)
    
    # Parse and print result
    try:
        result = parser.parse_file(str(test_file))
        print("XML Parser Test Successful!")
        print(f"Asset ID: {result['asset_metadata']['asset_id']}")
        print(f"Manufacturer: {result['asset_metadata']['manufacturer']}")
        print(f"Data points: {len(result['measurement']['frequencies'])}")
        print(f"Frequency range: {result['measurement']['freq_start']:.0f} - {result['measurement']['freq_end']:.0f} Hz")
        return result
    except Exception as e:
        print(f"XML Parser Test Failed: {e}")
        return None
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_xml_parser()
