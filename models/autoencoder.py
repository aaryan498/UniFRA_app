#!/usr/bin/env python3
"""
Autoencoder Model for FRA Anomaly Detection

Implements convolutional autoencoder for baseline-free anomaly detection in FRA data.
Trained on healthy transformer data to detect deviations indicating faults.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class FRAAutoencoder(nn.Module):
    """Convolutional Autoencoder for FRA anomaly detection."""
    
    def __init__(self, input_length: int = 4096, 
                 latent_dim: int = 64,
                 dropout_rate: float = 0.2):
        """
        Initialize autoencoder model.
        
        Args:
            input_length: Length of input FRA signal
            latent_dim: Dimension of latent bottleneck layer
            dropout_rate: Dropout rate for regularization
        """
        super(FRAAutoencoder, self).__init__()
        
        self.input_length = input_length
        self.latent_dim = latent_dim
        
        # Encoder
        self.encoder = nn.Sequential(
            # Input: (batch, 1, input_length)
            nn.Conv1d(1, 32, kernel_size=15, stride=2, padding=7),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 32, input_length/2)
            nn.Conv1d(32, 64, kernel_size=11, stride=2, padding=5),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 64, input_length/4)
            nn.Conv1d(64, 128, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 128, input_length/8)
            nn.Conv1d(128, 256, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
        )
        
        # Calculate the size after encoder convolutions
        self.encoded_size = self._calculate_encoded_size()
        
        # Bottleneck (latent space)
        self.bottleneck_encoder = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, latent_dim),
            nn.ReLU()
        )
        
        self.bottleneck_decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Unflatten(1, (256, 1))
        )
        
        # Decoder (symmetric to encoder)
        self.decoder = nn.Sequential(
            # Upsample to encoded size
            nn.Upsample(size=self.encoded_size, mode='linear', align_corners=False),
            
            # (batch, 256, input_length/8)
            nn.ConvTranspose1d(256, 128, kernel_size=5, stride=2, padding=2, output_padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 128, input_length/4)
            nn.ConvTranspose1d(128, 64, kernel_size=7, stride=2, padding=3, output_padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 64, input_length/2)
            nn.ConvTranspose1d(64, 32, kernel_size=11, stride=2, padding=5, output_padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout1d(dropout_rate),
            
            # (batch, 32, input_length)
            nn.ConvTranspose1d(32, 1, kernel_size=15, stride=2, padding=7, output_padding=1),
            nn.Tanh()  # Output activation to match input range
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _calculate_encoded_size(self) -> int:
        """Calculate the size after encoder convolutions."""
        size = self.input_length
        
        # After each conv layer with stride=2
        for _ in range(4):  # 4 conv layers
            size = size // 2
        
        return size
    
    def _initialize_weights(self):
        """Initialize model weights."""
        for m in self.modules():
            if isinstance(m, (nn.Conv1d, nn.ConvTranspose1d)):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode input to latent space.
        
        Args:
            x: Input tensor of shape (batch_size, input_length)
            
        Returns:
            Latent representation of shape (batch_size, latent_dim)
        """
        if len(x.shape) == 2:
            x = x.unsqueeze(1)  # Add channel dimension
        
        encoded = self.encoder(x)
        latent = self.bottleneck_encoder(encoded)
        
        return latent
    
    def decode(self, latent: torch.Tensor) -> torch.Tensor:
        """Decode latent representation to output.
        
        Args:
            latent: Latent tensor of shape (batch_size, latent_dim)
            
        Returns:
            Reconstructed tensor of shape (batch_size, input_length)
        """
        decoded_latent = self.bottleneck_decoder(latent)
        reconstructed = self.decoder(decoded_latent)
        
        # Remove channel dimension
        reconstructed = reconstructed.squeeze(1)
        
        return reconstructed
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through autoencoder.
        
        Args:
            x: Input tensor of shape (batch_size, input_length)
            
        Returns:
            Tuple of (reconstructed, latent_representation)
        """
        latent = self.encode(x)
        reconstructed = self.decode(latent)
        
        return reconstructed, latent
    
    def compute_reconstruction_error(self, x: torch.Tensor, 
                                   reduction: str = 'mean') -> torch.Tensor:
        """Compute reconstruction error (anomaly score).
        
        Args:
            x: Input tensor
            reduction: Reduction method ('mean', 'sum', 'none')
            
        Returns:
            Reconstruction error tensor
        """
        reconstructed, _ = self.forward(x)
        
        # Mean squared error per sample
        mse = F.mse_loss(reconstructed, x, reduction='none')
        
        if reduction == 'mean':
            return mse.mean(dim=1)  # Average over sequence length
        elif reduction == 'sum':
            return mse.sum(dim=1)   # Sum over sequence length
        else:
            return mse  # No reduction


class FRAAnomalyDetector:
    """Anomaly detector using trained autoencoder."""
    
    def __init__(self, autoencoder: FRAAutoencoder, device: str = 'cpu'):
        self.autoencoder = autoencoder
        self.device = device
        self.autoencoder.to(device)
        
        # Anomaly threshold (will be set during training)
        self.threshold = None
        
        # Statistics from healthy training data
        self.healthy_stats = {
            'mean_error': None,
            'std_error': None,
            'percentiles': None
        }
    
    def fit_threshold(self, healthy_dataloader, percentile: float = 99.0) -> float:
        """Fit anomaly threshold using healthy data.
        
        Args:
            healthy_dataloader: DataLoader with healthy FRA samples
            percentile: Percentile of reconstruction errors to use as threshold
            
        Returns:
            Computed threshold value
        """
        self.autoencoder.eval()
        
        reconstruction_errors = []
        
        with torch.no_grad():
            for batch_data in healthy_dataloader:
                if isinstance(batch_data, (list, tuple)):
                    data = batch_data[0]  # Assume first element is data
                else:
                    data = batch_data
                
                data = data.to(self.device)
                errors = self.autoencoder.compute_reconstruction_error(data)
                reconstruction_errors.extend(errors.cpu().numpy())
        
        reconstruction_errors = np.array(reconstruction_errors)
        
        # Compute statistics
        self.healthy_stats['mean_error'] = np.mean(reconstruction_errors)
        self.healthy_stats['std_error'] = np.std(reconstruction_errors)
        self.healthy_stats['percentiles'] = {
            '95': np.percentile(reconstruction_errors, 95),
            '99': np.percentile(reconstruction_errors, 99),
            '99.5': np.percentile(reconstruction_errors, 99.5),
            '99.9': np.percentile(reconstruction_errors, 99.9)
        }
        
        # Set threshold at specified percentile
        self.threshold = np.percentile(reconstruction_errors, percentile)
        
        logger.info(f"Anomaly threshold set to {self.threshold:.6f} ({percentile}th percentile)")
        logger.info(f"Healthy data statistics: mean={self.healthy_stats['mean_error']:.6f}, "
                   f"std={self.healthy_stats['std_error']:.6f}")
        
        return self.threshold
    
    def detect_anomaly(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Detect anomalies in input data.
        
        Args:
            x: Input tensor of shape (batch_size, input_length)
            
        Returns:
            Tuple of (anomaly_scores, is_anomaly, reconstructed)
        """
        if self.threshold is None:
            raise ValueError("Anomaly threshold not set. Call fit_threshold() first.")
        
        self.autoencoder.eval()
        
        with torch.no_grad():
            reconstructed, _ = self.autoencoder(x)
            anomaly_scores = self.autoencoder.compute_reconstruction_error(x)
            is_anomaly = anomaly_scores > self.threshold
        
        return anomaly_scores, is_anomaly, reconstructed
    
    def get_anomaly_confidence(self, anomaly_scores: torch.Tensor) -> torch.Tensor:
        """Compute anomaly confidence scores.
        
        Args:
            anomaly_scores: Reconstruction error scores
            
        Returns:
            Confidence scores between 0 and 1
        """
        if self.threshold is None:
            raise ValueError("Anomaly threshold not set.")
        
        # Normalize scores relative to threshold
        normalized_scores = anomaly_scores / self.threshold
        
        # Convert to confidence (sigmoid-like function)
        confidence = torch.sigmoid(2 * (normalized_scores - 1))
        
        return confidence


