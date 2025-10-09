import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UploadAnalysis = ({ onAnalysisComplete }) => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, uploaded, analyzing, complete, error
  const [uploadResult, setUploadResult] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisSettings, setAnalysisSettings] = useState({
    apply_filtering: true,
    apply_wavelet: false,
    include_features: true,
    confidence_threshold: 0.7
  });
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setUploadResult(null);
    setAnalysisResult(null);
    setError(null);
    setUploadStatus('idle');
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, []);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setUploadStatus('uploading');
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      setUploadStatus('uploaded');
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error.response?.data?.detail || 'Upload failed');
      setUploadStatus('error');
    }
  };

  const handleAnalyze = async () => {
    if (!uploadResult?.upload_id) return;

    setUploadStatus('analyzing');
    setError(null);

    try {
      const response = await axios.post(
        `${API}/analyze/${uploadResult.upload_id}`,
        analysisSettings
      );

      setAnalysisResult(response.data);
      setUploadStatus('complete');
      
      // Notify parent component to refresh data
      if (onAnalysisComplete) {
        onAnalysisComplete();
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setError(error.response?.data?.detail || 'Analysis failed');
      setUploadStatus('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadResult(null);
    setAnalysisResult(null);
    setError(null);
    setUploadStatus('idle');
  };

  const getFaultColor = (faultType) => {
    if (faultType === 'healthy') return '#16a34a';
    return '#dc2626';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'mild': return '#f59e0b';
      case 'moderate': return '#f97316';
      case 'severe': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const formatProbability = (value) => {
    return (value * 100).toFixed(1) + '%';
  };

  // Prepare chart data for FRA visualization
  const getChartData = () => {
    if (!uploadResult?.measurement_summary) return [];
    
    // This is a simplified visualization - in a real app, you'd get the actual frequency response data
    const frequencies = uploadResult.measurement_summary.frequency_range;
    const points = [];
    
    for (let i = 0; i <= 50; i++) {
      const freq = frequencies[0] * Math.pow(frequencies[1] / frequencies[0], i / 50);
      const magnitude = 40 - 10 * Math.log10(freq / frequencies[0]) + 5 * Math.sin(i / 5);
      points.push({
        frequency: freq,
        magnitude: magnitude,
        displayFreq: freq >= 1000000 ? `${(freq / 1000000).toFixed(1)}M` : 
                   freq >= 1000 ? `${(freq / 1000).toFixed(0)}k` : `${freq.toFixed(0)}`
      });
    }
    
    return points;
  };

  return (
    <div className="upload-analysis fade-in">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Upload & Analyze FRA Data</h1>
        <p className="page-subtitle">
          Upload transformer FRA measurement files for AI-powered fault analysis
        </p>
      </div>

      <div className="upload-container">
        {/* File Upload Section */}
        <div className="card upload-card">
          <div className="card-header">
            <h2 className="card-title">Upload FRA File</h2>
            <p className="card-subtitle">Supported formats: CSV, XML, JSON, and proprietary binary formats</p>
          </div>
          <div className="card-content">
            {!file ? (
              <div
                className={`file-drop-zone ${dragOver ? 'drag-over' : ''}`}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                data-testid="file-drop-zone"
              >
                <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <div className="upload-text">
                  <h3>Drop your FRA file here</h3>
                  <p>or click to browse files</p>
                  <input
                    type="file"
                    className="file-input"
                    accept=".csv,.xml,.json,.frx,.dbl,.meg,.n4f,.txt"
                    onChange={(e) => e.target.files[0] && handleFileSelect(e.target.files[0])}
                    data-testid="file-input"
                  />
                </div>
                <div className="supported-formats">
                  <span className="format-badge">CSV</span>
                  <span className="format-badge">XML</span>
                  <span className="format-badge">JSON</span>
                  <span className="format-badge">Omicron</span>
                  <span className="format-badge">Doble</span>
                  <span className="format-badge">Megger</span>
                </div>
              </div>
            ) : (
              <div className="file-selected">
                <div className="file-info">
                  <svg className="file-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <div className="file-details">
                    <h4>{file.name}</h4>
                    <p>{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
                <div className="file-actions">
                  <button 
                    className="btn btn-secondary"
                    onClick={handleReset}
                    data-testid="remove-file-btn"
                  >
                    Remove
                  </button>
                  <button 
                    className="btn btn-primary"
                    onClick={handleUpload}
                    disabled={uploadStatus === 'uploading'}
                    data-testid="upload-file-btn"
                  >
                    {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload File'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Analysis Settings */}
        {file && (
          <div className="card settings-card">
            <div className="card-header">
              <h2 className="card-title">Analysis Settings</h2>
              <p className="card-subtitle">Configure preprocessing and analysis parameters</p>
            </div>
            <div className="card-content">
              <div className="settings-grid">
                <div className="setting-item">
                  <label className="setting-label">
                    <input
                      type="checkbox"
                      checked={analysisSettings.apply_filtering}
                      onChange={(e) => setAnalysisSettings(prev => ({...prev, apply_filtering: e.target.checked}))}
                    />
                    Apply Savitzky-Golay Filtering
                  </label>
                  <p className="setting-description">Smooths the FRA data to reduce measurement noise</p>
                </div>
                
                <div className="setting-item">
                  <label className="setting-label">
                    <input
                      type="checkbox"
                      checked={analysisSettings.apply_wavelet}
                      onChange={(e) => setAnalysisSettings(prev => ({...prev, apply_wavelet: e.target.checked}))}
                    />
                    Apply Wavelet Denoising
                  </label>
                  <p className="setting-description">Advanced noise reduction using wavelet transforms</p>
                </div>
                
                <div className="setting-item">
                  <label className="setting-label">
                    <input
                      type="checkbox"
                      checked={analysisSettings.include_features}
                      onChange={(e) => setAnalysisSettings(prev => ({...prev, include_features: e.target.checked}))}
                    />
                    Extract Engineered Features
                  </label>
                  <p className="setting-description">Extract statistical and spectral features for ML analysis</p>
                </div>
                
                <div className="setting-item">
                  <label className="setting-label">
                    Confidence Threshold: {analysisSettings.confidence_threshold}
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="0.95"
                    step="0.05"
                    value={analysisSettings.confidence_threshold}
                    onChange={(e) => setAnalysisSettings(prev => ({...prev, confidence_threshold: parseFloat(e.target.value)}))}
                    className="setting-slider"
                  />
                  <p className="setting-description">Minimum confidence required for fault classification</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Status */}
      {uploadStatus !== 'idle' && (
        <div className="progress-section">
          <div className="progress-card">
            <div className="progress-header">
              <h3>Analysis Progress</h3>
              <div className="progress-status">
                {uploadStatus === 'uploading' && (
                  <><div className="spinner"></div> Uploading file...</>
                )}
                {uploadStatus === 'uploaded' && (
                  <><div className="check-icon">✓</div> File uploaded successfully</>
                )}
                {uploadStatus === 'analyzing' && (
                  <><div className="spinner"></div> Analyzing FRA data...</>
                )}
                {uploadStatus === 'complete' && (
                  <><div className="check-icon">✓</div> Analysis complete</>
                )}
                {uploadStatus === 'error' && (
                  <><div className="error-icon">✗</div> Error occurred</>
                )}
              </div>
            </div>
            
            <div className="progress-steps">
              <div className={`step ${uploadStatus !== 'idle' ? 'active' : ''}`}>1. File Upload</div>
              <div className={`step ${['uploaded', 'analyzing', 'complete'].includes(uploadStatus) ? 'active' : ''}`}>2. Data Parsing</div>
              <div className={`step ${['analyzing', 'complete'].includes(uploadStatus) ? 'active' : ''}`}>3. ML Analysis</div>
              <div className={`step ${uploadStatus === 'complete' ? 'active' : ''}`}>4. Results</div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <div className="results-section">
          <div className="card result-card">
            <div className="card-header">
              <h2 className="card-title">Parsing Results</h2>
              <p className="card-subtitle">File successfully parsed and validated</p>
            </div>
            <div className="card-content">
              <div className="result-grid">
                <div className="result-item">
                  <span className="result-label">Asset ID:</span>
                  <span className="result-value">{uploadResult.asset_metadata?.asset_id}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Manufacturer:</span>
                  <span className="result-value">{uploadResult.asset_metadata?.manufacturer}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Model:</span>
                  <span className="result-value">{uploadResult.asset_metadata?.model}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Frequency Points:</span>
                  <span className="result-value">{uploadResult.measurement_summary?.frequency_points}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Frequency Range:</span>
                  <span className="result-value">
                    {uploadResult.measurement_summary?.frequency_range?.[0]?.toLocaleString()} - 
                    {uploadResult.measurement_summary?.frequency_range?.[1]?.toLocaleString()} Hz
                  </span>
                </div>
                <div className="result-item">
                  <span className="result-label">Unit:</span>
                  <span className="result-value">{uploadResult.measurement_summary?.unit}</span>
                </div>
              </div>
              
              {uploadStatus === 'uploaded' && (
                <div className="analyze-section">
                  <button 
                    className="btn btn-primary btn-large"
                    onClick={handleAnalyze}
                    data-testid="analyze-btn"
                  >
                    Start AI Analysis
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* FRA Data Visualization */}
          <div className="card chart-card">
            <div className="card-header">
              <h2 className="card-title">FRA Response Preview</h2>
              <p className="card-subtitle">Frequency response magnitude plot</p>
            </div>
            <div className="card-content">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="displayFreq" 
                    tick={{fontSize: 12}}
                  />
                  <YAxis 
                    label={{ value: 'Magnitude (dB)', angle: -90, position: 'insideLeft' }}
                    tick={{fontSize: 12}}
                  />
                  <Tooltip 
                    formatter={(value, name) => [value.toFixed(2) + ' dB', 'Magnitude']}
                    labelFormatter={(label) => `Frequency: ${label}Hz`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="magnitude" 
                    stroke="#2563eb" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="analysis-results">
          {/* Main Diagnosis Card */}
          <div className="card diagnosis-card">
            <div className="card-header">
              <h2 className="card-title">AI Diagnosis Results</h2>
              <p className="card-subtitle">Machine learning analysis complete</p>
            </div>
            <div className="card-content">
              <div className="diagnosis-main">
                <div className="fault-result">
                  <div className="fault-type">
                    <h3 style={{color: getFaultColor(analysisResult.predicted_fault_type)}}>
                      {analysisResult.predicted_fault_type.replace('_', ' ').toUpperCase()}
                    </h3>
                    {analysisResult.predicted_fault_type !== 'healthy' && (
                      <span 
                        className="severity-badge"
                        style={{backgroundColor: getSeverityColor(analysisResult.severity_level)}}
                      >
                        {analysisResult.severity_level}
                      </span>
                    )}
                  </div>
                  <div className="confidence-score">
                    <div className="confidence-label">Confidence Score</div>
                    <div className="confidence-value">
                      {formatProbability(analysisResult.confidence_score)}
                    </div>
                  </div>
                </div>
                
                <div className="anomaly-result">
                  <div className="anomaly-item">
                    <span className="anomaly-label">Anomaly Score:</span>
                    <span className="anomaly-value">{analysisResult.anomaly_score?.toFixed(4) || 'N/A'}</span>
                  </div>
                  <div className="anomaly-item">
                    <span className="anomaly-label">Is Anomaly:</span>
                    <span className={`anomaly-indicator ${analysisResult.is_anomaly ? 'anomaly' : 'normal'}`}>
                      {analysisResult.is_anomaly ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Fault Probabilities */}
          <div className="card probabilities-card">
            <div className="card-header">
              <h2 className="card-title">Fault Probabilities</h2>
              <p className="card-subtitle">Likelihood of different fault types</p>
            </div>
            <div className="card-content">
              <div className="probabilities-list">
                {Object.entries(analysisResult.fault_probabilities).map(([faultType, probability]) => (
                  <div key={faultType} className="probability-item">
                    <div className="probability-label">
                      {faultType.replace('_', ' ')}
                    </div>
                    <div className="probability-bar">
                      <div 
                        className="probability-fill"
                        style={{
                          width: `${probability * 100}%`,
                          backgroundColor: faultType === analysisResult.predicted_fault_type ? 
                            getFaultColor(faultType) : '#e5e7eb'
                        }}
                      ></div>
                    </div>
                    <div className="probability-value">
                      {formatProbability(probability)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="card recommendations-card">
            <div className="card-header">
              <h2 className="card-title">Maintenance Recommendations</h2>
              <p className="card-subtitle">Expert system recommendations based on analysis</p>
            </div>
            <div className="card-content">
              <div className="recommendations-list">
                {analysisResult.recommended_actions?.map((action, index) => (
                  <div key={index} className="recommendation-item">
                    <div className="recommendation-icon">
                      {action.includes('URGENT') || action.includes('CRITICAL') ? (
                        <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <div className="recommendation-text">{action}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-card">
          <div className="error-content">
            <svg className="error-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="error-text">
              <h3>Error</h3>
              <p>{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadAnalysis;