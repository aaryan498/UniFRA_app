#!/usr/bin/env python3
"""
FRA Image Representation

Converts FRA frequency response data to visual representations for analysis.
Supports multiple visualization formats including plots, spectrograms, and heatmaps.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
from scipy import signal
from PIL import Image, ImageDraw, ImageFont
import io
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class FRAImageGenerator:
    """Generates various image representations of FRA data."""
    
    def __init__(self, image_size: Tuple[int, int] = (512, 384), 
                 dpi: int = 100):
        """
        Initialize image generator.
        
        Args:
            image_size: Output image size (width, height)
            dpi: Image resolution
        """
        self.image_size = image_size
        self.dpi = dpi
        
        # Color schemes
        self.color_schemes = {
            'default': {
                'background': '#FFFFFF',
                'curve': '#1f77b4',
                'grid': '#E0E0E0',
                'text': '#000000'
            },
            'dark': {
                'background': '#2E2E2E',
                'curve': '#00D4FF',
                'grid': '#404040',
                'text': '#FFFFFF'
            },
            'fault_highlight': {
                'background': '#FFFFFF',
                'curve': '#FF6B6B',
                'grid': '#E0E0E0',
                'text': '#000000',
                'highlight': '#FFD93D'
            }
        }
    
    def create_fra_plot(self, frequencies: np.ndarray, 
                       magnitudes: np.ndarray,
                       phases: Optional[np.ndarray] = None,
                       title: str = "FRA Response",
                       color_scheme: str = 'default',
                       highlight_bands: Optional[List[Tuple[float, float]]] = None) -> np.ndarray:
        """Create standard FRA magnitude vs frequency plot.
        
        Args:
            frequencies: Frequency points (Hz)
            magnitudes: Magnitude values (dB)
            phases: Phase values (degrees), optional
            title: Plot title
            color_scheme: Color scheme to use
            highlight_bands: Frequency bands to highlight
            
        Returns:
            Image array (RGB)
        """
        colors = self.color_schemes.get(color_scheme, self.color_schemes['default'])
        
        # Create figure
        fig_width = self.image_size[0] / self.dpi
        fig_height = self.image_size[1] / self.dpi
        
        if phases is not None:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_width, fig_height), 
                                          facecolor=colors['background'])
        else:
            fig, ax1 = plt.subplots(1, 1, figsize=(fig_width, fig_height),
                                   facecolor=colors['background'])
        
        # Magnitude plot
        ax1.semilogx(frequencies, magnitudes, color=colors['curve'], linewidth=2)
        ax1.set_xlabel('Frequency (Hz)', color=colors['text'])
        ax1.set_ylabel('Magnitude (dB)', color=colors['text'])
        ax1.set_title(title, color=colors['text'], fontsize=14, fontweight='bold')
        ax1.grid(True, color=colors['grid'], alpha=0.7)
        ax1.set_facecolor(colors['background'])
        
        # Highlight frequency bands if specified
        if highlight_bands:
            for f_min, f_max in highlight_bands:
                ax1.axvspan(f_min, f_max, alpha=0.3, 
                           color=colors.get('highlight', '#FFD93D'))
        
        # Customize appearance
        ax1.tick_params(colors=colors['text'])
        ax1.spines['bottom'].set_color(colors['text'])
        ax1.spines['left'].set_color(colors['text'])
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # Phase plot if available
        if phases is not None:
            ax2.semilogx(frequencies, phases, color=colors['curve'], linewidth=2)
            ax2.set_xlabel('Frequency (Hz)', color=colors['text'])
            ax2.set_ylabel('Phase (degrees)', color=colors['text'])
            ax2.grid(True, color=colors['grid'], alpha=0.7)
            ax2.set_facecolor(colors['background'])
            
            ax2.tick_params(colors=colors['text'])
            ax2.spines['bottom'].set_color(colors['text'])
            ax2.spines['left'].set_color(colors['text'])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Convert to image array
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        return buf
    
    def create_spectrogram(self, frequencies: np.ndarray,
                          magnitudes: np.ndarray,
                          title: str = "FRA Spectrogram",
                          color_scheme: str = 'default') -> np.ndarray:
        """Create spectrogram representation of FRA data.
        
        Args:
            frequencies: Frequency points
            magnitudes: Magnitude values
            title: Plot title
            color_scheme: Color scheme
            
        Returns:
            Spectrogram image array
        """
        colors = self.color_schemes.get(color_scheme, self.color_schemes['default'])
        
        # Create spectrogram using STFT
        nperseg = min(256, len(magnitudes) // 4)
        f, t, Sxx = signal.spectrogram(
            magnitudes,
            fs=len(magnitudes),
            nperseg=nperseg,
            mode='magnitude'
        )
        
        # Convert to dB
        Sxx_db = 20 * np.log10(np.maximum(Sxx, 1e-12))
        
        # Create plot
        fig_width = self.image_size[0] / self.dpi
        fig_height = self.image_size[1] / self.dpi
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height),
                              facecolor=colors['background'])
        
        # Plot spectrogram
        im = ax.pcolormesh(t, f, Sxx_db, shading='gouraud', cmap='viridis')
        ax.set_xlabel('Time Index', color=colors['text'])
        ax.set_ylabel('Frequency Bin', color=colors['text'])
        ax.set_title(title, color=colors['text'], fontsize=14, fontweight='bold')
        ax.set_facecolor(colors['background'])
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Magnitude (dB)', color=colors['text'])
        cbar.ax.tick_params(colors=colors['text'])
        
        # Customize appearance
        ax.tick_params(colors=colors['text'])
        for spine in ax.spines.values():
            spine.set_color(colors['text'])
        
        plt.tight_layout()
        
        # Convert to image array
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        return buf
    
    def create_comparison_plot(self, baseline_data: Dict, 
                              current_data: Dict,
                              title: str = "FRA Comparison") -> np.ndarray:
        """Create comparison plot between baseline and current FRA data.
        
        Args:
            baseline_data: Baseline FRA data with 'frequencies' and 'magnitudes'
            current_data: Current FRA data with 'frequencies' and 'magnitudes'
            title: Plot title
            
        Returns:
            Comparison plot image array
        """
        fig_width = self.image_size[0] / self.dpi
        fig_height = self.image_size[1] / self.dpi
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Plot baseline
        ax.semilogx(baseline_data['frequencies'], baseline_data['magnitudes'],
                   'b-', linewidth=2, label='Baseline', alpha=0.8)
        
        # Plot current
        ax.semilogx(current_data['frequencies'], current_data['magnitudes'],
                   'r-', linewidth=2, label='Current', alpha=0.8)
        
        # Calculate and plot difference
        if len(baseline_data['frequencies']) == len(current_data['frequencies']):
            diff = np.array(current_data['magnitudes']) - np.array(baseline_data['magnitudes'])
            ax2 = ax.twinx()
            ax2.semilogx(current_data['frequencies'], diff, 'g--', 
                        linewidth=1, alpha=0.6, label='Difference')
            ax2.set_ylabel('Difference (dB)', color='green')
            ax2.tick_params(axis='y', labelcolor='green')
        
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Magnitude (dB)')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        # Convert to image array
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        return buf
    
    def create_fault_visualization(self, frequencies: np.ndarray,
                                  magnitudes: np.ndarray,
                                  fault_probabilities: Dict[str, float],
                                  predicted_fault: str,
                                  confidence: float) -> np.ndarray:
        """Create visualization highlighting fault characteristics.
        
        Args:
            frequencies: Frequency points
            magnitudes: Magnitude values 
            fault_probabilities: Dictionary of fault type probabilities
            predicted_fault: Predicted fault type
            confidence: Prediction confidence
            
        Returns:
            Fault visualization image
        """
        fig_width = self.image_size[0] / self.dpi
        fig_height = self.image_size[1] / self.dpi
        
        # Create subplot layout
        fig = plt.figure(figsize=(fig_width, fig_height))
        gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], width_ratios=[3, 1])
        
        # Main FRA plot
        ax_main = fig.add_subplot(gs[0, :])
        
        # Color based on fault type
        fault_colors = {
            'healthy': '#2E8B57',
            'axial_displacement': '#FF6B6B',
            'radial_deformation': '#4ECDC4',
            'core_grounding': '#45B7D1',
            'turn_turn_short': '#F39C12',
            'insulation_degradation': '#9B59B6',
            'partial_discharge': '#E74C3C'
        }
        
        curve_color = fault_colors.get(predicted_fault, '#1f77b4')
        
        ax_main.semilogx(frequencies, magnitudes, color=curve_color, linewidth=2.5)
        ax_main.set_xlabel('Frequency (Hz)')
        ax_main.set_ylabel('Magnitude (dB)')
        ax_main.set_title(f'FRA Analysis: {predicted_fault.replace("_", " ").title()} '
                         f'(Confidence: {confidence:.1%})', fontweight='bold')
        ax_main.grid(True, alpha=0.3)
        
        # Probability bar chart
        ax_prob = fig.add_subplot(gs[1, 0])
        
        # Select top 5 probabilities for display
        sorted_faults = sorted(fault_probabilities.items(), 
                             key=lambda x: x[1], reverse=True)[:5]
        
        fault_names = [f.replace('_', ' ').title()[:10] for f, _ in sorted_faults]
        probabilities = [p for _, p in sorted_faults]
        
        bars = ax_prob.barh(fault_names, probabilities)
        
        # Color bars based on fault type
        for i, (fault_type, _) in enumerate(sorted_faults):
            bars[i].set_color(fault_colors.get(fault_type, '#1f77b4'))
        
        ax_prob.set_xlabel('Probability')
        ax_prob.set_title('Fault Probabilities')
        ax_prob.set_xlim(0, 1)
        
        # Add confidence indicator
        ax_conf = fig.add_subplot(gs[1, 1])
        ax_conf.pie([confidence, 1-confidence], 
                   colors=['#2E8B57', '#E0E0E0'],
                   startangle=90,
                   counterclock=False)
        ax_conf.set_title(f'Confidence\n{confidence:.1%}')
        
        plt.tight_layout()
        
        # Convert to image array
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(canvas.get_width_height()[::-1] + (3,))
        
        plt.close(fig)
        
        return buf
    
    def save_image(self, image_array: np.ndarray, filepath: str, 
                  format: str = 'PNG') -> None:
        """Save image array to file.
        
        Args:
            image_array: Image data as numpy array
            filepath: Output file path
            format: Image format (PNG, JPEG, etc.)
        """
        image = Image.fromarray(image_array)
        image.save(filepath, format=format)
        logger.info(f"Image saved to {filepath}")
    
    def array_to_base64(self, image_array: np.ndarray) -> str:
        """Convert image array to base64 string for web display.
        
        Args:
            image_array: Image data as numpy array
            
        Returns:
            Base64 encoded image string
        """
        import base64
        
        image = Image.fromarray(image_array)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"


# Test function
def test_image_generator():
    """Test FRA image generation functionality."""
    print("\nTesting FRA Image Generator...")
    
    generator = FRAImageGenerator()
    
    # Create test data
    frequencies = np.logspace(4, 7, 1000)  # 10 kHz to 10 MHz
    magnitudes = 40 - 10 * np.log10(frequencies / 1e4)  # Typical FRA curve
    phases = -20 * np.log10(frequencies / 1e4)  # Phase response
    
    # Add some resonance features
    resonance_freqs = [100e3, 1e6, 5e6]
    for f_res in resonance_freqs:
        resonance = 5 * np.exp(-((frequencies - f_res) / (0.2 * f_res))**2)
        magnitudes += resonance
    
    try:
        # Test basic FRA plot
        fra_plot = generator.create_fra_plot(frequencies, magnitudes, phases)
        print(f"✓ FRA plot created: {fra_plot.shape}")
        
        # Test spectrogram
        spectrogram = generator.create_spectrogram(frequencies, magnitudes)
        print(f"✓ Spectrogram created: {spectrogram.shape}")
        
        # Test fault visualization
        fault_probs = {
            'healthy': 0.1,
            'axial_displacement': 0.7,
            'radial_deformation': 0.1,
            'core_grounding': 0.05,
            'turn_turn_short': 0.05
        }
        
        fault_viz = generator.create_fault_visualization(
            frequencies, magnitudes, fault_probs, 'axial_displacement', 0.85
        )
        print(f"✓ Fault visualization created: {fault_viz.shape}")
        
        # Test base64 conversion
        base64_str = generator.array_to_base64(fra_plot)
        print(f"✓ Base64 conversion successful: {len(base64_str)} characters")
        
        return generator
        
    except Exception as e:
        print(f"✗ Image generator test failed: {e}")
        return None


if __name__ == "__main__":
    test_image_generator()