class FRAAutoencoderTrainer:
    """Training utilities for FRA autoencoder."""
    
    def __init__(self, autoencoder: FRAAutoencoder, device: str = 'cpu'):
        self.autoencoder = autoencoder
        self.device = device
        self.autoencoder.to(device)
        
        # Loss function
        self.criterion = nn.MSELoss()
    
    def train_epoch(self, dataloader, optimizer, epoch: int) -> Dict[str, float]:
        """Train for one epoch.
        
        Args:
            dataloader: Training data loader (healthy samples only)
            optimizer: Optimizer instance
            epoch: Current epoch number
            
        Returns:
            Dictionary of training metrics
        """
        self.autoencoder.train()
        
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch_data in enumerate(dataloader):
            if isinstance(batch_data, (list, tuple)):
                data = batch_data[0]  # Assume first element is data
            else:
                data = batch_data
            
            data = data.to(self.device)
            
            optimizer.zero_grad()
            
            # Forward pass
            reconstructed, latent = self.autoencoder(data)
            
            # Reconstruction loss
            loss = self.criterion(reconstructed, data)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            if batch_idx % 10 == 0:
                logger.info(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.6f}')
        
        metrics = {
            'loss': total_loss / num_batches,
            'avg_reconstruction_error': total_loss / num_batches
        }
        
        return metrics
    
    def evaluate(self, dataloader) -> Dict[str, float]:
        """Evaluate autoencoder on validation data.
        
        Args:
            dataloader: Validation data loader
            
        Returns:
            Dictionary of evaluation metrics
        """
        self.autoencoder.eval()
        
        total_loss = 0.0
        reconstruction_errors = []
        num_batches = 0
        
        with torch.no_grad():
            for batch_data in dataloader:
                if isinstance(batch_data, (list, tuple)):
                    data = batch_data[0]
                else:
                    data = batch_data
                
                data = data.to(self.device)
                
                reconstructed, latent = self.autoencoder(data)
                loss = self.criterion(reconstructed, data)
                
                total_loss += loss.item()
                num_batches += 1
                
                # Compute per-sample reconstruction errors
                errors = self.autoencoder.compute_reconstruction_error(data)
                reconstruction_errors.extend(errors.cpu().numpy())
        
        reconstruction_errors = np.array(reconstruction_errors)
        
        metrics = {
            'loss': total_loss / num_batches,
            'mean_reconstruction_error': np.mean(reconstruction_errors),
            'std_reconstruction_error': np.std(reconstruction_errors),
            'max_reconstruction_error': np.max(reconstruction_errors),
            'min_reconstruction_error': np.min(reconstruction_errors)
        }
        
        return metrics


