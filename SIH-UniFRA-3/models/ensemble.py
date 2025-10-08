#!/usr/bin/env python3
"""
Ensemble Methods for FRA Fault Classification

Implements model ensembling, stacking, and calibration utilities for improved 
FRA fault diagnosis accuracy and confidence estimation.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, confusion_matrix
from typing import Dict, List, Tuple, Optional, Any
import logging
import joblib

logger = logging.getLogger(__name__)

class FRAEnsembleModel:
    """Ensemble model combining multiple approaches for robust FRA fault diagnosis."""
    
    def __init__(self):
        self.models = {}
        self.feature_model = None  # For traditional ML on engineered features
        self.cnn_1d_model = None   # 1D CNN model
        self.cnn_2d_model = None   # 2D CNN model
        self.autoencoder = None    # Autoencoder for anomaly detection
        
        # Ensemble weights (learned or manually tuned)
        self.ensemble_weights = {
            'feature_model': 0.3,
            'cnn_1d': 0.4,
            'cnn_2d': 0.2,
            'autoencoder': 0.1
        }
        
        # Meta-classifier for stacking
        self.meta_classifier = None
        
        # Fault type and severity mappings
        self.fault_classes = [
            'healthy', 'axial_displacement', 'radial_deformation', 
            'core_grounding', 'turn_turn_short', 'open_circuit',
            'insulation_degradation', 'partial_discharge', 
            'lamination_deform', 'saturation_effect'
        ]
        
        self.severity_classes = ['mild', 'moderate', 'severe']
    
    def add_feature_model(self, model_type: str = 'random_forest', **kwargs):
        """Add traditional ML model for engineered features.
        
        Args:
            model_type: Type of model ('random_forest', 'logistic_regression')
            **kwargs: Model parameters
        """
        if model_type == 'random_forest':
            # Multi-output Random Forest for fault type and severity
            self.feature_model = {
                'fault': RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 200),
                    max_depth=kwargs.get('max_depth', None),
                    min_samples_split=kwargs.get('min_samples_split', 5),
                    random_state=42,
                    n_jobs=-1
                ),
                'severity': RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', 10),
                    min_samples_split=kwargs.get('min_samples_split', 5),
                    random_state=42,
                    n_jobs=-1
                )
            }
        elif model_type == 'logistic_regression':
            # Calibrated logistic regression
            self.feature_model = {
                'fault': CalibratedClassifierCV(
                    LogisticRegression(
                        max_iter=kwargs.get('max_iter', 1000),
                        random_state=42
                    ),
                    method='isotonic',
                    cv=3
                ),
                'severity': CalibratedClassifierCV(
                    LogisticRegression(
                        max_iter=kwargs.get('max_iter', 1000),
                        random_state=42
                    ),
                    method='isotonic',
                    cv=3
                )
            }
        
        logger.info(f"Added {model_type} feature model")
    
    def add_cnn_models(self, cnn_1d_model=None, cnn_2d_model=None):
        """Add CNN models to ensemble.
        
        Args:
            cnn_1d_model: Trained 1D CNN model
            cnn_2d_model: Trained 2D CNN model
        """
        if cnn_1d_model is not None:
            self.cnn_1d_model = cnn_1d_model
            self.cnn_1d_model.eval()
            logger.info("Added 1D CNN model")
        
        if cnn_2d_model is not None:
            self.cnn_2d_model = cnn_2d_model
            self.cnn_2d_model.eval()
            logger.info("Added 2D CNN model")
    
    def add_autoencoder(self, autoencoder):
        """Add autoencoder for anomaly detection.
        
        Args:
            autoencoder: Trained autoencoder model
        """
        self.autoencoder = autoencoder
        self.autoencoder.eval()
        logger.info("Added autoencoder model")
    
    def train_feature_models(self, X_features: np.ndarray, 
                           y_fault: np.ndarray, 
                           y_severity: np.ndarray):
        """Train traditional ML models on engineered features.
        
        Args:
            X_features: Feature matrix (n_samples, n_features)
            y_fault: Fault type labels
            y_severity: Severity level labels
        """
        if self.feature_model is None:
            raise ValueError("Feature model not initialized. Call add_feature_model() first.")
        
        logger.info("Training feature models...")
        
        # Train fault classifier
        self.feature_model['fault'].fit(X_features, y_fault)
        
        # Train severity classifier (only on faulty samples)
        faulty_mask = y_fault != 0  # Assuming 0 is healthy class
        if np.any(faulty_mask):
            X_faulty = X_features[faulty_mask]
            y_severity_faulty = y_severity[faulty_mask]
            self.feature_model['severity'].fit(X_faulty, y_severity_faulty)
        
        logger.info("Feature models training completed")
    
    def predict_features(self, X_features: np.ndarray) -> Dict[str, np.ndarray]:
        """Make predictions using feature-based models.
        
        Args:
            X_features: Feature matrix
            
        Returns:
            Dictionary of predictions and probabilities
        """
        if self.feature_model is None:
            return {'fault_proba': None, 'severity_proba': None}
        
        # Fault predictions
        fault_proba = self.feature_model['fault'].predict_proba(X_features)
        fault_pred = np.argmax(fault_proba, axis=1)
        
        # Severity predictions (only for faulty samples)
        severity_proba = np.zeros((len(X_features), len(self.severity_classes)))
        severity_pred = np.zeros(len(X_features), dtype=int)
        
        faulty_mask = fault_pred != 0  # Non-healthy predictions
        if np.any(faulty_mask) and len(X_features[faulty_mask]) > 0:
            severity_proba_faulty = self.feature_model['severity'].predict_proba(X_features[faulty_mask])
            severity_proba[faulty_mask] = severity_proba_faulty
            severity_pred[faulty_mask] = np.argmax(severity_proba_faulty, axis=1)
        
        return {
            'fault_proba': fault_proba,
            'fault_pred': fault_pred,
            'severity_proba': severity_proba,
            'severity_pred': severity_pred
        }
    
    def predict_cnn_1d(self, X_signal: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Make predictions using 1D CNN model.
        
        Args:
            X_signal: Signal tensor (batch_size, signal_length)
            
        Returns:
            Dictionary of predictions and probabilities
        """
        if self.cnn_1d_model is None:
            return {'fault_proba': None, 'severity_proba': None}
        
        with torch.no_grad():
            fault_logits, severity_logits, anomaly_logits = self.cnn_1d_model(X_signal)
            
            fault_proba = F.softmax(fault_logits, dim=1)
            severity_proba = F.softmax(severity_logits, dim=1)
            anomaly_proba = F.softmax(anomaly_logits, dim=1)
            
            fault_pred = torch.argmax(fault_proba, dim=1)
            severity_pred = torch.argmax(severity_proba, dim=1)
        
        return {
            'fault_proba': fault_proba,
            'fault_pred': fault_pred,
            'severity_proba': severity_proba,
            'severity_pred': severity_pred,
            'anomaly_proba': anomaly_proba
        }
    
    def predict_cnn_2d(self, X_image: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Make predictions using 2D CNN model.
        
        Args:
            X_image: Image tensor (batch_size, height, width)
            
        Returns:
            Dictionary of predictions and probabilities
        """
        if self.cnn_2d_model is None:
            return {'fault_proba': None, 'severity_proba': None}
        
        with torch.no_grad():
            fault_logits, severity_logits, anomaly_logits = self.cnn_2d_model(X_image)
            
            fault_proba = F.softmax(fault_logits, dim=1)
            severity_proba = F.softmax(severity_logits, dim=1)
            
            fault_pred = torch.argmax(fault_proba, dim=1)
            severity_pred = torch.argmax(severity_proba, dim=1)
        
        return {
            'fault_proba': fault_proba,
            'fault_pred': fault_pred,
            'severity_proba': severity_proba,
            'severity_pred': severity_pred
        }
    
    def predict_autoencoder(self, X_signal: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Make anomaly predictions using autoencoder.
        
        Args:
            X_signal: Signal tensor
            
        Returns:
            Dictionary of anomaly scores and predictions
        """
        if self.autoencoder is None:
            return {'anomaly_score': None, 'is_anomaly': None}
        
        with torch.no_grad():
            reconstruction_error = self.autoencoder.compute_reconstruction_error(X_signal)
            
            # Simple threshold-based anomaly detection
            # (In practice, threshold should be learned from validation data)
            threshold = 0.01  # Placeholder threshold
            is_anomaly = reconstruction_error > threshold
        
        return {
            'anomaly_score': reconstruction_error,
            'is_anomaly': is_anomaly
        }
    
    def ensemble_predict(self, fra_data: Dict) -> Dict[str, Any]:
        """Make ensemble predictions combining all models.
        
        Args:
            fra_data: Dictionary containing different data representations:
                - 'features': Engineered features (np.ndarray)
                - 'signal': 1D signal data (torch.Tensor)
                - 'image': 2D image data (torch.Tensor)
        
        Returns:
            Ensemble predictions with confidence scores
        """
        predictions = {}
        
        # Get predictions from each model
        if 'features' in fra_data:
            feature_pred = self.predict_features(fra_data['features'])
            predictions['features'] = feature_pred
        
        if 'signal' in fra_data:
            cnn_1d_pred = self.predict_cnn_1d(fra_data['signal'])
            predictions['cnn_1d'] = cnn_1d_pred
            
            autoencoder_pred = self.predict_autoencoder(fra_data['signal'])
            predictions['autoencoder'] = autoencoder_pred
        
        if 'image' in fra_data:
            cnn_2d_pred = self.predict_cnn_2d(fra_data['image'])
            predictions['cnn_2d'] = cnn_2d_pred
        
        # Combine predictions using weighted averaging
        ensemble_result = self._combine_predictions(predictions)
        
        return ensemble_result
    
    def _combine_predictions(self, predictions: Dict) -> Dict[str, Any]:
        """Combine predictions from multiple models using weighted averaging.
        
        Args:
            predictions: Dictionary of model predictions
            
        Returns:
            Combined ensemble predictions
        """
        fault_probas = []
        severity_probas = []
        weights = []
        
        # Collect fault probability predictions
        for model_name, pred in predictions.items():
            if pred.get('fault_proba') is not None:
                if isinstance(pred['fault_proba'], torch.Tensor):
                    fault_proba = pred['fault_proba'].cpu().numpy()
                else:
                    fault_proba = pred['fault_proba']
                
                fault_probas.append(fault_proba)
                
                # Get model weight
                if model_name == 'features':
                    weights.append(self.ensemble_weights['feature_model'])
                elif model_name == 'cnn_1d':
                    weights.append(self.ensemble_weights['cnn_1d'])
                elif model_name == 'cnn_2d':
                    weights.append(self.ensemble_weights['cnn_2d'])
        
        # Collect severity probability predictions
        severity_probas = []
        for model_name, pred in predictions.items():
            if pred.get('severity_proba') is not None:
                if isinstance(pred['severity_proba'], torch.Tensor):
                    severity_proba = pred['severity_proba'].cpu().numpy()
                else:
                    severity_proba = pred['severity_proba']
                
                severity_probas.append(severity_proba)
        
        # Weighted average of fault predictions
        if fault_probas:
            weights = np.array(weights) / np.sum(weights)  # Normalize weights
            ensemble_fault_proba = np.average(fault_probas, axis=0, weights=weights)
            ensemble_fault_pred = np.argmax(ensemble_fault_proba, axis=1)
        else:
            ensemble_fault_proba = None
            ensemble_fault_pred = None
        
        # Weighted average of severity predictions
        if severity_probas:
            ensemble_severity_proba = np.average(severity_probas, axis=0, weights=weights[:len(severity_probas)])
            ensemble_severity_pred = np.argmax(ensemble_severity_proba, axis=1)
        else:
            ensemble_severity_proba = None
            ensemble_severity_pred = None
        
        # Anomaly information
        anomaly_info = predictions.get('autoencoder', {})
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence(ensemble_fault_proba, ensemble_severity_proba)
        
        return {
            'fault_probabilities': ensemble_fault_proba,
            'fault_prediction': ensemble_fault_pred,
            'severity_probabilities': ensemble_severity_proba,
            'severity_prediction': ensemble_severity_pred,
            'anomaly_score': anomaly_info.get('anomaly_score'),
            'is_anomaly': anomaly_info.get('is_anomaly'),
            'confidence_scores': confidence_scores,
            'individual_predictions': predictions
        }
    
    def _calculate_confidence(self, fault_proba: Optional[np.ndarray], 
                            severity_proba: Optional[np.ndarray]) -> Dict[str, float]:
        """Calculate confidence scores for predictions.
        
        Args:
            fault_proba: Fault probability array
            severity_proba: Severity probability array
            
        Returns:
            Dictionary of confidence metrics
        """
        confidence = {}
        
        if fault_proba is not None:
            # Entropy-based confidence (lower entropy = higher confidence)
            fault_entropy = -np.sum(fault_proba * np.log(fault_proba + 1e-8), axis=1)
            max_entropy = np.log(len(self.fault_classes))
            fault_confidence = 1 - (fault_entropy / max_entropy)
            
            confidence['fault_confidence'] = float(np.mean(fault_confidence))
            confidence['fault_max_probability'] = float(np.max(fault_proba))
        
        if severity_proba is not None:
            severity_entropy = -np.sum(severity_proba * np.log(severity_proba + 1e-8), axis=1)
            max_entropy = np.log(len(self.severity_classes))
            severity_confidence = 1 - (severity_entropy / max_entropy)
            
            confidence['severity_confidence'] = float(np.mean(severity_confidence))
            confidence['severity_max_probability'] = float(np.max(severity_proba))
        
        return confidence
    
    def save_ensemble(self, filepath: str):
        """Save ensemble model to disk.
        
        Args:
            filepath: Path to save the ensemble
        """
        ensemble_data = {
            'feature_model': self.feature_model,
            'ensemble_weights': self.ensemble_weights,
            'fault_classes': self.fault_classes,
            'severity_classes': self.severity_classes
        }
        
        joblib.dump(ensemble_data, filepath)
        logger.info(f"Ensemble model saved to {filepath}")
    
    def load_ensemble(self, filepath: str):
        """Load ensemble model from disk.
        
        Args:
            filepath: Path to load the ensemble from
        """
        ensemble_data = joblib.load(filepath)
        
        self.feature_model = ensemble_data['feature_model']
        self.ensemble_weights = ensemble_data['ensemble_weights']
        self.fault_classes = ensemble_data['fault_classes']
        self.severity_classes = ensemble_data['severity_classes']
        
        logger.info(f"Ensemble model loaded from {filepath}")


# Test function
def test_ensemble():
    """Test ensemble model functionality."""
    print("\nTesting FRA Ensemble Model...")
    
    try:
        # Create ensemble
        ensemble = FRAEnsembleModel()
        
        # Add feature model
        ensemble.add_feature_model('random_forest', n_estimators=50)
        
        # Create mock data
        n_samples = 100
        n_features = 50
        
        X_features = np.random.randn(n_samples, n_features)
        y_fault = np.random.randint(0, len(ensemble.fault_classes), n_samples)
        y_severity = np.random.randint(0, len(ensemble.severity_classes), n_samples)
        
        # Train feature models
        ensemble.train_feature_models(X_features, y_fault, y_severity)
        
        # Test predictions
        feature_predictions = ensemble.predict_features(X_features[:10])
        
        print(f"✓ Feature model training and prediction successful")
        print(f"✓ Fault prediction shape: {feature_predictions['fault_proba'].shape}")
        print(f"✓ Severity prediction shape: {feature_predictions['severity_proba'].shape}")
        
        # Test ensemble prediction with mock data
        fra_data = {
            'features': X_features[:5]
        }
        
        ensemble_result = ensemble.ensemble_predict(fra_data)
        
        print(f"✓ Ensemble prediction successful")
        print(f"✓ Confidence scores: {ensemble_result['confidence_scores']}")
        
        return ensemble
        
    except Exception as e:
        print(f"✗ Ensemble test failed: {e}")
        return None


if __name__ == "__main__":
    test_ensemble()
