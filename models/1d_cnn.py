#!/usr/bin/env python3
"""
1D CNN Model for FRA Fault Classification

Implements a 1D Convolutional Neural Network for direct frequency-domain FRA analysis.
Designed to classify transformer faults and severity levels from raw FRA magnitude data.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class FRA1DCNN(nn.Module):
    """1D CNN for FRA fault classification from frequency domain data."""
    
    def __init__(self, input_length: int = 4096, 
                 num_fault_classes: int = 10, 
                 num_severity_classes: int = 3,
                 dropout_rate: float = 0.3):
        """
        Initialize 1D CNN model.
        
        Args:
            input_length: Length of input frequency response (number of points)
            num_fault_classes: Number of fault types (including healthy)
            num_severity_classes: Number of severity levels
            dropout_rate: Dropout rate for regularization
        """
        super(FRA1DCNN, self).__init__()
        
        self.input_length = input_length
        self.num_fault_classes = num_fault_classes
        self.num_severity_classes = num_severity_classes
        
        # Convolutional layers with batch normalization
        self.conv1 = nn.Conv1d(1, 32, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, stride=1, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        self.conv4 = nn.Conv1d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm1d(256)
        self.pool4 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Calculate the size after convolutions and pooling
        self.feature_size = self._calculate_conv_output_size()
        
        # Global Average Pooling
        self.global_avg_pool = nn.AdaptiveAvgPool1d(1)
        
        # Fully connected layers
        self.dropout = nn.Dropout(dropout_rate)
        
        # Shared feature extractor
        self.fc_shared = nn.Linear(256, 128)
        
        # Fault type classification head
        self.fc_fault = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, num_fault_classes)
        )
        
        # Severity classification head
        self.fc_severity = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(32, num_severity_classes)
        )
        
        # Anomaly detection head (binary classification: healthy vs faulty)
        self.fc_anomaly = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(32, 2)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _calculate_conv_output_size(self) -> int:
        """Calculate the output size after convolution and pooling layers."""
        size = self.input_length
        
        # After conv1 + pool1
        size = size // 2
        
        # After conv2 + pool2
        size = size // 2
        
        # After conv3 + pool3
        size = size // 2
        
        # After conv4 + pool4
        size = size // 2
        
        return size * 256  # 256 is the number of channels after conv4
    
    def _initialize_weights(self):
        """Initialize model weights using Xavier/He initialization."""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
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
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_length)
            
        Returns:
            Tuple of (fault_logits, severity_logits, anomaly_logits)
        """
        # Add channel dimension: (batch_size, 1, input_length)
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        # Convolutional layers with ReLU and pooling
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        
        # Global Average Pooling
        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)  # Flatten: (batch_size, 256)
        
        # Shared feature representation
        x = F.relu(self.fc_shared(x))
        x = self.dropout(x)
        
        # Multiple classification heads
        fault_logits = self.fc_fault(x)
        severity_logits = self.fc_severity(x)
        anomaly_logits = self.fc_anomaly(x)
        
        return fault_logits, severity_logits, anomaly_logits
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract feature representations for visualization/analysis.
        
        Args:
            x: Input tensor of shape (batch_size, input_length)
            
        Returns:
            Feature tensor of shape (batch_size, 128)
        """
        with torch.no_grad():
            if len(x.shape) == 2:
                x = x.unsqueeze(1)
            
            # Forward through convolutional layers
            x = self.pool1(F.relu(self.bn1(self.conv1(x))))
            x = self.pool2(F.relu(self.bn2(self.conv2(x))))
            x = self.pool3(F.relu(self.bn3(self.conv3(x))))
            x = self.pool4(F.relu(self.bn4(self.conv4(x))))
            
            # Global Average Pooling
            x = self.global_avg_pool(x)
            x = x.view(x.size(0), -1)
            
            # Shared feature representation
            x = F.relu(self.fc_shared(x))
            
            return x


class FRA1DCNNTrainer:
    """Training utilities for 1D CNN model."""
    
    def __init__(self, model: FRA1DCNN, device: str = 'cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        
        # Loss functions
        self.fault_criterion = nn.CrossEntropyLoss()
        self.severity_criterion = nn.CrossEntropyLoss()
        self.anomaly_criterion = nn.CrossEntropyLoss()
        
        # Loss weights for multi-task learning
        self.loss_weights = {
            'fault': 1.0,
            'severity': 0.5,
            'anomaly': 0.3
        }
    
    def compute_loss(self, outputs: Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
                    targets: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute multi-task loss.
        
        Args:
            outputs: Tuple of (fault_logits, severity_logits, anomaly_logits)
            targets: Dict with keys 'fault', 'severity', 'anomaly'
            
        Returns:
            Tuple of (total_loss, loss_dict)
        """
        fault_logits, severity_logits, anomaly_logits = outputs
        
        # Individual losses
        fault_loss = self.fault_criterion(fault_logits, targets['fault'])
        severity_loss = self.severity_criterion(severity_logits, targets['severity'])
        anomaly_loss = self.anomaly_criterion(anomaly_logits, targets['anomaly'])
        
        # Weighted total loss
        total_loss = (
            self.loss_weights['fault'] * fault_loss +
            self.loss_weights['severity'] * severity_loss +
            self.loss_weights['anomaly'] * anomaly_loss
        )
        
        loss_dict = {
            'total_loss': total_loss.item(),
            'fault_loss': fault_loss.item(),
            'severity_loss': severity_loss.item(),
            'anomaly_loss': anomaly_loss.item()
        }
        
        return total_loss, loss_dict
    
    def train_epoch(self, dataloader, optimizer, epoch: int) -> Dict[str, float]:
        """Train for one epoch.
        
        Args:
            dataloader: Training data loader
            optimizer: Optimizer instance
            epoch: Current epoch number
            
        Returns:
            Dictionary of training metrics
        """
        self.model.train()
        
        total_loss = 0.0
        fault_correct = 0
        severity_correct = 0
        anomaly_correct = 0
        total_samples = 0
        
        for batch_idx, (data, targets) in enumerate(dataloader):
            data = data.to(self.device)
            targets = {k: v.to(self.device) for k, v in targets.items()}
            
            optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(data)
            
            # Compute loss
            loss, loss_dict = self.compute_loss(outputs, targets)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Track metrics
            total_loss += loss.item()
            
            fault_pred = outputs[0].argmax(dim=1)
            severity_pred = outputs[1].argmax(dim=1)
            anomaly_pred = outputs[2].argmax(dim=1)
            
            fault_correct += (fault_pred == targets['fault']).sum().item()
            severity_correct += (severity_pred == targets['severity']).sum().item()
            anomaly_correct += (anomaly_pred == targets['anomaly']).sum().item()
            
            total_samples += data.size(0)
            
            if batch_idx % 10 == 0:
                logger.info(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}')
        
        metrics = {
            'loss': total_loss / len(dataloader),
            'fault_accuracy': fault_correct / total_samples,
            'severity_accuracy': severity_correct / total_samples,
            'anomaly_accuracy': anomaly_correct / total_samples
        }
        
        return metrics
    
    def evaluate(self, dataloader) -> Dict[str, float]:
        """Evaluate model on validation/test data.
        
        Args:
            dataloader: Validation/test data loader
            
        Returns:
            Dictionary of evaluation metrics
        """
        self.model.eval()
        
        total_loss = 0.0
        fault_correct = 0
        severity_correct = 0
        anomaly_correct = 0
        total_samples = 0
        
        all_fault_preds = []
        all_severity_preds = []
        all_anomaly_preds = []
        all_fault_targets = []
        all_severity_targets = []
        all_anomaly_targets = []
        
        with torch.no_grad():
            for data, targets in dataloader:
                data = data.to(self.device)
                targets = {k: v.to(self.device) for k, v in targets.items()}
                
                outputs = self.model(data)
                loss, _ = self.compute_loss(outputs, targets)
                
                total_loss += loss.item()
                
                fault_pred = outputs[0].argmax(dim=1)
                severity_pred = outputs[1].argmax(dim=1)
                anomaly_pred = outputs[2].argmax(dim=1)
                
                fault_correct += (fault_pred == targets['fault']).sum().item()
                severity_correct += (severity_pred == targets['severity']).sum().item()
                anomaly_correct += (anomaly_pred == targets['anomaly']).sum().item()
                
                total_samples += data.size(0)
                
                # Store predictions for detailed analysis
                all_fault_preds.extend(fault_pred.cpu().numpy())
                all_severity_preds.extend(severity_pred.cpu().numpy())
                all_anomaly_preds.extend(anomaly_pred.cpu().numpy())
                all_fault_targets.extend(targets['fault'].cpu().numpy())
                all_severity_targets.extend(targets['severity'].cpu().numpy())
                all_anomaly_targets.extend(targets['anomaly'].cpu().numpy())
        
        metrics = {
            'loss': total_loss / len(dataloader),
            'fault_accuracy': fault_correct / total_samples,
            'severity_accuracy': severity_correct / total_samples,
            'anomaly_accuracy': anomaly_correct / total_samples,
            'predictions': {
                'fault': all_fault_preds,
                'severity': all_severity_preds,
                'anomaly': all_anomaly_preds
            },
            'targets': {
                'fault': all_fault_targets,
                'severity': all_severity_targets,
                'anomaly': all_anomaly_targets
            }
        }
        
        return metrics


