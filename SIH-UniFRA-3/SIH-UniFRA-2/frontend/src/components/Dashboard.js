import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AnalysisDetailView from './AnalysisDetailView';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, assets, systemStatus, onRefresh }) => {
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalAssets: 0,
    healthyAssets: 0,
    faultyAssets: 0,
    analysesToday: 0
  });
  const [selectedAnalysisId, setSelectedAnalysisId] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [assets]);

  const loadDashboardData = async () => {
    try {
      // Calculate statistics from assets data
      const totalAssets = assets.length;
      const healthyAssets = assets.filter(asset => 
        asset.latest_fault_type === 'healthy'
      ).length;
      const faultyAssets = totalAssets - healthyAssets;
      
      setStats({
        totalAssets,
        healthyAssets,
        faultyAssets,
        analysesToday: 0 // Would need to be calculated from actual analysis data
      });

      // Load recent analyses for the first few assets
      const recentAnalysesPromises = assets.slice(0, 5).map(async (asset) => {
        try {
          const response = await axios.get(`${API}/asset/${asset.asset_id}/history?limit=3`);
          return response.data;
        } catch (error) {
          console.error(`Failed to load history for ${asset.asset_id}:`, error);
          return [];
        }
      });

      const allAnalyses = await Promise.all(recentAnalysesPromises);
      const flatAnalyses = allAnalyses.flat()
        .sort((a, b) => new Date(b.analysis_date) - new Date(a.analysis_date))
        .slice(0, 10);

      setRecentAnalyses(flatAnalyses);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
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

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  const getProfilePicture = () => {
    if (user?.profile_picture) {
      return user.profile_picture;
    }
    return null;
  };

  const getInitials = () => {
    if (user?.full_name) {
      return user.full_name
        .split(' ')
        .map(name => name.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
    }
    return 'U';
  };

  return (
    <div className="dashboard fade-in">
      {/* User Profile Section - Centered at Top */}
      <div className="user-profile-section">
        <div className="user-profile-card">
          <div className="user-avatar-large">
            {getProfilePicture() ? (
              <img 
                src={getProfilePicture()} 
                alt="Profile"
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <div className="flex items-center justify-center w-full h-full bg-blue-600 text-white font-bold text-2xl">
                {getInitials()}
              </div>
            )}
          </div>
          <div className="user-profile-info">
            <h2 className="user-name-dashboard" data-testid="dashboard-user-name">
              {user?.full_name || 'Unknown User'}
            </h2>
            <p className="user-email-dashboard" data-testid="dashboard-user-email">
              {user?.email || 'No email'}
            </p>
            <div className="user-auth-badge">
              Signed in via {user?.auth_method?.replace('_', ' ') || 'Unknown'}
            </div>
          </div>
        </div>
      </div>

      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">FRA Diagnostics Dashboard</h1>
        <p className="page-subtitle">
          Monitor transformer health and analyze frequency response patterns
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="dashboard-grid">
        <div className="card stat-card">
          <div className="stat-value" data-testid="total-assets-count">{stats.totalAssets}</div>
          <div className="stat-label">Total Assets</div>
          <div className="stat-trend positive">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            Active monitoring
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-value" style={{color: '#16a34a'}} data-testid="healthy-assets-count">
            {stats.healthyAssets}
          </div>
          <div className="stat-label">Healthy Assets</div>
          <div className="stat-trend positive">
            {stats.totalAssets > 0 ? Math.round((stats.healthyAssets / stats.totalAssets) * 100) : 0}% of total
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-value" style={{color: '#dc2626'}} data-testid="faulty-assets-count">
            {stats.faultyAssets}
          </div>
          <div className="stat-label">Faults Detected</div>
          <div className="stat-trend negative">
            Requires attention
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-value" data-testid="analyses-today-count">{stats.analysesToday}</div>
          <div className="stat-label">Analyses Today</div>
          <div className="stat-trend positive">
            Last: {systemStatus?.timestamp ? formatDate(systemStatus.timestamp) : 'N/A'}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-content">
        {/* Asset Status Overview */}
        <div className="card" style={{marginBottom: '24px'}}>
          <div className="card-header">
            <h2 className="card-title">Asset Status Overview</h2>
            <p className="card-subtitle">Latest health status for all monitored transformers</p>
          </div>
          <div className="card-content">
            {assets.length === 0 ? (
              <div className="empty-state">
                <p>No assets found. Upload FRA data to start monitoring transformers.</p>
              </div>
            ) : (
              <div className="assets-grid">
                {assets.slice(0, 8).map((asset) => (
                  <div key={asset.asset_id} className="asset-card" data-testid={`asset-card-${asset.asset_id}`}>
                    <div className="asset-header">
                      <h3 className="asset-id">{asset.asset_id}</h3>
                      <span className={getFaultBadgeClass(asset.latest_fault_type)}>
                        {asset.latest_fault_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="asset-details">
                      <div className="asset-detail">
                        <span className="detail-label">Last Analysis:</span>
                        <span className="detail-value">
                          {formatDate(asset.latest_analysis)}
                        </span>
                      </div>
                      <div className="asset-detail">
                        <span className="detail-label">Confidence:</span>
                        <span className="detail-value">
                          {Math.round(asset.latest_confidence * 100)}%
                        </span>
                      </div>
                      <div className="asset-detail">
                        <span className="detail-label">Total Tests:</span>
                        <span className="detail-value">{asset.total_analyses}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Analyses */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Recent Analyses</h2>
            <p className="card-subtitle">Latest fault detection results across all assets</p>
          </div>
          <div className="card-content">
            {recentAnalyses.length === 0 ? (
              <div className="empty-state">
                <p>No recent analyses found. Start by uploading FRA data files.</p>
                <button 
                  className="btn btn-primary" 
                  onClick={() => window.location.href = '#upload'}
                  data-testid="upload-fra-data-btn"
                >
                  Upload FRA Data
                </button>
              </div>
            ) : (
              <div className="recent-analyses-list">
                {recentAnalyses.map((analysis) => (
                  <div key={analysis.analysis_id} className="analysis-item" data-testid={`analysis-item-${analysis.analysis_id}`}>
                    <div className="analysis-main">
                      <div className="analysis-asset">
                        <h4>{analysis.asset_id}</h4>
                        <span className="analysis-file">{analysis.filename}</span>
                      </div>
                      <div className="analysis-result">
                        <span className={getFaultBadgeClass(analysis.fault_type)}>
                          {analysis.fault_type.replace('_', ' ')}
                        </span>
                        {analysis.fault_type !== 'healthy' && (
                          <span className={getSeverityBadgeClass(analysis.severity_level)}>
                            {analysis.severity_level}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="analysis-meta">
                      <span className="analysis-date">
                        {formatDate(analysis.analysis_date)}
                      </span>
                      <span className="analysis-confidence">
                        {Math.round(analysis.confidence_score * 100)}% confidence
                      </span>
                      <button
                        onClick={() => setSelectedAnalysisId(analysis.analysis_id)}
                        className="btn btn-sm btn-outline ml-3"
                        data-testid={`view-details-${analysis.analysis_id}`}
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Status Card */}
      {systemStatus && (
        <div className="card system-status-card" style={{marginTop: '24px'}}>
          <div className="card-header">
            <h2 className="card-title">System Status</h2>
          </div>
          <div className="card-content">
            <div className="status-grid">
              <div className="status-item">
                <div className="status-label">API Status</div>
                <div className={`status-indicator ${
                  systemStatus.status === 'healthy' ? 'healthy' : 'error'
                }`}>
                  <div className="status-dot"></div>
                  {systemStatus.status === 'healthy' ? 'Operational' : 'Error'}
                </div>
              </div>
              
              <div className="status-item">
                <div className="status-label">Parser</div>
                <div className="status-indicator healthy">
                  <div className="status-dot"></div>
                  {systemStatus.components?.parser || 'Unknown'}
                </div>
              </div>
              
              <div className="status-item">
                <div className="status-label">ML Models</div>
                <div className="status-indicator healthy">
                  <div className="status-dot"></div>
                  {systemStatus.components?.ml_models || 'Unknown'}
                </div>
              </div>
              
              <div className="status-item">
                <div className="status-label">Database</div>
                <div className="status-indicator healthy">
                  <div className="status-dot"></div>
                  {systemStatus.components?.database || 'Unknown'}
                </div>
              </div>
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

export default Dashboard;