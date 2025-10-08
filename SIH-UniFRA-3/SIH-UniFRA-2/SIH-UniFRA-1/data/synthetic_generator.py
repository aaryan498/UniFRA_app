#!/usr/bin/env python3
"""
Synthetic FRA Data Generator

Generates labeled synthetic Frequency Response Analysis (FRA) data for training ML models.
Creates realistic FRA signatures with various fault types, severities, and noise conditions.

Supported fault types:
- axial_displacement
- radial_deformation  
- core_grounding
- turn_turn_short
- open_circuit
- insulation_degradation
- partial_discharge
- lamination_deform
- saturation_effect
- healthy (baseline)
"""

import numpy as np
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import uuid
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FaultType(Enum):
    """Enumeration of transformer fault types."""
    HEALTHY = "healthy"
    AXIAL_DISPLACEMENT = "axial_displacement"
    RADIAL_DEFORMATION = "radial_deformation"
    CORE_GROUNDING = "core_grounding"
    TURN_TURN_SHORT = "turn_turn_short"
    OPEN_CIRCUIT = "open_circuit"
    INSULATION_DEGRADATION = "insulation_degradation"
    PARTIAL_DISCHARGE = "partial_discharge"
    LAMINATION_DEFORM = "lamination_deform"
    SATURATION_EFFECT = "saturation_effect"