# Test function
def test_autoencoder():
    """Test autoencoder model with sample data."""
    print("\nTesting FRA Autoencoder Model...")
    
    # Model parameters
    input_length = 4096
    batch_size = 8
    latent_dim = 64
    
    # Create model
    autoencoder = FRAAutoencoder(
        input_length=input_length,
        latent_dim=latent_dim
    )
    
    # Create sample input (batch_size, input_length)
    sample_input = torch.randn(batch_size, input_length)
    
    try:
        # Forward pass
        reconstructed, latent = autoencoder(sample_input)
        
        print(f"✓ Autoencoder forward pass successful")
        print(f"✓ Input shape: {sample_input.shape}")
        print(f"✓ Reconstructed shape: {reconstructed.shape}")
        print(f"✓ Latent shape: {latent.shape}")
        
        # Test encoding and decoding separately
        encoded = autoencoder.encode(sample_input)
        decoded = autoencoder.decode(encoded)
        
        print(f"✓ Separate encode/decode successful")
        print(f"✓ Encoded shape: {encoded.shape}")
        print(f"✓ Decoded shape: {decoded.shape}")
        
        # Test reconstruction error
        recon_error = autoencoder.compute_reconstruction_error(sample_input)
        print(f"✓ Reconstruction error shape: {recon_error.shape}")
        print(f"✓ Mean reconstruction error: {recon_error.mean().item():.6f}")
        
        # Test anomaly detector
        detector = FRAAnomalyDetector(autoencoder)
        
        # Create mock healthy data for threshold fitting
        healthy_data = [torch.randn(4, input_length) for _ in range(5)]
        
        # Mock dataloader
        class MockDataLoader:
            def __init__(self, data_list):
                self.data_list = data_list
            
            def __iter__(self):
                return iter(self.data_list)
        
        healthy_dataloader = MockDataLoader(healthy_data)
        
        # Fit threshold
        threshold = detector.fit_threshold(healthy_dataloader, percentile=95)
        print(f"✓ Anomaly threshold fitted: {threshold:.6f}")
        
        # Test anomaly detection
        anomaly_scores, is_anomaly, reconstructed = detector.detect_anomaly(sample_input)
        print(f"✓ Anomaly detection completed")
        print(f"✓ Number of detected anomalies: {is_anomaly.sum().item()}")
        
        # Count parameters
        total_params = sum(p.numel() for p in autoencoder.parameters())
        trainable_params = sum(p.numel() for p in autoencoder.parameters() if p.requires_grad)
        
        print(f"✓ Total parameters: {total_params:,}")
        print(f"✓ Trainable parameters: {trainable_params:,}")
        
        return autoencoder
        
    except Exception as e:
        print(f"✗ Autoencoder test failed: {e}")
        return None


if __name__ == "__main__":
    test_autoencoder()
