#!/usr/bin/env python3
"""
FRA Parser Adapter and Auto-Detection

Automatic file format detection and parser routing for FRA data files.
Supports CSV, XML, JSON, and proprietary binary formats.
"""

import json
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Type, Union
import logging

from .csv_parser import CSVParser
from .xml_parser import XMLParser
from .proprietary_emulator import ProprietaryFormatEmulator

logger = logging.getLogger(__name__)

class FRAParserAdapter:
    """Universal FRA file parser with automatic format detection."""
    
    def __init__(self):
        self.csv_parser = CSVParser()
        self.xml_parser = XMLParser()
        self.binary_parser = ProprietaryFormatEmulator()
        
        # File extension to parser mapping
        self.extension_map = {
            '.csv': 'csv',
            '.txt': 'csv',  # Some CSV exports use .txt
            '.xml': 'xml',
            '.json': 'json',
            '.frx': 'omicron',  # Omicron binary
            '.dbl': 'doble',   # Doble binary
            '.meg': 'megger',  # Megger binary  
            '.n4f': 'newtons4th'  # Newtons4th binary
        }
        
        # Binary signatures for format detection
        self.binary_signatures = {
            b'OMICRON_FRX': 'omicron',
            b'DOBLE_M4000': 'doble',
            b'MEGGER_FRAX': 'megger',
            b'N4TH_ANALYZER': 'newtons4th'
        }
        
        # CSV delimiter detection patterns
        self.csv_patterns = [',', ';', '\t', '|']
    
    def detect_file_format(self, file_path: Union[str, Path]) -> str:
        """Detect FRA file format automatically.
        
        Returns: Format type ('csv', 'xml', 'json', 'omicron', 'doble', 'megger', 'newtons4th')
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"FRA file not found: {file_path}")
        
        # Check by extension first
        extension = file_path.suffix.lower()
        if extension in self.extension_map:
            detected_format = self.extension_map[extension]
            logger.info(f"Format detected by extension: {detected_format}")
            return detected_format
        
        # Read file header to detect format
        with open(file_path, 'rb') as f:
            header = f.read(1024)  # Read first 1KB
        
        # Check for binary signatures
        for signature, format_type in self.binary_signatures.items():
            if signature in header:
                logger.info(f"Format detected by binary signature: {format_type}")
                return format_type
        
        # Try to decode as text for CSV/XML/JSON detection
        try:
            header_text = header.decode('utf-8', errors='ignore')
            
            # Check for XML
            if header_text.strip().startswith('<?xml') or '<' in header_text[:100]:
                logger.info("Format detected as XML")
                return 'xml'
            
            # Check for JSON
            if header_text.strip().startswith('{') or header_text.strip().startswith('['):
                try:
                    json.loads(header_text[:512])
                    logger.info("Format detected as JSON")
                    return 'json'
                except json.JSONDecodeError:
                    pass
            
            # Check for CSV patterns
            for delimiter in self.csv_patterns:
                if delimiter in header_text and header_text.count(delimiter) > 5:
                    logger.info(f"Format detected as CSV with delimiter '{delimiter}'")
                    return 'csv'
            
            # If contains numbers and line breaks, assume CSV
            if any(char.isdigit() for char in header_text) and '\n' in header_text:
                logger.info("Format detected as CSV (fallback)")
                return 'csv'
                
        except UnicodeDecodeError:
            pass
        
        # Default fallback - try binary parsing
        logger.warning(f"Could not detect format for {file_path}, attempting binary parsing")
        return 'binary'
    
    def parse_json_file(self, file_path: str) -> Dict:
        """Parse JSON-formatted FRA file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If already in canonical format, return as-is
        if self._is_canonical_format(data):
            return data
        
        # Try to convert common JSON formats to canonical
        return self._convert_json_to_canonical(data, file_path)
    
    def _is_canonical_format(self, data: Dict) -> bool:
        """Check if data is already in canonical FRA format."""
        required_keys = ['asset_metadata', 'test_info', 'measurement', 'raw_file']
        return all(key in data for key in required_keys)
    
    def _convert_json_to_canonical(self, data: Dict, file_path: str) -> Dict:
        """Convert generic JSON FRA data to canonical format."""
        from datetime import datetime
        
        # Extract frequencies and magnitudes with various possible key names
        freq_keys = ['frequencies', 'freq', 'frequency', 'f', 'x_data']
        mag_keys = ['magnitudes', 'magnitude', 'mag', 'amplitude', 'y_data', 'db']
        phase_keys = ['phases', 'phase', 'angle', 'degrees']
        
        frequencies = None
        magnitudes = None
        phases = None
        
        for key in freq_keys:
            if key in data and isinstance(data[key], list):
                frequencies = data[key]
                break
        
        for key in mag_keys:
            if key in data and isinstance(data[key], list):
                magnitudes = data[key]
                break
        
        for key in phase_keys:
            if key in data and isinstance(data[key], list):
                phases = data[key]
                break
        
        if not frequencies or not magnitudes:
            raise ValueError("Could not find frequency and magnitude data in JSON file")
        
        # Build canonical structure with extracted data
        canonical_data = {
            "asset_metadata": {
                "asset_id": data.get('asset_id', data.get('id', 'unknown')),
                "manufacturer": data.get('manufacturer', data.get('make', 'unknown')),
                "model": data.get('model', 'unknown'),
                "rating_MVA": data.get('rating_MVA', data.get('rating', 100)),
                "winding_config": data.get('winding_config', 'unknown'),
                "serial": data.get('serial', 'unknown'),
                "year_installed": data.get('year_installed', 2020),
                "voltage_levels": data.get('voltage_levels', [132, 33])
            },
            "test_info": {
                "test_id": data.get('test_id', f"json_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "date": data.get('test_date', data.get('date', datetime.now().isoformat())),
                "technician": data.get('technician', 'unknown'),
                "instrument": data.get('instrument', data.get('device', 'unknown')),
                "test_voltage": data.get('test_voltage', data.get('voltage', 1000)),
                "coupling": data.get('coupling', 'capacitive'),
                "ambient_temp": data.get('ambient_temp', data.get('temperature', 25.0))
            },
            "measurement": {
                "frequencies": frequencies,
                "magnitudes": magnitudes,
                "unit": data.get('unit', data.get('magnitude_unit', 'dB')),
                "connection": data.get('connection', 'H1-H2'),
                "resolution": len(frequencies),
                "freq_start": frequencies[0],
                "freq_end": frequencies[-1]
            },
            "raw_file": {
                "filename": Path(file_path).name,
                "vendor_name": "generic",
                "original_format": "json",
                "file_size": Path(file_path).stat().st_size,
                "parser_version": "1.0"
            }
        }
        
        # Add phase data if available
        if phases:
            canonical_data["measurement"]["phases"] = phases
            canonical_data["measurement"]["phase_unit"] = "degrees"
        
        return canonical_data
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict:
        """Universal FRA file parser with automatic format detection.
        
        Args:
            file_path: Path to FRA data file
            
        Returns:
            Dict: Canonical FRA data structure
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported or parsing fails
        """
        file_path = Path(file_path)
        
        # Detect file format
        format_type = self.detect_file_format(file_path)
        
        logger.info(f"Parsing {file_path} as {format_type} format")
        
        try:
            # Route to appropriate parser
            if format_type == 'csv':
                return self.csv_parser.parse_file(str(file_path))
            
            elif format_type == 'xml':
                return self.xml_parser.parse_file(str(file_path))
            
            elif format_type == 'json':
                return self.parse_json_file(str(file_path))
            
            elif format_type in ['omicron', 'doble', 'megger', 'newtons4th']:
                return self.binary_parser.read_file(str(file_path))
            
            else:
                raise ValueError(f"Unsupported file format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            raise ValueError(f"Failed to parse FRA file {file_path.name}: {e}")
    
    def validate_canonical_data(self, data: Dict) -> bool:
        """Validate canonical FRA data structure.
        
        Args:
            data: Canonical FRA data dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required top-level keys
            required_keys = ['asset_metadata', 'test_info', 'measurement', 'raw_file']
            if not all(key in data for key in required_keys):
                return False
            
            # Check asset metadata
            asset_required = ['asset_id', 'manufacturer', 'model', 'rating_MVA']
            if not all(key in data['asset_metadata'] for key in asset_required):
                return False
            
            # Check test info
            test_required = ['test_id', 'date', 'instrument', 'test_voltage']
            if not all(key in data['test_info'] for key in test_required):
                return False
            
            # Check measurement data
            meas_required = ['frequencies', 'magnitudes', 'unit']
            if not all(key in data['measurement'] for key in meas_required):
                return False
            
            # Validate data arrays
            frequencies = data['measurement']['frequencies']
            magnitudes = data['measurement']['magnitudes']
            
            if not isinstance(frequencies, list) or not isinstance(magnitudes, list):
                return False
            
            if len(frequencies) != len(magnitudes) or len(frequencies) < 10:
                return False
            
            # Check if phase data exists and has correct length
            if 'phases' in data['measurement']:
                phases = data['measurement']['phases']
                if not isinstance(phases, list) or len(phases) != len(frequencies):
                    return False
            
            return True
            
        except (KeyError, TypeError, AttributeError):
            return False
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported file formats and extensions.
        
        Returns:
            Dict: Format categories and their supported extensions
        """
        return {
            'text_formats': ['.csv', '.txt', '.xml', '.json'],
            'binary_formats': ['.frx', '.dbl', '.meg', '.n4f'],
            'vendor_formats': {
                'omicron': '.frx',
                'doble': '.dbl',
                'megger': '.meg',
                'newtons4th': '.n4f'
            }
        }


# Test function
def test_parser_adapter():
    """Test the universal FRA parser adapter."""
    from .csv_parser import test_csv_parser
    from .xml_parser import test_xml_parser
    from .proprietary_emulator import test_proprietary_formats
    
    adapter = FRAParserAdapter()
    
    print("Testing FRA Parser Adapter...")
    print(f"Supported formats: {adapter.get_supported_formats()}")
    
    # Test CSV parsing
    print("\nTesting CSV parsing through adapter...")
    csv_result = test_csv_parser()
    if csv_result:
        is_valid = adapter.validate_canonical_data(csv_result)
        print(f"CSV validation result: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test XML parsing
    print("\nTesting XML parsing through adapter...")
    xml_result = test_xml_parser()
    if xml_result:
        is_valid = adapter.validate_canonical_data(xml_result)
        print(f"XML validation result: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test proprietary formats
    print("\nTesting proprietary formats through adapter...")
    test_proprietary_formats()
    
    print("\nFRA Parser Adapter testing completed!")


if __name__ == "__main__":
    test_parser_adapter()
