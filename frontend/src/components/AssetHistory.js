import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LineChart from 'recharts/lib/chart/LineChart';
import Line from 'recharts/lib/cartesian/Line';
import XAxis from 'recharts/lib/cartesian/XAxis';
import YAxis from 'recharts/lib/cartesian/YAxis';
import CartesianGrid from 'recharts/lib/cartesian/CartesianGrid';
import Tooltip from 'recharts/lib/component/Tooltip';
import Legend from 'recharts/lib/component/Legend';
import ResponsiveContainer from 'recharts/lib/component/ResponsiveContainer';
import AnalysisDetailView from './AnalysisDetailView';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AssetHistory = ({ assets }) => {
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [assetHistory, setAssetHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState(null);

  useEffect(() => {
    if (assets.length > 0 && !selectedAsset) {
      setSelectedAsset(assets[0].asset_id);
    }
  }, [assets, selectedAsset]);

  useEffect(() => {
    if (selectedAsset) {
      loadAssetHistory(selectedAsset);
    }
  }, [selectedAsset]);

  const loadAssetHistory = async (assetId) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API}/asset/${assetId}/history?limit=50`);
      setAssetHistory(response.data);
    } catch (error) {
      console.error('Failed to load asset history:', error);
      setError('Failed to load asset history');
      setAssetHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFaultBadgeClass = (faultType) => {
    if (faultType === 'healthy') return 'badge healthy';
    return 'badge fault';
  };

  const getSeverityBadgeClass = (severity) => {
    return `badge ${severity}`;
  };

  const getFaultColor = (faultType) => {
    if (faultType === 'healthy') return '#16a34a';
    return '#dc2626';
  };

  // Prepare trend data for chart
  const getTrendData = () => {
    return assetHistory
      .slice()
      .reverse()
      .map((analysis, index) => ({
        index: index + 1,
        date: new Date(analysis.analysis_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        confidence: Math.round(analysis.confidence_score * 100),
        isHealthy: analysis.fault_type === 'healthy' ? 100 : 0,
        isFaulty: analysis.fault_type !== 'healthy' ? 100 : 0
      }));
  };

  const currentAsset = assets.find(a => a.asset_id === selectedAsset);

  return (
    <div className="asset-history fade-in">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Asset History & Trends</h1>
        <p className="page-subtitle">
          Track transformer health over time and analyze diagnostic trends
        </p>
      </div>

      {/* Asset Selection */}
      <div className="asset-selector">
        <div className="card selector-card">
          <div className="card-header">
            <h2 className="card-title">Select Asset</h2>
            <p className="card-subtitle">Choose a transformer to view its diagnostic history</p>
          </div>
          <div className="card-content">
            {assets.length === 0 ? (
              <div className="empty-state">
                <p>No assets found. Upload FRA data to start tracking transformers.</p>
              </div>
            ) : (
              <div className="asset-grid">
                {assets.map((asset) => (
                  <button
                    key={asset.asset_id}
                    className={`asset-option ${
                      selectedAsset === asset.asset_id ? 'selected' : ''
                    }`}
                    onClick={() => setSelectedAsset(asset.asset_id)}
                    data-testid={`asset-${asset.asset_id}`}
                  >
                    <div className="asset-option-header">
                      <h3>{asset.asset_id}</h3>
                      <span className={getFaultBadgeClass(asset.latest_fault_type)}>
                        {asset.latest_fault_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="asset-option-details">
                      <div className="detail-row">
                        <span>Last Analysis:</span>
                        <span>{formatDate(asset.latest_analysis)}</span>
                      </div>
                      <div className="detail-row">
                        <span>Total Analyses:</span>
                        <span>{asset.total_analyses}</span>
                      </div>
                      <div className="detail-row">
                        <span>Confidence:</span>
                        <span>{Math.round(asset.latest_confidence * 100)}%</span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Asset Details & Trends */}
      {selectedAsset && (
        <div className="asset-details">
          {/* Current Status */}
          <div className="card status-card">
            <div className="card-header">
              <h2 className="card-title">Current Status - {selectedAsset}</h2>
              <p className="card-subtitle">Latest diagnostic information</p>
            </div>
            <div className="card-content">
              {currentAsset && (
                <div className="status-grid">
                  <div className="status-item">
                    <div className="status-label">Health Status</div>
                    <div className="status-value">
                      <span 
                        className={getFaultBadgeClass(currentAsset.latest_fault_type)}
                        style={{fontSize: '14px', padding: '8px 16px'}}
                      >
                        {currentAsset.latest_fault_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  
                  <div className="status-item">
                    <div className="status-label">Last Analysis</div>
                    <div className="status-value">{formatDate(currentAsset.latest_analysis)}</div>
                  </div>
                  
                  <div className="status-item">
                    <div className="status-label">Confidence Score</div>
                    <div className="status-value">{Math.round(currentAsset.latest_confidence * 100)}%</div>
                  </div>
                  
                  <div className="status-item">
                    <div className="status-label">Total Analyses</div>
                    <div className="status-value">{currentAsset.total_analyses}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Trend Chart */}
          {assetHistory.length > 1 && (
            <div className="card chart-card">
              <div className="card-header">
                <h2 className="card-title">Health Trend Analysis</h2>
                <p className="card-subtitle">Confidence scores and health status over time</p>
              </div>
              <div className="card-content">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getTrendData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{fontSize: 12}}
                    />
                    <YAxis 
                      label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft' }}
                      tick={{fontSize: 12}}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'confidence') return [value + '%', 'Confidence'];
                        return [value > 0 ? 'Yes' : 'No', name === 'isHealthy' ? 'Healthy' : 'Faulty'];
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="confidence" 
                      stroke="#2563eb" 
                      strokeWidth={2}
                      name="Confidence"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* History Table */}
          <div className="card history-card">
            <div className="card-header">
              <h2 className="card-title">Analysis History</h2>
              <p className="card-subtitle">Detailed history of all diagnostic analyses</p>
            </div>
            <div className="card-content">
              {loading ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <p>Loading history...</p>
                </div>
              ) : error ? (
                <div className="error-message">
                  <p>{error}</p>
                </div>
              ) : assetHistory.length === 0 ? (
                <div className="empty-state">
                  <p>No analysis history found for this asset.</p>
                </div>
              ) : (
                <div className="history-table">
                  <div className="table-header">
                    <div className="table-cell">Date & Time</div>
                    <div className="table-cell">Filename</div>
                    <div className="table-cell">Fault Type</div>
                    <div className="table-cell">Severity</div>
                    <div className="table-cell">Confidence</div>
                    <div className="table-cell">Actions</div>
                  </div>
                  
                  <div className="table-body">
                    {assetHistory.map((analysis) => (
                      <div key={analysis.analysis_id} className="table-row" data-testid={`history-row-${analysis.analysis_id}`}>
                        <div className="table-cell">
                          <div className="date-time">
                            <div className="date">{formatDate(analysis.analysis_date)}</div>
                          </div>
                        </div>
                        
                        <div className="table-cell">
                          <div className="filename">{analysis.filename}</div>
                        </div>
                        
                        <div className="table-cell">
                          <span className={getFaultBadgeClass(analysis.fault_type)}>
                            {analysis.fault_type.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="table-cell">
                          {analysis.fault_type !== 'healthy' && analysis.severity_level && (
                            <span className={getSeverityBadgeClass(analysis.severity_level)}>
                              {analysis.severity_level}
                            </span>
                          )}
                        </div>
                        
                        <div className="table-cell">
                          <div className="confidence-indicator">
                            <div 
                              className="confidence-bar"
                              style={{
                                width: `${analysis.confidence_score * 100}%`,
                                backgroundColor: getFaultColor(analysis.fault_type)
                              }}
                            ></div>
                            <span className="confidence-text">
                              {Math.round(analysis.confidence_score * 100)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="table-cell">
                          <button 
                            className="btn btn-secondary btn-small"
                            onClick={() => setSelectedAnalysisId(analysis.analysis_id)}
                            data-testid={`view-analysis-${analysis.analysis_id}`}
                          >
                            View Details
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Analysis Detail View Modal */}
      {selectedAnalysisId && (
        <AnalysisDetailView
          analysisId={selectedAnalysisId}
          onClose={() => setSelectedAnalysisId(null)}
        />
      )}
    </div>
  );
};

export default AssetHistory;