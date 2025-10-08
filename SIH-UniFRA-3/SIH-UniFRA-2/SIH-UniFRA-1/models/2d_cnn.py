#!/usr/bin/env python3
"""
2D CNN Model for FRA Fault Classification

Implements a 2D Convolutional Neural Network for FRA spectrogram/image analysis.
Designed to analyze FRA data converted to 2D representations (spectrograms, plots).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FRA2DCNN(nn.Module):
    """2D CNN for FRA fault classification from spectrogram/image data."""
    
    def __init__(self, input_size: Tuple[int, int] = (224, 224),
                 num_fault_classes: int = 10,
                 num_severity_classes: int = 3,
                 dropout_rate: float = 0.3):
        """
        Initialize 2D CNN model.
        
        Args:
            input_size: Input image size as (height, width)
            num_fault_classes: Number of fault types (including healthy)
            num_severity_classes: Number of severity levels  
            dropout_rate: Dropout rate for regularization
        """
        super(FRA2DCNN, self).__init__()
        
        self.input_size = input_size
        self.num_fault_classes = num_fault_classes
        self.num_severity_classes = num_severity_classes
        
        # Convolutional backbone (ResNet-inspired)
        self.conv1 = nn.Conv2d(1, 32, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        
        # Residual blocks
        self.layer1 = self._make_layer(32, 64, 2, stride=1)
        self.layer2 = self._make_layer(64, 128, 2, stride=2)
        self.layer3 = self._make_layer(128, 256, 2, stride=2)
        self.layer4 = self._make_layer(256, 512, 2, stride=2)
        
        # Global average pooling
        self.global_avg_pool = nn.AdaptiveAvgPool2d(1)
        
        # Fully connected layers
        self.dropout = nn.Dropout(dropout_rate)
        
        # Shared feature extractor
        self.fc_shared = nn.Linear(512, 256)
        
        # Classification heads
        self.fc_fault = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, num_fault_classes)
        )
        
        self.fc_severity = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, num_severity_classes)
        )
        
        self.fc_anomaly = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, 2)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _make_layer(self, in_channels: int, out_channels: int, 
                   num_blocks: int, stride: int = 1) -> nn.Sequential:
        """Create a residual layer with multiple blocks."""
        layers = []
        
        # First block may have stride > 1 for downsampling
        layers.append(ResidualBlock(in_channels, out_channels, stride))
        
        # Remaining blocks have stride = 1
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels, 1))
        
        return nn.Sequential(*layers)
    
    def _initialize_weights(self):
        """Initialize model weights."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, height, width) or (batch_size, 1, height, width)
            
        Returns:
            Tuple of (fault_logits, severity_logits, anomaly_logits)
        """
        # Add channel dimension if needed
        if len(x.shape) == 3:
            x = x.unsqueeze(1)  # (batch_size, 1, height, width)
        
        # Initial convolution
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        
        # Residual layers
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        # Global average pooling
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)  # Flatten
        
        # Shared feature representation
        x = F.relu(self.fc_shared(x))
        x = self.dropout(x)
        
        # Classification heads
        fault_logits = self.fc_fault(x)
        severity_logits = self.fc_severity(x)
        anomaly_logits = self.fc_anomaly(x)
        
        return fault_logits, severity_logits, anomaly_logits
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract feature representations.
        
        Args:
            x: Input tensor
            
        Returns:
            Feature tensor of shape (batch_size, 256)
        """
        with torch.no_grad():
            if len(x.shape) == 3:
                x = x.unsqueeze(1)
            
            # Forward through backbone
            x = self.pool1(F.relu(self.bn1(self.conv1(x))))
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            
            # Global average pooling
            x = self.global_avg_pool(x)
            x = x.view(x.size(0), -1)
            
            # Shared features
            x = F.relu(self.fc_shared(x))
            
            return x


class ResidualBlock(nn.Module):
    """Residual block for 2D CNN."""
    
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super(ResidualBlock, self).__init__()
        
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, 
                              stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3,
                              stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Shortcut connection
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, 
                         stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        
        out += residual
        out = F.relu(out)
        
        return out


