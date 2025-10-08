#!/usr/bin/env python3
"""
Proprietary Binary Format Emulator for FRA Data

Emulates binary file formats from major FRA instrument vendors:
- Omicron (.frx)
- Doble (.dbl)
- Megger (.meg)
- Newtons4th (.n4f)

Includes both writers (to create sample files) and readers (parsers).
"""

import struct
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, BinaryIO
import hashlib
import logging

logger = logging.getLogger(__name__)

class ProprietaryFormatEmulator:
    """Emulates proprietary binary FRA formats from major vendors."""
    
    def __init__(self):
        self.vendor_signatures = {
            'omicron': b'OMICRON_FRX_V2.1',
            'doble': b'DOBLE_M4000_FMT1',
            'megger': b'MEGGER_FRAX_150',
            'newtons4th': b'N4TH_ANALYZER_V3'
        }
        
        self.format_extensions = {
            'omicron': '.frx',
            'doble': '.dbl', 
            'megger': '.meg',
            'newtons4th': '.n4f'
        }
    
    def write_omicron_frx(self, canonical_data: Dict, output_path: str) -> None:
        """Write Omicron .frx binary format (emulated)."""
        with open(output_path, 'wb') as f:
            # Header signature
            f.write(self.vendor_signatures['omicron'])
            f.write(b'\x00' * (64 - len(self.vendor_signatures['omicron'])))
            
            # Format version
            f.write(struct.pack('<I', 0x00020001))  # Version 2.1
            
            # Asset metadata section
            asset_id = canonical_data['asset_metadata']['asset_id'].encode('utf-8')[:32]
            f.write(struct.pack('<32s', asset_id))
            
            manufacturer = canonical_data['asset_metadata']['manufacturer'].encode('utf-8')[:32] 
            f.write(struct.pack('<32s', manufacturer))
            
            model = canonical_data['asset_metadata']['model'].encode('utf-8')[:32]
            f.write(struct.pack('<32s', model))
            
            f.write(struct.pack('<f', canonical_data['asset_metadata']['rating_MVA']))
            
            # Test info section
            test_id = canonical_data['test_info']['test_id'].encode('utf-8')[:32]
            f.write(struct.pack('<32s', test_id))
            
            f.write(struct.pack('<f', canonical_data['test_info']['test_voltage']))
            f.write(struct.pack('<f', canonical_data['test_info'].get('ambient_temp', 25.0)))
            
            # Measurement section header
            frequencies = canonical_data['measurement']['frequencies']
            magnitudes = canonical_data['measurement']['magnitudes']
            phases = canonical_data['measurement'].get('phases', [0] * len(frequencies))
            
            num_points = len(frequencies)
            f.write(struct.pack('<I', num_points))
            f.write(struct.pack('<d', frequencies[0]))  # Start freq
            f.write(struct.pack('<d', frequencies[-1])) # End freq
            
            # Connection info
            connection = canonical_data['measurement'].get('connection', 'H1-H2').encode('utf-8')[:16]
            f.write(struct.pack('<16s', connection))
            
            # Data section
            for i in range(num_points):
                f.write(struct.pack('<d', frequencies[i]))  # 8 bytes
                f.write(struct.pack('<f', magnitudes[i]))   # 4 bytes
                f.write(struct.pack('<f', phases[i]))       # 4 bytes
            
            # Checksum (simple CRC32)
            f.seek(0)
            data = f.read()
            checksum = hashlib.crc32(data) & 0xffffffff
            f.write(struct.pack('<I', checksum))
    
    def read_omicron_frx(self, file_path: str) -> Dict:
        """Read Omicron .frx binary format (emulated)."""
        with open(file_path, 'rb') as f:
            # Verify header signature
            header = f.read(64)
            if not header.startswith(self.vendor_signatures['omicron']):
                raise ValueError("Invalid Omicron FRX file signature")
            
            # Read format version
            version = struct.unpack('<I', f.read(4))[0]
            
            # Read asset metadata
            asset_id = struct.unpack('<32s', f.read(32))[0].decode('utf-8').rstrip('\x00')
            manufacturer = struct.unpack('<32s', f.read(32))[0].decode('utf-8').rstrip('\x00')
            model = struct.unpack('<32s', f.read(32))[0].decode('utf-8').rstrip('\x00')
            rating_mva = struct.unpack('<f', f.read(4))[0]
            
            # Read test info
            test_id = struct.unpack('<32s', f.read(32))[0].decode('utf-8').rstrip('\x00')
            test_voltage = struct.unpack('<f', f.read(4))[0]
            ambient_temp = struct.unpack('<f', f.read(4))[0]
            
            # Read measurement header
            num_points = struct.unpack('<I', f.read(4))[0]
            freq_start = struct.unpack('<d', f.read(8))[0]
            freq_end = struct.unpack('<d', f.read(8))[0]
            connection = struct.unpack('<16s', f.read(16))[0].decode('utf-8').rstrip('\x00')
            
            # Read measurement data
            frequencies = []
            magnitudes = []
            phases = []
            
            for _ in range(num_points):
                freq = struct.unpack('<d', f.read(8))[0]
                mag = struct.unpack('<f', f.read(4))[0]
                phase = struct.unpack('<f', f.read(4))[0]
                
                frequencies.append(freq)
                magnitudes.append(mag)
                phases.append(phase)
        
        # Build canonical data structure
        return {
            "asset_metadata": {
                "asset_id": asset_id,
                "manufacturer": manufacturer,
                "model": model,
                "rating_MVA": rating_mva,
                "winding_config": "unknown",
                "serial": "unknown",
                "year_installed": 2020,
                "voltage_levels": [132, 33]
            },
            "test_info": {
                "test_id": test_id,
                "date": datetime.now().isoformat(),
                "technician": "unknown",
                "instrument": "Omicron FRAnalyzer",
                "test_voltage": test_voltage,
                "coupling": "capacitive",
                "ambient_temp": ambient_temp
            },
            "measurement": {
                "frequencies": frequencies,
                "magnitudes": magnitudes,
                "phases": phases,
                "unit": "dB",
                "connection": connection,
                "resolution": num_points,
                "freq_start": freq_start,
                "freq_end": freq_end
            },
            "raw_file": {
                "filename": Path(file_path).name,
                "vendor_name": "omicron",
                "original_format": "binary",
                "file_size": Path(file_path).stat().st_size,
                "parser_version": "1.0"
            }
        }
    
    def write_doble_dbl(self, canonical_data: Dict, output_path: str) -> None:
        """Write Doble .dbl binary format (emulated)."""
        with open(output_path, 'wb') as f:
            # Header signature
            f.write(self.vendor_signatures['doble'])
            f.write(b'\x00' * (32 - len(self.vendor_signatures['doble'])))
            
            # Doble uses big-endian format
            # File header
            f.write(struct.pack('>I', 0x44424C01))  # DBL1 signature
            f.write(struct.pack('>H', 2024))        # Year
            f.write(struct.pack('>H', 1))           # Month
            f.write(struct.pack('>H', 15))          # Day
            
            # Asset info (Doble format uses fixed 64-byte blocks)
            asset_block = bytearray(64)
            asset_id_bytes = canonical_data['asset_metadata']['asset_id'].encode('utf-8')[:32]
            asset_block[:len(asset_id_bytes)] = asset_id_bytes
            f.write(asset_block)
            
            # Test parameters
            f.write(struct.pack('>f', canonical_data['test_info']['test_voltage']))
            f.write(struct.pack('>I', len(canonical_data['measurement']['frequencies'])))
            f.write(struct.pack('>d', canonical_data['measurement']['freq_start']))
            f.write(struct.pack('>d', canonical_data['measurement']['freq_end']))
            
            # Measurement data (interleaved format)
            frequencies = canonical_data['measurement']['frequencies']
            magnitudes = canonical_data['measurement']['magnitudes']
            phases = canonical_data['measurement'].get('phases', [0] * len(frequencies))
            
            for i in range(len(frequencies)):
                f.write(struct.pack('>d', frequencies[i]))
                f.write(struct.pack('>d', magnitudes[i]))
                f.write(struct.pack('>d', phases[i]))
    
    def read_doble_dbl(self, file_path: str) -> Dict:
        """Read Doble .dbl binary format (emulated)."""
        with open(file_path, 'rb') as f:
            # Verify header
            header = f.read(32)
            if not header.startswith(self.vendor_signatures['doble']):
                raise ValueError("Invalid Doble DBL file signature")
            
            # Read file header (big-endian)
            signature = struct.unpack('>I', f.read(4))[0]
            year = struct.unpack('>H', f.read(2))[0]
            month = struct.unpack('>H', f.read(2))[0] 
            day = struct.unpack('>H', f.read(2))[0]
            
            # Read asset info
            asset_block = f.read(64)
            asset_id = asset_block.decode('utf-8').rstrip('\x00')
            
            # Read test parameters
            test_voltage = struct.unpack('>f', f.read(4))[0]
            num_points = struct.unpack('>I', f.read(4))[0]
            freq_start = struct.unpack('>d', f.read(8))[0]
            freq_end = struct.unpack('>d', f.read(8))[0]
            
            # Read measurement data
            frequencies = []
            magnitudes = []
            phases = []
            
            for _ in range(num_points):
                freq = struct.unpack('>d', f.read(8))[0]
                mag = struct.unpack('>d', f.read(8))[0]
                phase = struct.unpack('>d', f.read(8))[0]
                
                frequencies.append(freq)
                magnitudes.append(mag)
                phases.append(phase)
        
        return {
            "asset_metadata": {
                "asset_id": asset_id,
                "manufacturer": "unknown",
                "model": "unknown",
                "rating_MVA": 100,
                "winding_config": "unknown",
                "serial": "unknown", 
                "year_installed": 2020,
                "voltage_levels": [132, 33]
            },
            "test_info": {
                "test_id": f"doble_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "date": f"{year}-{month:02d}-{day:02d}T12:00:00Z",
                "technician": "unknown",
                "instrument": "Doble M4000",
                "test_voltage": test_voltage,
                "coupling": "capacitive",
                "ambient_temp": 25.0
            },
            "measurement": {
                "frequencies": frequencies,
                "magnitudes": magnitudes,
                "phases": phases,
                "unit": "dB",
                "connection": "H1-H2",
                "resolution": num_points,
                "freq_start": freq_start,
                "freq_end": freq_end
            },
            "raw_file": {
                "filename": Path(file_path).name,
                "vendor_name": "doble",
                "original_format": "binary",
                "file_size": Path(file_path).stat().st_size,
                "parser_version": "1.0"
            }
        }
    
    def write_megger_meg(self, canonical_data: Dict, output_path: str) -> None:
        """Write Megger .meg binary format (emulated)."""
        with open(output_path, 'wb') as f:
            # Megger header with proprietary structure
            f.write(self.vendor_signatures['megger'])
            f.write(b'\x00' * (48 - len(self.vendor_signatures['megger'])))
            
            # Megger-specific header fields
            f.write(struct.pack('<I', 0x4D454752))  # 'MEGR' in little-endian
            f.write(struct.pack('<H', 150))         # Model FRAX-150
            f.write(struct.pack('<H', 0x0001))      # Format version
            
            # Asset and test metadata (Megger uses Pascal-style strings)
            asset_id = canonical_data['asset_metadata']['asset_id']
            self._write_pascal_string(f, asset_id, 32)
            
            manufacturer = canonical_data['asset_metadata']['manufacturer']
            self._write_pascal_string(f, manufacturer, 32)
            
            # Test voltage and conditions
            f.write(struct.pack('<f', canonical_data['test_info']['test_voltage']))
            f.write(struct.pack('<f', canonical_data['test_info'].get('ambient_temp', 25.0)))
            
            # Frequency sweep parameters
            frequencies = canonical_data['measurement']['frequencies']
            magnitudes = canonical_data['measurement']['magnitudes']
            phases = canonical_data['measurement'].get('phases', [0] * len(frequencies))
            
            f.write(struct.pack('<I', len(frequencies)))  # Number of points
            f.write(struct.pack('<I', 0))                 # Reserved
            
            # Data in Megger format (frequency, magnitude, phase triplets)
            for i in range(len(frequencies)):
                f.write(struct.pack('<f', frequencies[i]))
                f.write(struct.pack('<f', magnitudes[i]))
                f.write(struct.pack('<f', phases[i]))
                f.write(struct.pack('<I', i))  # Point index
    
    def _write_pascal_string(self, f: BinaryIO, text: str, max_len: int) -> None:
        """Write Pascal-style string (length byte + string data)."""
        text_bytes = text.encode('utf-8')[:max_len-1]
        f.write(struct.pack('<B', len(text_bytes)))
        f.write(text_bytes)
        # Pad to max_len
        f.write(b'\x00' * (max_len - 1 - len(text_bytes)))
    
    def _read_pascal_string(self, f: BinaryIO, max_len: int) -> str:
        """Read Pascal-style string."""
        length = struct.unpack('<B', f.read(1))[0]
        text_bytes = f.read(length)
        f.read(max_len - 1 - length)  # Skip padding
        return text_bytes.decode('utf-8')
    
    def read_megger_meg(self, file_path: str) -> Dict:
        """Read Megger .meg binary format (emulated)."""
        with open(file_path, 'rb') as f:
            # Verify header
            header = f.read(48)
            if not header.startswith(self.vendor_signatures['megger']):
                raise ValueError("Invalid Megger MEG file signature")
            
            # Read Megger header
            signature = struct.unpack('<I', f.read(4))[0]
            model = struct.unpack('<H', f.read(2))[0]
            version = struct.unpack('<H', f.read(2))[0]
            
            # Read metadata
            asset_id = self._read_pascal_string(f, 32)
            manufacturer = self._read_pascal_string(f, 32)
            
            test_voltage = struct.unpack('<f', f.read(4))[0]
            ambient_temp = struct.unpack('<f', f.read(4))[0]
            
            # Read measurement parameters
            num_points = struct.unpack('<I', f.read(4))[0]
            reserved = struct.unpack('<I', f.read(4))[0]
            
            # Read data
            frequencies = []
            magnitudes = []
            phases = []
            
            for _ in range(num_points):
                freq = struct.unpack('<f', f.read(4))[0]
                mag = struct.unpack('<f', f.read(4))[0]
                phase = struct.unpack('<f', f.read(4))[0]
                index = struct.unpack('<I', f.read(4))[0]
                
                frequencies.append(freq)
                magnitudes.append(mag)
                phases.append(phase)
        
        return {
            "asset_metadata": {
                "asset_id": asset_id,
                "manufacturer": manufacturer,
                "model": f"FRAX-{model}",
                "rating_MVA": 100,
                "winding_config": "unknown",
                "serial": "unknown",
                "year_installed": 2020,
                "voltage_levels": [132, 33]
            },
            "test_info": {
                "test_id": f"megger_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "date": datetime.now().isoformat(),
                "technician": "unknown",
                "instrument": f"Megger FRAX-{model}",
                "test_voltage": test_voltage,
                "coupling": "capacitive",
                "ambient_temp": ambient_temp
            },
            "measurement": {
                "frequencies": frequencies,
                "magnitudes": magnitudes,
                "phases": phases,
                "unit": "dB",
                "connection": "H1-H2",
                "resolution": num_points,
                "freq_start": frequencies[0] if frequencies else 0,
                "freq_end": frequencies[-1] if frequencies else 0
            },
            "raw_file": {
                "filename": Path(file_path).name,
                "vendor_name": "megger",
                "original_format": "binary",
                "file_size": Path(file_path).stat().st_size,
                "parser_version": "1.0"
            }
        }
    
    def write_newtons4th_n4f(self, canonical_data: Dict, output_path: str) -> None:
        """Write Newtons4th .n4f binary format (emulated)."""
        with open(output_path, 'wb') as f:
            # Newtons4th header
            f.write(self.vendor_signatures['newtons4th'])
            f.write(b'\x00' * (32 - len(self.vendor_signatures['newtons4th'])))
            
            # Format identifier and version
            f.write(struct.pack('>I', 0x4E345446))  # 'N4TF' signature
            f.write(struct.pack('>H', 3))           # Version 3
            f.write(struct.pack('>H', 0))           # Subversion
            
            # Timestamp (Unix timestamp)
            timestamp = int(datetime.now().timestamp())
            f.write(struct.pack('>Q', timestamp))
            
            # Asset metadata (JSON-like structure in binary)
            frequencies = canonical_data['measurement']['frequencies']
            magnitudes = canonical_data['measurement']['magnitudes']
            phases = canonical_data['measurement'].get('phases', [0] * len(frequencies))
            
            # Measurement header
            f.write(struct.pack('>I', len(frequencies)))  # Number of points
            f.write(struct.pack('>d', frequencies[0]))    # Start frequency
            f.write(struct.pack('>d', frequencies[-1]))   # End frequency
            f.write(struct.pack('>f', canonical_data['test_info']['test_voltage']))
            
            # Connection string
            connection = canonical_data['measurement'].get('connection', 'H1-H2').encode('utf-8')[:8]
            f.write(struct.pack('>8s', connection))
            
            # Data section (Newtons4th uses double precision)
            for i in range(len(frequencies)):
                f.write(struct.pack('>d', frequencies[i]))
                f.write(struct.pack('>d', magnitudes[i]))
                f.write(struct.pack('>d', phases[i]))
            
            # Footer with metadata
            asset_json = json.dumps({
                'asset_id': canonical_data['asset_metadata']['asset_id'],
                'manufacturer': canonical_data['asset_metadata']['manufacturer'],
                'model': canonical_data['asset_metadata']['model'],
                'rating_MVA': canonical_data['asset_metadata']['rating_MVA']
            }).encode('utf-8')
            
            f.write(struct.pack('>I', len(asset_json)))
            f.write(asset_json)
    
    def read_newtons4th_n4f(self, file_path: str) -> Dict:
        """Read Newtons4th .n4f binary format (emulated)."""
        with open(file_path, 'rb') as f:
            # Verify header
            header = f.read(32)
            if not header.startswith(self.vendor_signatures['newtons4th']):
                raise ValueError("Invalid Newtons4th N4F file signature")
            
            # Read format info
            signature = struct.unpack('>I', f.read(4))[0]
            version = struct.unpack('>H', f.read(2))[0]
            subversion = struct.unpack('>H', f.read(2))[0]
            
            # Read timestamp
            timestamp = struct.unpack('>Q', f.read(8))[0]
            test_date = datetime.fromtimestamp(timestamp).isoformat()
            
            # Read measurement header
            num_points = struct.unpack('>I', f.read(4))[0]
            freq_start = struct.unpack('>d', f.read(8))[0]
            freq_end = struct.unpack('>d', f.read(8))[0]
            test_voltage = struct.unpack('>f', f.read(4))[0]
            connection = struct.unpack('>8s', f.read(8))[0].decode('utf-8').rstrip('\x00')
            
            # Read measurement data
            frequencies = []
            magnitudes = []
            phases = []
            
            for _ in range(num_points):
                freq = struct.unpack('>d', f.read(8))[0]
                mag = struct.unpack('>d', f.read(8))[0]
                phase = struct.unpack('>d', f.read(8))[0]
                
                frequencies.append(freq)
                magnitudes.append(mag)
                phases.append(phase)
            
            # Read footer metadata
            metadata_len = struct.unpack('>I', f.read(4))[0]
            metadata_json = f.read(metadata_len).decode('utf-8')
            metadata = json.loads(metadata_json)
        
        return {
            "asset_metadata": {
                "asset_id": metadata.get('asset_id', 'unknown'),
                "manufacturer": metadata.get('manufacturer', 'unknown'),
                "model": metadata.get('model', 'unknown'),
                "rating_MVA": metadata.get('rating_MVA', 100),
                "winding_config": "unknown",
                "serial": "unknown",
                "year_installed": 2020,
                "voltage_levels": [132, 33]
            },
            "test_info": {
                "test_id": f"n4th_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "date": test_date,
                "technician": "unknown",
                "instrument": "Newtons4th Analyzer V3",
                "test_voltage": test_voltage,
                "coupling": "capacitive",
                "ambient_temp": 25.0
            },
            "measurement": {
                "frequencies": frequencies,
                "magnitudes": magnitudes,
                "phases": phases,
                "unit": "dB",
                "connection": connection,
                "resolution": num_points,
                "freq_start": freq_start,
                "freq_end": freq_end
            },
            "raw_file": {
                "filename": Path(file_path).name,
                "vendor_name": "newtons4th",
                "original_format": "binary",
                "file_size": Path(file_path).stat().st_size,
                "parser_version": "1.0"
            }
        }
    
    def write_file(self, canonical_data: Dict, vendor: str, output_path: str) -> None:
        """Write binary file in specified vendor format."""
        if vendor == 'omicron':
            self.write_omicron_frx(canonical_data, output_path)
        elif vendor == 'doble':
            self.write_doble_dbl(canonical_data, output_path)
        elif vendor == 'megger':
            self.write_megger_meg(canonical_data, output_path)
        elif vendor == 'newtons4th':
            self.write_newtons4th_n4f(canonical_data, output_path)
        else:
            raise ValueError(f"Unsupported vendor format: {vendor}")
    
    def read_file(self, file_path: str) -> Dict:
        """Auto-detect and read binary file format."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Binary file not found: {file_path}")
        
        # Try to detect format by extension first
        extension = file_path.suffix.lower()
        vendor = None
        for v, ext in self.format_extensions.items():
            if extension == ext:
                vendor = v
                break
        
        # If no extension match, try reading header signatures
        if vendor is None:
            with open(file_path, 'rb') as f:
                header = f.read(64)
                for v, sig in self.vendor_signatures.items():
                    if sig in header:
                        vendor = v
                        break
        
        if vendor is None:
            raise ValueError(f"Could not detect binary format for file: {file_path}")
        
        # Parse with appropriate reader
        if vendor == 'omicron':
            return self.read_omicron_frx(str(file_path))
        elif vendor == 'doble':
            return self.read_doble_dbl(str(file_path))
        elif vendor == 'megger':
            return self.read_megger_meg(str(file_path))
        elif vendor == 'newtons4th':
            return self.read_newtons4th_n4f(str(file_path))
        else:
            raise ValueError(f"Unsupported vendor format: {vendor}")


# Test function
def test_proprietary_formats():
    """Test all proprietary format emulators."""
    emulator = ProprietaryFormatEmulator()
    
    # Create test canonical data
    test_data = {
        "asset_metadata": {
            "asset_id": "TR_TEST_001",
            "manufacturer": "Test Manufacturer",
            "model": "Test Model 500MVA",
            "rating_MVA": 500,
            "winding_config": "Dyn11",
            "serial": "SN123456",
            "year_installed": 2022,
            "voltage_levels": [400, 132]
        },
        "test_info": {
            "test_id": "TEST_20240115_001",
            "date": "2024-01-15T14:30:00Z",
            "technician": "John Smith",
            "instrument": "Test Analyzer",
            "test_voltage": 1200,
            "coupling": "capacitive",
            "ambient_temp": 23.5
        },
        "measurement": {
            "frequencies": [20000, 50000, 100000, 200000, 500000, 1000000, 2000000, 5000000, 10000000],
            "magnitudes": [45.2, 42.1, 38.9, 34.2, 28.1, 20.8, 12.1, 2.1, -8.9],
            "phases": [5.1, 3.2, 1.2, -2.1, -7.8, -18.5, -38.9, -78.5, -118.2],
            "unit": "dB",
            "connection": "H1-H2",
            "resolution": 9,
            "freq_start": 20000,
            "freq_end": 10000000
        },
        "raw_file": {
            "filename": "test.bin",
            "vendor_name": "generic",
            "original_format": "binary",
            "file_size": 0,
            "parser_version": "1.0"
        }
    }
    
    vendors = ['omicron', 'doble', 'megger', 'newtons4th']
    
    for vendor in vendors:
        try:
            # Get appropriate extension
            extension = emulator.format_extensions[vendor]
            test_file = f"/tmp/test_{vendor}{extension}"
            
            # Write file
            emulator.write_file(test_data, vendor, test_file)
            print(f"✓ {vendor.upper()} binary write successful")
            
            # Read file back
            parsed_data = emulator.read_file(test_file)
            print(f"✓ {vendor.upper()} binary read successful")
            
            # Basic validation
            assert parsed_data['asset_metadata']['asset_id'] == test_data['asset_metadata']['asset_id']
            assert len(parsed_data['measurement']['frequencies']) == len(test_data['measurement']['frequencies'])
            
            # Cleanup
            Path(test_file).unlink()
            
        except Exception as e:
            print(f"✗ {vendor.upper()} binary test failed: {e}")
    
    print("Proprietary format emulator tests completed!")


if __name__ == "__main__":
    test_proprietary_formats()
