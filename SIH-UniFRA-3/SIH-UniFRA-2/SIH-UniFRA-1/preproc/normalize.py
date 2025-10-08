#!/usr/bin/env python3
"""
FRA Data Normalization and Preprocessing

Normalizes FRA data from different sources to a common format suitable for ML analysis.
Handles resampling, filtering, and standardization.
"""

import numpy as np
from scipy import signal, interpolate
from scipy.ndimage import uniform_filter1d
import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

class FRANormalizer:
    """Normalizes and preprocesses FRA measurement data for ML analysis."""
    
    def __init__(self, target_points: int = 4096, 
                 freq_range: Tuple[float, float] = (20e3, 12e6),
                 magnitude_range: Tuple[float, float] = (-60, 60)):
        """
        Initialize FRA normalizer.
        
        Args:
            target_points: Target number of frequency points after resampling
            freq_range: Target frequency range (Hz) as (min_freq, max_freq)
            magnitude_range: Expected magnitude range (dB) for normalization
        """
        self.target_points = target_points
        self.freq_min, self.freq_max = freq_range
        self.mag_min, self.mag_max = magnitude_range
        
        # Savitzky-Golay filter parameters for smoothing
        self.sg_window = 51  # Should be odd
        self.sg_polyorder = 3
        
    def resample_to_common_grid(self, frequencies: np.ndarray, 
                               magnitudes: np.ndarray, 
                               phases: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Resample FRA data to a common frequency grid.
        
        Args:
            frequencies: Original frequency points (Hz)
            magnitudes: Magnitude values (dB)
            phases: Phase values (degrees), optional
            
        Returns:
            Tuple of (resampled_frequencies, resampled_magnitudes, resampled_phases)
        """
        # Create target frequency grid (logarithmic spacing)
        target_frequencies = np.logspace(
            np.log10(self.freq_min), 
            np.log10(self.freq_max), 
            self.target_points
        )
        
        # Ensure input frequencies are sorted
        sort_indices = np.argsort(frequencies)
        frequencies = frequencies[sort_indices]
        magnitudes = magnitudes[sort_indices]
        if phases is not None:
            phases = phases[sort_indices]
        
        # Remove duplicate frequencies
        unique_indices = np.unique(frequencies, return_index=True)[1]
        frequencies = frequencies[unique_indices]
        magnitudes = magnitudes[unique_indices]
        if phases is not None:
            phases = phases[unique_indices]
        
        # Clip to target frequency range
        valid_mask = (frequencies >= self.freq_min) & (frequencies <= self.freq_max)
        frequencies = frequencies[valid_mask]
        magnitudes = magnitudes[valid_mask]
        if phases is not None:
            phases = phases[valid_mask]
        
        if len(frequencies) < 10:
            raise ValueError("Insufficient frequency points after filtering")
        
        # Interpolate to target grid using cubic spline
        try:
            # Use log-frequency for better interpolation
            log_freq_orig = np.log10(frequencies)
            log_freq_target = np.log10(target_frequencies)
            
            # Interpolate magnitudes
            mag_interpolator = interpolate.interp1d(
                log_freq_orig, magnitudes, 
                kind='cubic', 
                bounds_error=False, 
                fill_value='extrapolate'
            )
            resampled_magnitudes = mag_interpolator(log_freq_target)
            
            # Interpolate phases if available
            resampled_phases = None
            if phases is not None:
                # Handle phase wraparound
                unwrapped_phases = np.unwrap(np.radians(phases))
                phase_interpolator = interpolate.interp1d(
                    log_freq_orig, unwrapped_phases,
                    kind='cubic',
                    bounds_error=False,
                    fill_value='extrapolate'
                )
                resampled_phases = np.degrees(phase_interpolator(log_freq_target))
            
        except Exception as e:
            logger.warning(f"Cubic interpolation failed: {e}. Using linear interpolation.")
            
            # Fallback to linear interpolation
            mag_interpolator = interpolate.interp1d(
                frequencies, magnitudes,
                kind='linear',
                bounds_error=False,
                fill_value='extrapolate'
            )
            resampled_magnitudes = mag_interpolator(target_frequencies)
            
            resampled_phases = None
            if phases is not None:
                phase_interpolator = interpolate.interp1d(
                    frequencies, phases,
                    kind='linear', 
                    bounds_error=False,
                    fill_value='extrapolate'
                )
                resampled_phases = phase_interpolator(target_frequencies)
        
        return target_frequencies, resampled_magnitudes, resampled_phases
    
    def apply_savgol_filter(self, magnitudes: np.ndarray, 
                           phases: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply Savitzky-Golay filter for smoothing.
        
        Args:
            magnitudes: Magnitude values
            phases: Phase values, optional
            
        Returns:
            Tuple of (filtered_magnitudes, filtered_phases)
        """
        # Ensure window size is appropriate
        window_size = min(self.sg_window, len(magnitudes))
        if window_size % 2 == 0:
            window_size -= 1
        window_size = max(window_size, 5)  # Minimum window size
        
        polyorder = min(self.sg_polyorder, window_size - 1)
        
        try:
            filtered_magnitudes = signal.savgol_filter(
                magnitudes, window_size, polyorder
            )
            
            filtered_phases = None
            if phases is not None:
                filtered_phases = signal.savgol_filter(
                    phases, window_size, polyorder
                )
                
        except Exception as e:
            logger.warning(f"Savitzky-Golay filtering failed: {e}. Returning original data.")
            filtered_magnitudes = magnitudes
            filtered_phases = phases
        
        return filtered_magnitudes, filtered_phases
    
    def apply_wavelet_denoising(self, magnitudes: np.ndarray, 
                               wavelet: str = 'db4', 
                               sigma: Optional[float] = None) -> np.ndarray:
        """Apply wavelet denoising to magnitude data.
        
        Args:
            magnitudes: Magnitude values
            wavelet: Wavelet type for denoising
            sigma: Noise standard deviation (estimated if None)
            
        Returns:
            Denoised magnitude values
        """
        try:
            import pywt
            
            # Estimate noise if not provided
            if sigma is None:
                # Use robust median estimator
                sigma = np.median(np.abs(np.diff(magnitudes))) / 0.6745
            
            # Wavelet decomposition
            coeffs = pywt.wavedec(magnitudes, wavelet, mode='symmetric')
            
            # Soft thresholding
            threshold = sigma * np.sqrt(2 * np.log(len(magnitudes)))
            coeffs_thresh = [pywt.threshold(c, threshold, mode='soft') for c in coeffs]
            
            # Reconstruction
            denoised = pywt.waverec(coeffs_thresh, wavelet, mode='symmetric')
            
            return denoised[:len(magnitudes)]  # Ensure same length
            
        except ImportError:
            logger.warning("PyWavelets not available. Skipping wavelet denoising.")
            return magnitudes
        except Exception as e:
            logger.warning(f"Wavelet denoising failed: {e}. Returning original data.")
            return magnitudes
    
    def normalize_magnitude(self, magnitudes: np.ndarray) -> np.ndarray:
        """Normalize magnitude values to [0, 1] range.
        
        Args:
            magnitudes: Magnitude values in dB
            
        Returns:
            Normalized magnitude values
        """
        # Clip to expected range
        clipped_magnitudes = np.clip(magnitudes, self.mag_min, self.mag_max)
        
        # Normalize to [0, 1]
        normalized = (clipped_magnitudes - self.mag_min) / (self.mag_max - self.mag_min)
        
        return normalized
    
    def normalize_phase(self, phases: np.ndarray) -> np.ndarray:
        """Normalize phase values to [-1, 1] range.
        
        Args:
            phases: Phase values in degrees
            
        Returns:
            Normalized phase values
        """
        # Wrap phases to [-180, 180] range
        wrapped_phases = np.angle(np.exp(1j * np.radians(phases)), deg=True)
        
        # Normalize to [-1, 1]
        normalized = wrapped_phases / 180.0
        
        return normalized
    
    def process_fra_data(self, canonical_data: Dict, 
                        apply_filtering: bool = True,
                        apply_wavelet: bool = False) -> Dict:
        """Complete preprocessing pipeline for FRA data.
        
        Args:
            canonical_data: Canonical FRA data structure
            apply_filtering: Whether to apply Savitzky-Golay filtering
            apply_wavelet: Whether to apply wavelet denoising
            
        Returns:
            Processed FRA data with normalized measurements
        """
        measurement = canonical_data['measurement']
        
        # Extract data
        frequencies = np.array(measurement['frequencies'])
        magnitudes = np.array(measurement['magnitudes'])
        phases = np.array(measurement.get('phases', []))
        
        if len(phases) == 0:
            phases = None
        
        # Convert magnitudes to dB if needed
        if measurement.get('unit', 'dB').lower() != 'db':
            if measurement['unit'].lower() in ['linear', 'magnitude']:
                magnitudes = 20 * np.log10(np.maximum(magnitudes, 1e-12))
            else:
                logger.warning(f"Unknown magnitude unit: {measurement['unit']}. Assuming dB.")
        
        # Step 1: Resample to common grid
        resampled_freq, resampled_mag, resampled_phase = self.resample_to_common_grid(
            frequencies, magnitudes, phases
        )
        
        # Step 2: Apply filtering if requested
        if apply_filtering:
            resampled_mag, resampled_phase = self.apply_savgol_filter(
                resampled_mag, resampled_phase
            )
        
        # Step 3: Apply wavelet denoising if requested
        if apply_wavelet:
            resampled_mag = self.apply_wavelet_denoising(resampled_mag)
        
        # Step 4: Normalize data
        normalized_mag = self.normalize_magnitude(resampled_mag)
        normalized_phase = None
        if resampled_phase is not None:
            normalized_phase = self.normalize_phase(resampled_phase)
        
        # Create processed data structure
        processed_data = canonical_data.copy()
        processed_data['measurement']['frequencies'] = resampled_freq.tolist()
        processed_data['measurement']['magnitudes'] = resampled_mag.tolist()
        processed_data['measurement']['unit'] = 'dB'
        
        if normalized_phase is not None:
            processed_data['measurement']['phases'] = resampled_phase.tolist()
            processed_data['measurement']['phase_unit'] = 'degrees'
        
        # Add normalization metadata
        from datetime import datetime
        processed_data['processing_metadata'] = {
            'processed_date': datetime.now().isoformat(),
            'preprocessing_steps': [
                'resampling_to_common_grid',
                'savitzky_golay_filtering' if apply_filtering else None,
                'wavelet_denoising' if apply_wavelet else None,
                'normalization'
            ],
            'target_points': self.target_points,
            'frequency_range_hz': [self.freq_min, self.freq_max],
            'magnitude_range_db': [self.mag_min, self.mag_max],
            'normalized_data': {
                'frequencies_log10': np.log10(resampled_freq).tolist(),
                'magnitudes_normalized': normalized_mag.tolist(),
                'phases_normalized': normalized_phase.tolist() if normalized_phase is not None else None
            }
        }
        
        # Remove None values from preprocessing steps
        processed_data['processing_metadata']['preprocessing_steps'] = [
            step for step in processed_data['processing_metadata']['preprocessing_steps'] 
            if step is not None
        ]
        
        return processed_data
    
    def create_spectrogram(self, frequencies: np.ndarray, 
                          magnitudes: np.ndarray,
                          nperseg: int = 256) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create spectrogram representation for 2D CNN analysis.
        
        Args:
            frequencies: Frequency values
            magnitudes: Magnitude values
            nperseg: Length of each segment for STFT
            
        Returns:
            Tuple of (frequencies, times, spectrogram)
        """
        # Use Short-Time Fourier Transform to create spectrogram
        # Treat magnitude data as time series
        f, t, Sxx = signal.spectrogram(
            magnitudes, 
            fs=len(magnitudes),
            nperseg=min(nperseg, len(magnitudes)//4),
            noverlap=None,
            mode='magnitude'
        )
        
        return f, t, Sxx


# Test function
def test_normalizer():
    """Test FRA normalizer with sample data."""
    normalizer = FRANormalizer()
    
    # Create test FRA data
    frequencies = np.logspace(4, 7, 1000)  # 10 kHz to 10 MHz
    magnitudes = 40 - 10 * np.log10(frequencies / 1e4)  # Decreasing with frequency
    phases = -20 * np.log10(frequencies / 1e4)  # Phase lag
    
    # Add some noise
    magnitudes += 0.1 * np.random.normal(size=len(magnitudes))
    phases += 0.5 * np.random.normal(size=len(phases))
    
    # Create canonical data structure
    test_data = {
        'measurement': {
            'frequencies': frequencies.tolist(),
            'magnitudes': magnitudes.tolist(),
            'phases': phases.tolist(),
            'unit': 'dB',
            'phase_unit': 'degrees'
        },
        'asset_metadata': {'asset_id': 'TEST_TR_001'},
        'test_info': {'test_id': 'TEST_001'},
        'raw_file': {'filename': 'test.csv'}
    }
    
    try:
        # Process data
        processed = normalizer.process_fra_data(
            test_data, 
            apply_filtering=True, 
            apply_wavelet=False
        )
        
        print("FRA Normalizer Test Results:")
        print(f"✓ Original data points: {len(frequencies)}")
        print(f"✓ Processed data points: {len(processed['measurement']['frequencies'])}")
        print(f"✓ Frequency range: {processed['processing_metadata']['frequency_range_hz']}")
        print(f"✓ Preprocessing steps: {processed['processing_metadata']['preprocessing_steps']}")
        
        # Validate normalized data
        norm_mag = np.array(processed['processing_metadata']['normalized_data']['magnitudes_normalized'])
        norm_phase = np.array(processed['processing_metadata']['normalized_data']['phases_normalized'])
        
        print(f"✓ Normalized magnitude range: [{norm_mag.min():.3f}, {norm_mag.max():.3f}]")
        print(f"✓ Normalized phase range: [{norm_phase.min():.3f}, {norm_phase.max():.3f}]")
        
        return processed
        
    except Exception as e:
        print(f"✗ FRA Normalizer test failed: {e}")
        return None


if __name__ == "__main__":
    test_normalizer()