# Test function
def test_1d_cnn():
    """Test 1D CNN model with sample data."""
    print("Testing 1D CNN FRA Model...")
    
    # Model parameters
    input_length = 4096
    batch_size = 8
    num_fault_classes = 10
    num_severity_classes = 3
    
    # Create model
    model = FRA1DCNN(
        input_length=input_length,
        num_fault_classes=num_fault_classes,
        num_severity_classes=num_severity_classes
    )
    
    # Create sample input
    sample_input = torch.randn(batch_size, input_length)
    
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
        
        # Test trainer
        trainer = FRA1DCNNTrainer(model)
        
        # Create sample targets
        sample_targets = {
            'fault': torch.randint(0, num_fault_classes, (batch_size,)),
            'severity': torch.randint(0, num_severity_classes, (batch_size,)),
            'anomaly': torch.randint(0, 2, (batch_size,))
        }
        
        outputs = (fault_logits, severity_logits, anomaly_logits)
        loss, loss_dict = trainer.compute_loss(outputs, sample_targets)
        
        print(f"✓ Loss computation successful: {loss.item():.4f}")
        print(f"✓ Loss breakdown: {loss_dict}")
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        print(f"✓ Total parameters: {total_params:,}")
        print(f"✓ Trainable parameters: {trainable_params:,}")
        
        return model
        
    except Exception as e:
        print(f"✗ 1D CNN test failed: {e}")
        return None


if __name__ == "__main__":
    test_1d_cnn()
