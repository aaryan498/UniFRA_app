import React from 'react';

const Sidebar = ({ isOpen, activeView, onViewChange, onToggle, systemStatus }) => {
  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'upload',
      label: 'Upload & Analyze',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      )
    },
    {
      id: 'history',
      label: 'Asset History',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      id: 'system-status',
      label: 'System Status',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  ];

  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          {isOpen && (
            <div className="brand-text">
              <h2 className="brand-title">UniFRA</h2>
              <p className="brand-subtitle">AI FRA Diagnostics</p>
            </div>
          )}
        </div>
 
      </div>

      {/* Navigation Menu */}
      <nav className="sidebar-nav">
        <ul className="nav-list">
          {menuItems.map((item) => (
            <li key={item.id} className="nav-item">
              <button
                className={`nav-link ${
                  activeView === item.id ? 'active' : ''
                }`}
                onClick={() => onViewChange(item.id)}
                data-testid={`nav-${item.id}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {isOpen && <span className="nav-label">{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Mini System Status Indicator */}
      {isOpen && systemStatus && (
        <div className="sidebar-footer">
          <div className="system-status-mini">
            <div className="status-header">
              <h4>Quick Status</h4>
            </div>
            <div className="status-items">
              <div className="status-item-mini">
                <div className={`status-dot ${systemStatus.status === 'healthy' ? 'healthy' : 'error'}`}></div>
                <span className="status-text">API: {systemStatus.status === 'healthy' ? 'OK' : 'Error'}</span>
              </div>
              <div className="status-item-mini">
                <div className="status-dot healthy"></div>
                <span className="status-text">ML: OK</span>
              </div>
              <div className="status-item-mini">
                <div className="status-dot healthy"></div>
                <span className="status-text">DB: OK</span>
              </div>
            </div>
            <button 
              onClick={() => onViewChange('system-status')}
              className="view-full-status-btn"
              data-testid="view-full-status"
            >
              View Full Status
            </button>
          </div>
        </div>
      )}

      {/* Collapsed Status Indicator */}
      {!isOpen && systemStatus && (
        <div className="sidebar-footer-collapsed">
          <div className="status-indicator-collapsed" title={`System Status: ${systemStatus.status}`}>
            <div className={`status-dot-large ${systemStatus.status === 'healthy' ? 'healthy' : 'error'}`}></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;