class FRAImageConverter:
    """Converts FRA data to 2D image representations for CNN analysis."""
    
    def __init__(self, image_size: Tuple[int, int] = (224, 224)):
        self.image_size = image_size
    
    def fra_to_spectrogram(self, frequencies: np.ndarray, 
                          magnitudes: np.ndarray,
                          phases: Optional[np.ndarray] = None) -> np.ndarray:
        """Convert FRA data to spectrogram representation.
        
        Args:
            frequencies: Frequency points
            magnitudes: Magnitude values
            phases: Phase values (optional)
            
        Returns:
            2D spectrogram image
        """
        try:
            import matplotlib.pyplot as plt
            from scipy import signal
            
            # Create spectrogram using STFT of magnitude data
            nperseg = min(256, len(magnitudes) // 4)
            f, t, Sxx = signal.spectrogram(
                magnitudes, 
                fs=len(magnitudes),
                nperseg=nperseg,
                mode='magnitude'
            )
            
            # Convert to dB scale
            Sxx_db = 20 * np.log10(np.maximum(Sxx, 1e-12))
            
            # Resize to target image size
            from scipy.ndimage import zoom
            
            zoom_factors = (
                self.image_size[0] / Sxx_db.shape[0],
                self.image_size[1] / Sxx_db.shape[1]
            )
            
            spectrogram_image = zoom(Sxx_db, zoom_factors)
            
            # Normalize to [0, 1]
            spectrogram_image = (spectrogram_image - spectrogram_image.min()) / (
                spectrogram_image.max() - spectrogram_image.min() + 1e-8
            )
            
            return spectrogram_image
            
        except Exception as e:
            logger.warning(f"Spectrogram conversion failed: {e}")
            # Fallback to simple 2D representation
            return self.fra_to_plot_image(frequencies, magnitudes, phases)
    
    def fra_to_plot_image(self, frequencies: np.ndarray,
                         magnitudes: np.ndarray, 
                         phases: Optional[np.ndarray] = None) -> np.ndarray:
        """Convert FRA data to plot-based image representation.
        
        Args:
            frequencies: Frequency points
            magnitudes: Magnitude values
            phases: Phase values (optional)
            
        Returns:
            2D plot image
        """
        try:
            import matplotlib.pyplot as plt
            from io import BytesIO
            from PIL import Image
            
            # Create figure with specified size
            fig, ax = plt.subplots(figsize=(8, 6), dpi=28)  # Gives ~224x168
            
            # Plot magnitude vs frequency
            ax.semilogx(frequencies, magnitudes, 'b-', linewidth=2)
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Magnitude (dB)')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(frequencies[0], frequencies[-1])
            
            # Remove axes for cleaner image
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel('')
            ax.set_ylabel('')
            
            # Convert to image array
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            
            # Load as PIL image and convert to numpy
            img = Image.open(buf).convert('L')  # Grayscale
            img = img.resize(self.image_size, Image.Resampling.LANCZOS)
            img_array = np.array(img) / 255.0  # Normalize to [0, 1]
            
            plt.close(fig)
            buf.close()
            
            return img_array
            
        except Exception as e:
            logger.warning(f"Plot image conversion failed: {e}")
            # Fallback to simple grid representation
            return self._create_simple_grid(frequencies, magnitudes)
    
    def _create_simple_grid(self, frequencies: np.ndarray, 
                           magnitudes: np.ndarray) -> np.ndarray:
        """Create simple grid representation as fallback."""
        # Create a simple 2D grid representation
        grid = np.zeros(self.image_size)
        
        # Map frequency and magnitude to grid coordinates
        log_freq = np.log10(frequencies)
        
        freq_min, freq_max = log_freq.min(), log_freq.max()
        mag_min, mag_max = magnitudes.min(), magnitudes.max()
        
        for i, (f, m) in enumerate(zip(log_freq, magnitudes)):
            # Map to grid coordinates
            x = int((f - freq_min) / (freq_max - freq_min) * (self.image_size[1] - 1))
            y = int((m - mag_min) / (mag_max - mag_min) * (self.image_size[0] - 1))
            
            # Invert y-axis (higher magnitude at top)
            y = self.image_size[0] - 1 - y
            
            if 0 <= x < self.image_size[1] and 0 <= y < self.image_size[0]:
                grid[y, x] = 1.0
        
        return grid


# Test function
def test_2d_cnn():
    """Test 2D CNN model with sample data."""
    print("\nTesting 2D CNN FRA Model...")
    
    # Model parameters
    image_size = (224, 224)
    batch_size = 4
    num_fault_classes = 10
    num_severity_classes = 3
    
    # Create model
    model = FRA2DCNN(
        input_size=image_size,
        num_fault_classes=num_fault_classes,
        num_severity_classes=num_severity_classes
    )
    
    # Create sample input (batch_size, height, width)
    sample_input = torch.randn(batch_size, *image_size)
    
    try:
        # Forward pass
        fault_logits, severity_logits, anomaly_logits = model(sample_input)
        
        print(f"✓ Model forward pass successful")
        print(f"✓ Input shape: {sample_input.shape}")
        print(f"✓ Fault logits shape: {fault_logits.shape}")
        print(f"✓ Severity logits shape: {severity_logits.shape}")
        print(f"✓ Anomaly logits shape: {anomaly_logits.shape}")
        
        # Test feature extraction
        features = model.extract_features(sample_input)
        print(f"✓ Feature extraction shape: {features.shape}")
        
        # Test image converter
        converter = FRAImageConverter(image_size)
        
        # Create sample FRA data
        frequencies = np.logspace(4, 7, 1000)
        magnitudes = 40 - 10 * np.log10(frequencies / 1e4)
        
        # Convert to image
        fra_image = converter.fra_to_plot_image(frequencies, magnitudes)
        print(f"✓ FRA to image conversion shape: {fra_image.shape}")
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        print(f"✓ Total parameters: {total_params:,}")
        print(f"✓ Trainable parameters: {trainable_params:,}")
        
        return model
        
    except Exception as e:
        print(f"✗ 2D CNN test failed: {e}")
        return None


if __name__ == "__main__":
    test_2d_cnn()
