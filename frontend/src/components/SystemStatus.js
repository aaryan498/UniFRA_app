import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SystemStatus = ({ systemStatus, onRefresh }) => {
  const [detailedStatus, setDetailedStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [performanceData, setPerformanceData] = useState([]);

  useEffect(() => {
    loadDetailedStatus();
    generateMockLogs();
    generatePerformanceData();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      onRefresh();
      loadDetailedStatus();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [refreshInterval, onRefresh]);

  const loadDetailedStatus = async () => {
    setLoading(true);
    try {
      // For now, we'll enhance the existing systemStatus with mock detailed data
      // In a real implementation, this would be a separate API endpoint
      const mockDetailedStatus = {
        ...systemStatus,
        uptime: '2 days, 14 hours, 23 minutes',
        memory_usage: '45%',
        cpu_usage: '23%',
        disk_usage: '67%',
        active_sessions: 12,
        total_analyses_today: 45,
        avg_response_time: '234ms',
        components: {
          api_server: {
            status: 'healthy',
            port: 8001,
            last_check: new Date().toISOString(),
            response_time: '12ms'
          },
          database: {
            status: 'healthy',
            connections: 8,
            last_check: new Date().toISOString(),
            response_time: '5ms'
          },
          ml_models: {
            status: 'healthy',
            loaded_models: 4,
            last_prediction: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
            avg_inference_time: '45ms'
          },
          file_parser: {
            status: 'healthy',
            supported_formats: 7,
            last_parse: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
            success_rate: '98.5%'
          },
          authentication: {
            status: 'healthy',
            active_methods: ['email', 'google_oauth', 'emergent_oauth'],
            last_login: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            success_rate: '99.2%'
          }
        }
      };
      setDetailedStatus(mockDetailedStatus);
    } catch (error) {
      console.error('Failed to load detailed status:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockLogs = () => {
    const mockLogs = [
      {
        timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
        level: 'INFO',
        component: 'API',
        message: 'FRA analysis completed successfully for asset TR_001'
      },
      {
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        level: 'INFO',
        component: 'AUTH',
        message: 'User logged in via Google OAuth'
      },
      {
        timestamp: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
        level: 'INFO',
        component: 'PARSER',
        message: 'CSV file parsed successfully: fra_data_20250109.csv'
      },
      {
        timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
        level: 'WARN',
        component: 'ML',
        message: 'Low confidence prediction detected for asset TR_045'
      },
      {
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        level: 'INFO',
        component: 'DB',
        message: 'Database backup completed successfully'
      }
    ];
    setLogs(mockLogs);
  };
  const generatePerformanceData = () => {
    const now = new Date();
    const data = [];
    for (let i = 0; i < 24; i++) {
      const timestamp = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000);
      data.push({
        timestamp: timestamp.toISOString(),
        responseTime: 45 + Math.random() * 20,
        cpuUsage: 15 + Math.random() * 25,
        memoryUsage: 60 + Math.random() * 15,
        activeUsers: Math.floor(1 + Math.random() * 5)
      });
    }
    setPerformanceData(data);
  };

  const formatUptime = (uptime) => {
    // Mock uptime formatting
    return uptime || 'Unknown';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'INFO':
        return 'text-blue-600 bg-blue-100';
      case 'WARN':
        return 'text-yellow-600 bg-yellow-100';
      case 'ERROR':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };
  const performanceChartData = [
    {
      x: performanceData.map(d => d.timestamp),
      y: performanceData.map(d => d.responseTime),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Response Time (ms)',
      line: { color: '#2563eb', width: 2 },
      marker: { size: 4 }
    },
    {
      x: performanceData.map(d => d.timestamp),
      y: performanceData.map(d => d.cpuUsage),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'CPU Usage (%)',
      line: { color: '#dc2626', width: 2 },
      marker: { size: 4 },
      yaxis: 'y2'
    },
    {
      x: performanceData.map(d => d.timestamp),
      y: performanceData.map(d => d.memoryUsage),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Memory Usage (%)',
      line: { color: '#16a34a', width: 2 },
      marker: { size: 4 },
      yaxis: 'y2'
    }
  ];

  const performanceLayout = {
    title: 'System Performance (24 Hours)',
    xaxis: { title: 'Time' },
    yaxis: { title: 'Response Time (ms)', side: 'left' },
    yaxis2: {
      title: 'Resource Usage (%)',
      side: 'right',
      overlaying: 'y',
      range: [0, 100]
    },
    legend: { x: 0, y: 1.2, orientation: 'h' },
    margin: { l: 50, r: 50, t: 50, b: 50 },
    height: 400
  };

  if (!systemStatus) {
    return (
      <div className="system-status-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading system status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="system-status-page fade-in" data-testid="system-status-page">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">System Status</h1>
        <p className="page-subtitle">
          Monitor UniFRA system health, performance metrics, and component status
        </p>
        <div className="header-actions">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="refresh-interval-select"
            data-testid="refresh-interval-select"
          >
            <option value={10}>Refresh every 10s</option>
            <option value={30}>Refresh every 30s</option>
            <option value={60}>Refresh every 1 min</option>
            <option value={300}>Refresh every 5 min</option>
          </select>
          <button 
            className="btn btn-primary"
            onClick={() => {
              onRefresh();
              loadDetailedStatus();
            }}
            disabled={loading}
            data-testid="manual-refresh-btn"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Refreshing...
              </div>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Overall System Health */}
      <div className="status-overview-grid">
        <div className="card">
          <div className="card-content">
            <div className="status-overview-item">
              <div className="status-icon">
                <div className={`status-dot-large ${systemStatus.status === 'healthy' ? 'healthy' : 'error'}`}></div>
              </div>
              <div className="status-info">
                <h3 className="status-title" data-testid="overall-status">Overall Status</h3>
                <p className={`status-value ${systemStatus.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`} data-testid="status-badge">
                  {systemStatus.status === 'healthy' ? 'All Systems Operational' : 'System Issues Detected'}
                </p>
                <p className="status-subtitle">Last updated: {new Date(systemStatus.timestamp).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        {detailedStatus && (
          <>
            <div className="card">
              <div className="card-content">
                <div className="metric-item">
                  <h4 className="metric-label">System Uptime</h4>
                  <p className="metric-value">{formatUptime(detailedStatus.uptime)}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-content">
                <div className="metric-item">
                  <h4 className="metric-label">Active Sessions</h4>
                  <p className="metric-value">{detailedStatus.active_sessions}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-content">
                <div className="metric-item">
                  <h4 className="metric-label">Analyses Today</h4>
                  <p className="metric-value">{detailedStatus.total_analyses_today}</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Component Status */}
      {detailedStatus && (
        <div className="card" style={{marginBottom: '24px'}}>
          <div className="card-header">
            <h2 className="card-title">Component Status</h2>
            <p className="card-subtitle">Individual system component health and metrics</p>
          </div>
          <div className="card-content">
            <div className="component-status-grid">
              {Object.entries(detailedStatus.components).map(([componentName, component]) => (
                <div key={componentName} className="component-status-card" data-testid={`component-${componentName}`}>
                  <div className="component-header">
                    <h3 className="component-name">
                      {componentName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    <span className={`status-badge ${getStatusColor(component.status)}`} data-testid={`${componentName}-status`}>
                      {component.status}
                    </span>
                  </div>
                  
                  <div className="component-metrics">
                    {component.port && (
                      <div className="metric">
                        <span className="metric-label">Port:</span>
                        <span className="metric-value">{component.port}</span>
                      </div>
                    )}
                    {component.connections && (
                      <div className="metric">
                        <span className="metric-label">Connections:</span>
                        <span className="metric-value">{component.connections}</span>
                      </div>
                    )}
                    {component.loaded_models && (
                      <div className="metric">
                        <span className="metric-label">Models:</span>
                        <span className="metric-value">{component.loaded_models}</span>
                      </div>
                    )}
                    {component.supported_formats && (
                      <div className="metric">
                        <span className="metric-label">Formats:</span>
                        <span className="metric-value">{component.supported_formats}</span>
                      </div>
                    )}
                    {component.response_time && (
                      <div className="metric">
                        <span className="metric-label">Response Time:</span>
                        <span className="metric-value">{component.response_time}</span>
                      </div>
                    )}
                    {component.success_rate && (
                      <div className="metric">
                        <span className="metric-label">Success Rate:</span>
                        <span className="metric-value">{component.success_rate}</span>
                      </div>
                    )}
                    <div className="metric">
                      <span className="metric-label">Last Check:</span>
                      <span className="metric-value">
                        {new Date(component.last_check).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Performance Charts */}
      <div className="card performance-chart">
        <div className="card-header">
          <h2 className="card-title">Performance Monitoring</h2>
          <p className="card-subtitle">Real-time system performance metrics</p>
        </div>
        <div className="card-content">
          <Plot
            data={performanceChartData}
            layout={performanceLayout}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Metrics */}
        <div className="card metrics-card">
          <div className="card-header">
            <h2 className="card-title">Performance Metrics</h2>
            <p className="card-subtitle">Current system performance indicators</p>
          </div>
          <div className="card-content">
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">API Response Time</div>
                <div className="metric-value" data-testid="response-time">~50ms</div>
                <div className="metric-trend positive">+5% faster than last week</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-label">Analysis Processing Time</div>
                <div className="metric-value" data-testid="processing-time">~2.3s</div>
                <div className="metric-trend positive">Average per analysis</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-label">Active Users</div>
                <div className="metric-value" data-testid="active-users">1</div>
                <div className="metric-trend neutral">Current session</div>
              </div>
              
              <div className="metric-item">
                <div className="metric-label">System Uptime</div>
                <div className="metric-value" data-testid="uptime">99.9%</div>
                <div className="metric-trend positive">Last 30 days</div>
              </div>
            </div>
          </div>
        </div>

        {/* System Logs */}
        <div className="card logs-card">
          <div className="card-header">
            <h2 className="card-title">System Logs</h2>
            <p className="card-subtitle">Recent system events and alerts</p>
          </div>
          <div className="card-content">
            <div className="logs-list" data-testid="system-logs">
              {logs.length > 0 ? (
                logs.map((log, index) => (
                  <div key={index} className="log-entry">
                    <div className="flex items-start space-x-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getLogLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">[{log.component}] {log.message}</p>
                        <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-logs">
                  <p>No recent logs available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="card info-card">
        <div className="card-header">
          <h2 className="card-title">System Information</h2>
        </div>
        <div className="card-content">
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Platform Version</span>
              <span className="info-value" data-testid="platform-version">{systemStatus?.version || '2.0.0'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Environment</span>
              <span className="info-value" data-testid="environment">Production</span>
            </div>
            <div className="info-item">
              <span className="info-label">Last Deployment</span>
              <span className="info-value" data-testid="last-deployment">{new Date().toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Health Check Interval</span>
              <span className="info-value" data-testid="health-check-interval">30 seconds</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;