class SeverityLevel(Enum):
    """Fault severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

@dataclass
class TransformerSpec:
    """Transformer specification for synthetic generation."""
    rating_mva: float
    voltage_hv: float
    voltage_lv: float
    winding_config: str
    manufacturer: str
    model: str
    year_installed: int

class SyntheticFRAGenerator:
    """Generator for synthetic FRA data with realistic fault patterns."""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Standard frequency range for FRA: 20 Hz to 12 MHz
        self.freq_min = 20e3   # 20 kHz
        self.freq_max = 12e6   # 12 MHz
        self.num_points = 2048  # Standard resolution
        
        # Transformer specifications database
        self.transformer_specs = [
            TransformerSpec(100, 132, 33, "Dyn11", "ABB", "TDOC 100MVA", 2015),
            TransformerSpec(200, 220, 66, "YNyn0", "Siemens", "GEAFOL 200MVA", 2018),
            TransformerSpec(300, 400, 132, "Dyn11", "Schneider", "Trihal 300MVA", 2020),
            TransformerSpec(500, 500, 220, "YNyn0", "BHEL", "Power 500MVA", 2016),
            TransformerSpec(150, 220, 33, "Dyn1", "Crompton", "Distribution 150MVA", 2019),
            TransformerSpec(80, 132, 11, "Dyn11", "Kirloskar", "Compact 80MVA", 2021),
        ]
        
        # Test instrument specifications
        self.instruments = [
            "Omicron FRAnalyzer",
            "Doble M4000", 
            "Megger FRAX-150",
            "Newtons4th N4A",
            "Raytech FRAT-500",
            "Phenix FRAX-101"
        ]
        
        # Fault signature parameters (frequency-dependent effects)
        self.fault_signatures = {
            FaultType.HEALTHY: {
                'resonance_shifts': [0, 0, 0],  # No shifts
                'magnitude_changes': [0, 0, 0],  # No changes
                'phase_distortions': [0, 0, 0],  # No distortions
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.AXIAL_DISPLACEMENT: {
                'resonance_shifts': [0.1, 0.2, 0.05],  # Low, mid, high freq shifts
                'magnitude_changes': [-2, -5, -1],      # dB changes per band
                'phase_distortions': [2, 5, 1],         # Phase shift degrees
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.RADIAL_DEFORMATION: {
                'resonance_shifts': [0.05, 0.3, 0.1],
                'magnitude_changes': [-1, -8, -3],
                'phase_distortions': [1, 8, 3],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.CORE_GROUNDING: {
                'resonance_shifts': [0.2, 0.1, 0.02],
                'magnitude_changes': [-5, -3, -0.5],
                'phase_distortions': [8, 3, 0.5],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.TURN_TURN_SHORT: {
                'resonance_shifts': [0.15, 0.4, 0.2],
                'magnitude_changes': [-3, -12, -6],
                'phase_distortions': [5, 15, 8],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.OPEN_CIRCUIT: {
                'resonance_shifts': [0.05, 0.6, 0.4],
                'magnitude_changes': [-1, -20, -15],
                'phase_distortions': [2, 30, 25],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.INSULATION_DEGRADATION: {
                'resonance_shifts': [0.08, 0.12, 0.25],
                'magnitude_changes': [-2, -4, -8],
                'phase_distortions': [3, 6, 12],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.PARTIAL_DISCHARGE: {
                'resonance_shifts': [0.02, 0.08, 0.3], 
                'magnitude_changes': [-0.5, -2, -10],
                'phase_distortions': [1, 4, 18],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.LAMINATION_DEFORM: {
                'resonance_shifts': [0.3, 0.15, 0.05],
                'magnitude_changes': [-8, -4, -1],
                'phase_distortions': [12, 6, 2],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            },
            FaultType.SATURATION_EFFECT: {
                'resonance_shifts': [0.25, 0.1, 0.03],
                'magnitude_changes': [-6, -2, -0.5],
                'phase_distortions': [10, 4, 1],
                'frequency_bands': [(20e3, 1e5), (1e5, 1e6), (1e6, 12e6)]
            }
        }
    
    def generate_base_fra_signature(self, transformer_spec: TransformerSpec) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate base healthy FRA signature for a transformer.
        
        Returns:
            Tuple of (frequencies, magnitudes, phases)
        """
        # Generate logarithmic frequency sweep
        frequencies = np.logspace(np.log10(self.freq_min), np.log10(self.freq_max), self.num_points)
        
        # Base magnitude response (typical transformer characteristic)
        # Higher frequencies have lower magnitude (capacitive coupling dominance)
        log_freq = np.log10(frequencies)
        
        # Resonance peaks at characteristic frequencies based on transformer size
        resonance_freqs = [
            50e3 * (100 / transformer_spec.rating_mva)**0.3,   # Low freq resonance
            500e3 * (100 / transformer_spec.rating_mva)**0.2,  # Mid freq resonance
            3e6 * (100 / transformer_spec.rating_mva)**0.1     # High freq resonance
        ]
        
        # Base magnitude curve (starts high, decreases with frequency)
        base_magnitude = 50 - 8 * (log_freq - np.log10(self.freq_min))
        
        # Add resonance peaks
        for i, res_freq in enumerate(resonance_freqs):
            # Gaussian resonance peak
            peak_width = 0.3 + 0.1 * i  # Wider peaks at higher frequencies
            peak_height = 8 - 2 * i      # Lower peaks at higher frequencies
            
            resonance_curve = peak_height * np.exp(-((log_freq - np.log10(res_freq)) / peak_width)**2)
            base_magnitude += resonance_curve
        
        # Add transformer-specific variations
        if "Dyn" in transformer_spec.winding_config:
            # Delta-wye transformers have different characteristics
            base_magnitude += 2 * np.sin(0.5 * log_freq)
        
        # Phase response (starts positive, becomes increasingly negative)
        base_phase = 10 - 15 * (log_freq - np.log10(self.freq_min))
        
        # Add phase resonances
        for i, res_freq in enumerate(resonance_freqs):
            phase_shift = (20 - 5 * i) * np.exp(-((log_freq - np.log10(res_freq)) / 0.2)**2)
            base_phase += phase_shift
        
        return frequencies, base_magnitude, base_phase
    
    def apply_fault_signature(self, frequencies: np.ndarray, magnitudes: np.ndarray, phases: np.ndarray,
                            fault_type: FaultType, severity: SeverityLevel) -> Tuple[np.ndarray, np.ndarray]:
        """Apply fault-specific signatures to base FRA response.
        
        Returns:
            Tuple of (modified_magnitudes, modified_phases)
        """
        if fault_type == FaultType.HEALTHY:
            return magnitudes.copy(), phases.copy()
        
        signature = self.fault_signatures[fault_type]
        
        # Severity multipliers
        severity_multipliers = {
            SeverityLevel.MILD: 0.3,
            SeverityLevel.MODERATE: 0.7, 
            SeverityLevel.SEVERE: 1.0
        }
        
        severity_mult = severity_multipliers[severity]
        
        modified_magnitudes = magnitudes.copy()
        modified_phases = phases.copy()
        
        log_freq = np.log10(frequencies)
        
        # Apply frequency-band-specific effects
        for i, (f_start, f_end) in enumerate(signature['frequency_bands']):
            # Create frequency band mask
            band_mask = (frequencies >= f_start) & (frequencies <= f_end)
            
            if not np.any(band_mask):
                continue
            
            # Apply resonance shifts
            resonance_shift = signature['resonance_shifts'][i] * severity_mult
            if resonance_shift != 0:
                # Shift resonance frequency (simulate mechanical displacement)
                shift_factor = 1 + resonance_shift * 0.1
                freq_shift_mask = band_mask
                modified_magnitudes[freq_shift_mask] += resonance_shift * np.sin(2 * np.pi * log_freq[freq_shift_mask])
            
            # Apply magnitude changes
            mag_change = signature['magnitude_changes'][i] * severity_mult
            modified_magnitudes[band_mask] += mag_change
            
            # Apply phase distortions
            phase_change = signature['phase_distortions'][i] * severity_mult
            modified_phases[band_mask] += phase_change
        
        return modified_magnitudes, modified_phases
    
    def add_noise(self, magnitudes: np.ndarray, phases: np.ndarray, 
                 noise_level: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """Add realistic measurement noise to FRA data.
        
        Args:
            magnitudes: Magnitude values in dB
            phases: Phase values in degrees
            noise_level: Noise level (0.0 to 1.0)
            
        Returns:
            Tuple of (noisy_magnitudes, noisy_phases)
        """
        # Gaussian noise for magnitudes (typical ±0.1 dB measurement uncertainty)
        mag_noise_std = 0.1 * noise_level
        magnitude_noise = np.random.normal(0, mag_noise_std, len(magnitudes))
        
        # Gaussian noise for phases (typical ±0.5° measurement uncertainty) 
        phase_noise_std = 0.5 * noise_level
        phase_noise = np.random.normal(0, phase_noise_std, len(phases))
        
        # Add 1/f noise component (more realistic for electronic instruments)
        freq_noise_factor = np.sqrt(1.0 / np.arange(1, len(magnitudes) + 1))
        mag_1f_noise = 0.05 * noise_level * freq_noise_factor * np.random.normal(0, 1, len(magnitudes))
        phase_1f_noise = 0.2 * noise_level * freq_noise_factor * np.random.normal(0, 1, len(phases))
        
        noisy_magnitudes = magnitudes + magnitude_noise + mag_1f_noise
        noisy_phases = phases + phase_noise + phase_1f_noise
        
        return noisy_magnitudes, noisy_phases
    
    def generate_sample(self, fault_type: Optional[FaultType] = None, 
                       severity: Optional[SeverityLevel] = None,
                       transformer_spec: Optional[TransformerSpec] = None,
                       noise_level: float = 0.2) -> Dict:
        """Generate a single synthetic FRA sample.
        
        Args:
            fault_type: Type of fault to simulate (random if None)
            severity: Fault severity (random if None) 
            transformer_spec: Transformer specification (random if None)
            noise_level: Measurement noise level (0.0 to 1.0)
            
        Returns:
            Dict: Canonical FRA data structure with fault labels
        """
        # Random selections if not specified
        if fault_type is None:
            fault_type = random.choice(list(FaultType))
        
        if severity is None:
            severity = random.choice(list(SeverityLevel))
        
        if transformer_spec is None:
            transformer_spec = random.choice(self.transformer_specs)
        
        # Generate base signature
        frequencies, base_magnitudes, base_phases = self.generate_base_fra_signature(transformer_spec)
        
        # Apply fault signature
        magnitudes, phases = self.apply_fault_signature(
            frequencies, base_magnitudes, base_phases, fault_type, severity
        )
        
        # Add measurement noise
        magnitudes, phases = self.add_noise(magnitudes, phases, noise_level)
        
        # Generate random test metadata
        test_date = datetime.now() - timedelta(days=random.randint(0, 365*3))
        technician_names = ["John Smith", "Maria Garcia", "David Johnson", "Lisa Wang", "Ahmed Hassan"]
        
        # Create canonical data structure
        sample_data = {
            "asset_metadata": {
                "asset_id": f"TR_{transformer_spec.manufacturer[:3].upper()}_{random.randint(1000, 9999)}",
                "manufacturer": transformer_spec.manufacturer,
                "model": transformer_spec.model,
                "rating_MVA": transformer_spec.rating_mva,
                "winding_config": transformer_spec.winding_config,
                "serial": f"SN{random.randint(100000, 999999)}",
                "year_installed": transformer_spec.year_installed,
                "voltage_levels": [transformer_spec.voltage_hv, transformer_spec.voltage_lv]
            },
            "test_info": {
                "test_id": f"FRA_{test_date.strftime('%Y%m%d')}_{random.randint(100, 999)}",
                "date": test_date.isoformat(),
                "technician": random.choice(technician_names),
                "instrument": random.choice(self.instruments),
                "test_voltage": random.choice([800, 1000, 1200, 1500]),
                "coupling": random.choice(["capacitive", "inductive"]),
                "ambient_temp": round(random.uniform(15, 35), 1)
            },
            "measurement": {
                "frequencies": frequencies.tolist(),
                "magnitudes": magnitudes.tolist(),
                "phases": phases.tolist(),
                "unit": "dB",
                "phase_unit": "degrees",
                "connection": random.choice(["H1-H2", "H1-X1", "H2-X2", "X1-X2"]),
                "resolution": len(frequencies),
                "freq_start": float(frequencies[0]),
                "freq_end": float(frequencies[-1])
            },
            "raw_file": {
                "filename": f"synthetic_{fault_type.value}_{severity.value}_{uuid.uuid4().hex[:8]}.json",
                "vendor_name": "synthetic",
                "original_format": "json",
                "file_size": 0,  # Will be calculated when saved
                "parser_version": "1.0"
            },
            # Ground truth labels for ML training
            "fault_labels": {
                "fault_type": fault_type.value,
                "severity_level": severity.value,
                "is_faulty": fault_type != FaultType.HEALTHY,
                "fault_confidence": 1.0,  # Perfect labels for synthetic data
                "generation_params": {
                    "noise_level": noise_level,
                    "transformer_rating": transformer_spec.rating_mva,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
        }
        
        return sample_data
    
    def generate_dataset(self, num_samples: int = 3000, 
                        output_dir: str = "/app/data/synthetic_dataset",
                        balanced: bool = True,
                        noise_range: Tuple[float, float] = (0.05, 0.3)) -> Dict[str, int]:
        """Generate a complete synthetic FRA dataset.
        
        Args:
            num_samples: Total number of samples to generate
            output_dir: Directory to save dataset
            balanced: Whether to balance samples across fault types and severities
            noise_range: Range of noise levels to apply (min, max)
            
        Returns:
            Dict: Generation statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (output_path / "canonical").mkdir(exist_ok=True)
        (output_path / "vendor_formats").mkdir(exist_ok=True)
        
        # Calculate samples per category if balanced
        fault_types = list(FaultType)
        severity_levels = list(SeverityLevel)
        
        if balanced:
            # Ensure healthy samples are well represented (20% of dataset)
            healthy_samples = int(0.2 * num_samples)
            faulty_samples = num_samples - healthy_samples
            
            # Distribute faulty samples across fault types and severities
            samples_per_fault = faulty_samples // (len(fault_types) - 1)  # Exclude HEALTHY
            samples_per_severity = samples_per_fault // len(severity_levels)
        
        generation_stats = {
            "total_samples": 0,
            "fault_distribution": {ft.value: 0 for ft in fault_types},
            "severity_distribution": {sl.value: 0 for sl in severity_levels},
            "transformer_distribution": {}
        }
        
        logger.info(f"Generating {num_samples} synthetic FRA samples...")
        
        for i in range(num_samples):
            if i % 100 == 0:
                logger.info(f"Generated {i}/{num_samples} samples ({i/num_samples*100:.1f}%)")
            
            # Select fault type and severity
            if balanced:
                if i < healthy_samples:
                    fault_type = FaultType.HEALTHY
                    severity = SeverityLevel.MILD  # Doesn't matter for healthy
                else:
                    # Cycle through fault types and severities
                    fault_idx = ((i - healthy_samples) // samples_per_severity) % (len(fault_types) - 1)
                    severity_idx = (i - healthy_samples) % len(severity_levels)
                    
                    # Skip HEALTHY in fault_types
                    fault_type = [ft for ft in fault_types if ft != FaultType.HEALTHY][fault_idx]
                    severity = severity_levels[severity_idx]
            else:
                fault_type = random.choice(fault_types)
                severity = random.choice(severity_levels)
            
            # Random noise level
            noise_level = random.uniform(*noise_range)
            
            # Generate sample
            sample = self.generate_sample(
                fault_type=fault_type,
                severity=severity, 
                noise_level=noise_level
            )
            
            # Update statistics
            generation_stats["total_samples"] += 1
            generation_stats["fault_distribution"][fault_type.value] += 1
            generation_stats["severity_distribution"][severity.value] += 1
            
            transformer_model = sample["asset_metadata"]["model"]
            if transformer_model not in generation_stats["transformer_distribution"]:
                generation_stats["transformer_distribution"][transformer_model] = 0
            generation_stats["transformer_distribution"][transformer_model] += 1
            
            # Save canonical format
            canonical_filename = f"sample_{i:06d}_{fault_type.value}_{severity.value}.json"
            canonical_path = output_path / "canonical" / canonical_filename
            
            with open(canonical_path, 'w') as f:
                json.dump(sample, f, indent=2)
            
            # Update file size in metadata
            sample["raw_file"]["file_size"] = canonical_path.stat().st_size
            
            # Save in vendor formats (for parser testing)
            if i % 50 == 0:  # Save every 50th sample in vendor formats
                self._save_vendor_formats(sample, output_path / "vendor_formats", i)
        
        # Save generation statistics
        stats_path = output_path / "generation_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(generation_stats, f, indent=2)
        
        # Save dataset metadata
        metadata = {
            "dataset_info": {
                "name": "UniFRA Synthetic Dataset",
                "version": "1.0",
                "generated_date": datetime.now().isoformat(),
                "total_samples": num_samples,
                "frequency_range_hz": [self.freq_min, self.freq_max],
                "frequency_points": self.num_points,
                "balanced": balanced,
                "noise_range": noise_range
            },
            "fault_types": [ft.value for ft in fault_types],
            "severity_levels": [sl.value for sl in severity_levels],
            "transformer_specs": [
                {
                    "rating_mva": ts.rating_mva,
                    "voltage_hv": ts.voltage_hv,
                    "voltage_lv": ts.voltage_lv,
                    "winding_config": ts.winding_config,
                    "manufacturer": ts.manufacturer,
                    "model": ts.model
                } for ts in self.transformer_specs
            ],
            "statistics": generation_stats
        }
        
        metadata_path = output_path / "dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Dataset generation complete! Saved to {output_path}")
        logger.info(f"Statistics: {generation_stats}")
        
        return generation_stats
    
    def _save_vendor_formats(self, sample: Dict, vendor_dir: Path, sample_idx: int) -> None:
        """Save sample in various vendor formats for parser testing."""
        try:
            from ..parsers.proprietary_emulator import ProprietaryFormatEmulator
            from ..parsers.csv_parser import CSVParser
            
            emulator = ProprietaryFormatEmulator()
            
            # Save in one random vendor format
            vendors = ['omicron', 'doble', 'megger', 'newtons4th']
            selected_vendor = random.choice(vendors)
            
            vendor_filename = f"sample_{sample_idx:06d}.{emulator.format_extensions[selected_vendor][1:]}"
            vendor_path = vendor_dir / vendor_filename
            
            emulator.write_file(sample, selected_vendor, str(vendor_path))
            
        except Exception as e:
            logger.warning(f"Could not save vendor format for sample {sample_idx}: {e}")


# CLI interface
def main():
    """Command-line interface for synthetic dataset generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic FRA dataset')
    parser.add_argument('--samples', type=int, default=3000, help='Number of samples to generate')
    parser.add_argument('--output', type=str, default='/app/data/synthetic_dataset', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--balanced', action='store_true', help='Generate balanced dataset')
    parser.add_argument('--noise-min', type=float, default=0.05, help='Minimum noise level')
    parser.add_argument('--noise-max', type=float, default=0.3, help='Maximum noise level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Generate dataset
    generator = SyntheticFRAGenerator(seed=args.seed)
    stats = generator.generate_dataset(
        num_samples=args.samples,
        output_dir=args.output,
        balanced=args.balanced,
        noise_range=(args.noise_min, args.noise_max)
    )
    
    print(f"\nDataset generation completed successfully!")
    print(f"Total samples: {stats['total_samples']}")
    print(f"Fault distribution: {stats['fault_distribution']}")
    print(f"Output directory: {args.output}")


if __name__ == "__main__":
    main()
