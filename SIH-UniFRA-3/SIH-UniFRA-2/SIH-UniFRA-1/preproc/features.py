#!/usr/bin/env python3
"""
FRA Feature Extraction

Extracts engineered features from FRA data for ML analysis.
Includes frequency-domain, statistical, and domain-specific features.
"""

import numpy as np
from scipy import signal, stats
from sklearn.preprocessing import StandardScaler
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class FRAFeatureExtractor:
    """Extracts various features from FRA measurement data."""
    
    def __init__(self):
        # Define standard frequency bands for analysis
        self.frequency_bands = {
            'low': (20e3, 100e3),      # 20-100 kHz
            'mid_low': (100e3, 500e3), # 100-500 kHz
            'mid': (500e3, 2e6),       # 500 kHz - 2 MHz
            'mid_high': (2e6, 5e6),    # 2-5 MHz
            'high': (5e6, 12e6)        # 5-12 MHz
        }
        
        # Peak detection parameters
        self.peak_prominence = 2.0  # dB
        self.peak_width = 5        # Points
        
    def extract_band_energy_ratios(self, frequencies: np.ndarray, 
                                  magnitudes: np.ndarray) -> Dict[str, float]:
        """Calculate energy ratios across frequency bands.
        
        Args:
            frequencies: Frequency points (Hz)
            magnitudes: Magnitude values (dB)
            
        Returns:
            Dictionary of band energy ratios
        """
        # Convert dB to linear for energy calculation
        linear_magnitudes = 10**(magnitudes / 20)
        
        band_energies = {}
        
        for band_name, (f_min, f_max) in self.frequency_bands.items():
            # Find indices in frequency band
            band_mask = (frequencies >= f_min) & (frequencies <= f_max)
            
            if np.any(band_mask):
                # Calculate energy in band (sum of squared magnitudes)
                band_energy = np.sum(linear_magnitudes[band_mask]**2)
                band_energies[band_name] = band_energy
            else:
                band_energies[band_name] = 0.0
        
        # Calculate total energy
        total_energy = sum(band_energies.values())
        
        # Calculate energy ratios
        energy_ratios = {}
        for band_name, energy in band_energies.items():
            ratio = energy / total_energy if total_energy > 0 else 0.0
            energy_ratios[f'energy_ratio_{band_name}'] = ratio
        
        # Calculate cross-band ratios
        if band_energies['low'] > 0 and band_energies['high'] > 0:
            energy_ratios['low_to_high_ratio'] = band_energies['low'] / band_energies['high']
        else:
            energy_ratios['low_to_high_ratio'] = 0.0
            
        if band_energies['mid'] > 0 and band_energies['high'] > 0:
            energy_ratios['mid_to_high_ratio'] = band_energies['mid'] / band_energies['high']
        else:
            energy_ratios['mid_to_high_ratio'] = 0.0
        
        return energy_ratios
    
    def find_resonance_peaks(self, frequencies: np.ndarray, 
                            magnitudes: np.ndarray) -> Dict[str, List[float]]:
        """Detect resonance peaks and extract their characteristics.
        
        Args:
            frequencies: Frequency points (Hz)
            magnitudes: Magnitude values (dB)
            
        Returns:
            Dictionary of peak characteristics
        """
        try:
            # Find peaks with minimum prominence and width
            peaks, properties = signal.find_peaks(
                magnitudes,
                prominence=self.peak_prominence,
                width=self.peak_width
            )
            
            peak_features = {
                'num_peaks': len(peaks),
                'peak_frequencies': [],
                'peak_magnitudes': [],
                'peak_prominences': [],
                'peak_widths': []
            }
            
            if len(peaks) > 0:
                peak_features['peak_frequencies'] = frequencies[peaks].tolist()
                peak_features['peak_magnitudes'] = magnitudes[peaks].tolist()
                peak_features['peak_prominences'] = properties['prominences'].tolist()
                peak_features['peak_widths'] = properties['widths'].tolist()
                
                # Calculate peak statistics
                peak_features['mean_peak_frequency'] = np.mean(frequencies[peaks])
                peak_features['std_peak_frequency'] = np.std(frequencies[peaks])
                peak_features['max_peak_magnitude'] = np.max(magnitudes[peaks])
                peak_features['mean_peak_prominence'] = np.mean(properties['prominences'])
            else:
                # No peaks found
                peak_features.update({
                    'mean_peak_frequency': 0.0,
                    'std_peak_frequency': 0.0,
                    'max_peak_magnitude': 0.0,
                    'mean_peak_prominence': 0.0
                })
            
        except Exception as e:
            logger.warning(f"Peak detection failed: {e}")
            peak_features = {
                'num_peaks': 0,
                'peak_frequencies': [],
                'peak_magnitudes': [],
                'peak_prominences': [],
                'peak_widths': [],
                'mean_peak_frequency': 0.0,
                'std_peak_frequency': 0.0,
                'max_peak_magnitude': 0.0,
                'mean_peak_prominence': 0.0
            }
        
        return peak_features
    
    def calculate_slope_indices(self, frequencies: np.ndarray, 
                               magnitudes: np.ndarray) -> Dict[str, float]:
        """Calculate slope characteristics in different frequency bands.
        
        Args:
            frequencies: Frequency points (Hz)
            magnitudes: Magnitude values (dB)
            
        Returns:
            Dictionary of slope indices
        """
        log_frequencies = np.log10(frequencies)
        slope_features = {}
        
        for band_name, (f_min, f_max) in self.frequency_bands.items():
            band_mask = (frequencies >= f_min) & (frequencies <= f_max)
            
            if np.sum(band_mask) >= 3:  # Need at least 3 points for slope calculation
                band_log_freq = log_frequencies[band_mask]
                band_magnitudes = magnitudes[band_mask]
                
                # Linear regression to find slope
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    band_log_freq, band_magnitudes
                )
                
                slope_features[f'slope_{band_name}'] = slope
                slope_features[f'slope_r2_{band_name}'] = r_value**2
                slope_features[f'slope_std_err_{band_name}'] = std_err
            else:
                slope_features[f'slope_{band_name}'] = 0.0
                slope_features[f'slope_r2_{band_name}'] = 0.0
                slope_features[f'slope_std_err_{band_name}'] = 0.0
        
        # Overall slope across entire frequency range
        if len(log_frequencies) >= 3:
            overall_slope, _, overall_r2, _, _ = stats.linregress(log_frequencies, magnitudes)
            slope_features['overall_slope'] = overall_slope
            slope_features['overall_slope_r2'] = overall_r2**2
        else:
            slope_features['overall_slope'] = 0.0
            slope_features['overall_slope_r2'] = 0.0
        
        return slope_features
    
    def calculate_statistical_features(self, magnitudes: np.ndarray, 
                                     phases: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Calculate statistical features from magnitude and phase data.
        
        Args:
            magnitudes: Magnitude values
            phases: Phase values (optional)
            
        Returns:
            Dictionary of statistical features
        """
        stat_features = {}
        
        # Magnitude statistics
        stat_features['mag_mean'] = np.mean(magnitudes)
        stat_features['mag_std'] = np.std(magnitudes)
        stat_features['mag_var'] = np.var(magnitudes)
        stat_features['mag_skewness'] = stats.skew(magnitudes)
        stat_features['mag_kurtosis'] = stats.kurtosis(magnitudes)
        stat_features['mag_min'] = np.min(magnitudes)
        stat_features['mag_max'] = np.max(magnitudes)
        stat_features['mag_range'] = stat_features['mag_max'] - stat_features['mag_min']
        stat_features['mag_q25'] = np.percentile(magnitudes, 25)
        stat_features['mag_q75'] = np.percentile(magnitudes, 75)
        stat_features['mag_iqr'] = stat_features['mag_q75'] - stat_features['mag_q25']
        
        # Magnitude first and second derivatives (smoothness indicators)
        mag_diff1 = np.diff(magnitudes)
        mag_diff2 = np.diff(magnitudes, n=2)
        
        stat_features['mag_diff1_mean'] = np.mean(np.abs(mag_diff1))
        stat_features['mag_diff1_std'] = np.std(mag_diff1)
        stat_features['mag_diff2_mean'] = np.mean(np.abs(mag_diff2))
        stat_features['mag_diff2_std'] = np.std(mag_diff2)
        
        # Phase statistics (if available)
        if phases is not None:
            # Unwrap phases for better statistics
            unwrapped_phases = np.unwrap(np.radians(phases))
            
            stat_features['phase_mean'] = np.mean(unwrapped_phases)
            stat_features['phase_std'] = np.std(unwrapped_phases)
            stat_features['phase_var'] = np.var(unwrapped_phases)
            stat_features['phase_skewness'] = stats.skew(unwrapped_phases)
            stat_features['phase_kurtosis'] = stats.kurtosis(unwrapped_phases)
            stat_features['phase_range'] = np.max(unwrapped_phases) - np.min(unwrapped_phases)
            
            # Phase derivatives
            phase_diff1 = np.diff(unwrapped_phases)
            stat_features['phase_diff1_mean'] = np.mean(np.abs(phase_diff1))
            stat_features['phase_diff1_std'] = np.std(phase_diff1)
        else:
            # Set phase features to zero if not available
            phase_keys = ['phase_mean', 'phase_std', 'phase_var', 'phase_skewness', 
                         'phase_kurtosis', 'phase_range', 'phase_diff1_mean', 'phase_diff1_std']
            for key in phase_keys:
                stat_features[key] = 0.0
        
        return stat_features
    
    def calculate_spectral_features(self, frequencies: np.ndarray, 
                                   magnitudes: np.ndarray) -> Dict[str, float]:
        """Calculate spectral features like centroid, bandwidth, etc.
        
        Args:
            frequencies: Frequency points (Hz)
            magnitudes: Magnitude values (dB)
            
        Returns:
            Dictionary of spectral features
        """
        # Convert to linear scale for spectral calculations
        linear_magnitudes = 10**(magnitudes / 20)
        
        # Normalize to create probability distribution
        power_sum = np.sum(linear_magnitudes**2)
        if power_sum > 0:
            normalized_power = (linear_magnitudes**2) / power_sum
        else:
            normalized_power = np.ones_like(linear_magnitudes) / len(linear_magnitudes)
        
        spectral_features = {}
        
        # Spectral centroid (center of mass)
        spectral_features['spectral_centroid'] = np.sum(frequencies * normalized_power)
        
        # Spectral spread (second moment)
        centroid = spectral_features['spectral_centroid']
        spectral_features['spectral_spread'] = np.sqrt(
            np.sum(((frequencies - centroid)**2) * normalized_power)
        )
        
        # Spectral skewness (third moment)
        if spectral_features['spectral_spread'] > 0:
            spectral_features['spectral_skewness'] = (
                np.sum(((frequencies - centroid)**3) * normalized_power) / 
                (spectral_features['spectral_spread']**3)
            )
        else:
            spectral_features['spectral_skewness'] = 0.0
        
        # Spectral kurtosis (fourth moment)
        if spectral_features['spectral_spread'] > 0:
            spectral_features['spectral_kurtosis'] = (
                np.sum(((frequencies - centroid)**4) * normalized_power) / 
                (spectral_features['spectral_spread']**4)
            )
        else:
            spectral_features['spectral_kurtosis'] = 0.0
        
        # Spectral rolloff (frequency below which 85% of energy is contained)
        cumulative_power = np.cumsum(normalized_power)
        rolloff_idx = np.where(cumulative_power >= 0.85)[0]
        if len(rolloff_idx) > 0:
            spectral_features['spectral_rolloff'] = frequencies[rolloff_idx[0]]
        else:
            spectral_features['spectral_rolloff'] = frequencies[-1]
        
        # Zero crossing rate in magnitude (indication of oscillations)
        mag_centered = magnitudes - np.mean(magnitudes)
        zero_crossings = np.sum(np.diff(np.signbit(mag_centered)))
        spectral_features['zero_crossing_rate'] = zero_crossings / len(magnitudes)
        
        return spectral_features
    
    def extract_all_features(self, processed_data: Dict) -> Dict[str, float]:
        """Extract complete feature set from processed FRA data.
        
        Args:
            processed_data: Processed FRA data from normalizer
            
        Returns:
            Dictionary containing all extracted features
        """
        measurement = processed_data['measurement']
        
        frequencies = np.array(measurement['frequencies'])
        magnitudes = np.array(measurement['magnitudes'])
        phases = np.array(measurement.get('phases', []))
        
        if len(phases) == 0:
            phases = None
        
        # Extract all feature categories
        features = {}
        
        try:
            # Band energy ratios
            energy_features = self.extract_band_energy_ratios(frequencies, magnitudes)
            features.update(energy_features)
            
            # Peak characteristics
            peak_features = self.find_resonance_peaks(frequencies, magnitudes)
            # Only include scalar features (not lists)
            scalar_peak_features = {
                k: v for k, v in peak_features.items() 
                if not isinstance(v, list)
            }
            features.update(scalar_peak_features)
            
            # Slope indices
            slope_features = self.calculate_slope_indices(frequencies, magnitudes)
            features.update(slope_features)
            
            # Statistical features
            stat_features = self.calculate_statistical_features(magnitudes, phases)
            features.update(stat_features)
            
            # Spectral features
            spectral_features = self.calculate_spectral_features(frequencies, magnitudes)
            features.update(spectral_features)
            
            # Asset-specific features (if available)
            if 'asset_metadata' in processed_data:
                asset_meta = processed_data['asset_metadata']
                features['transformer_rating_mva'] = asset_meta.get('rating_MVA', 100)
                
                # Encode winding configuration
                winding_config = asset_meta.get('winding_config', 'unknown')
                features['is_dyn_winding'] = 1.0 if 'dyn' in winding_config.lower() else 0.0
                features['is_ynyn_winding'] = 1.0 if 'ynyn' in winding_config.lower() else 0.0
            
            # Test condition features
            if 'test_info' in processed_data:
                test_info = processed_data['test_info']
                features['test_voltage'] = test_info.get('test_voltage', 1000)
                features['ambient_temperature'] = test_info.get('ambient_temp', 25.0)
                
                # Coupling type
                coupling = test_info.get('coupling', 'capacitive')
                features['is_capacitive_coupling'] = 1.0 if coupling == 'capacitive' else 0.0
            
            logger.info(f"Extracted {len(features)} features from FRA data")
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return empty features dict on failure
            features = {}
        
        return features
    
    def create_feature_matrix(self, dataset_samples: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        """Create feature matrix from multiple FRA samples.
        
        Args:
            dataset_samples: List of processed FRA data samples
            
        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        all_features = []
        feature_names = None
        
        for i, sample in enumerate(dataset_samples):
            try:
                sample_features = self.extract_all_features(sample)
                
                if feature_names is None:
                    feature_names = sorted(sample_features.keys())
                
                # Create feature vector in consistent order
                feature_vector = [sample_features.get(name, 0.0) for name in feature_names]
                all_features.append(feature_vector)
                
            except Exception as e:
                logger.warning(f"Failed to extract features from sample {i}: {e}")
                # Skip this sample
                continue
        
        if not all_features:
            raise ValueError("No features could be extracted from dataset")
        
        feature_matrix = np.array(all_features)
        
        logger.info(f"Created feature matrix: {feature_matrix.shape} (samples x features)")
        
        return feature_matrix, feature_names


# Test function
def test_feature_extractor():
    """Test feature extraction with sample data."""
    from .normalize import test_normalizer
    
    # Get normalized test data
    processed_data = test_normalizer()
    
    if processed_data is None:
        print("✗ Could not get processed data for feature extraction test")
        return None
    
    extractor = FRAFeatureExtractor()
    
    try:
        # Extract features
        features = extractor.extract_all_features(processed_data)
        
        print(f"\nFRA Feature Extraction Test Results:")
        print(f"✓ Total features extracted: {len(features)}")
        
        # Display feature categories
        energy_features = {k: v for k, v in features.items() if 'energy' in k}
        peak_features = {k: v for k, v in features.items() if 'peak' in k}
        slope_features = {k: v for k, v in features.items() if 'slope' in k}
        stat_features = {k: v for k, v in features.items() if any(x in k for x in ['mean', 'std', 'skew', 'kurt'])}
        spectral_features = {k: v for k, v in features.items() if 'spectral' in k}
        
        print(f"✓ Energy features: {len(energy_features)}")
        print(f"✓ Peak features: {len(peak_features)}")
        print(f"✓ Slope features: {len(slope_features)}")
        print(f"✓ Statistical features: {len(stat_features)}")
        print(f"✓ Spectral features: {len(spectral_features)}")
        
        # Show sample features
        print("\nSample features:")
        for i, (key, value) in enumerate(list(features.items())[:10]):
            print(f"  {key}: {value:.4f}")
        
        return features
        
    except Exception as e:
        print(f"✗ Feature extraction test failed: {e}")
        return None


if __name__ == "__main__":
    test_feature_extractor()
