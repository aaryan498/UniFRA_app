import React, { useState } from 'react';

const Header = ({ user, onMenuClick, onRefresh, onLogout, systemStatus }) => {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

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

  const getAuthMethodDisplay = () => {
    switch (user?.auth_method) {
      case 'google_oauth':
        return 'Google';
      case 'emergent_oauth':
        return 'Emergent';
      case 'email':
        return 'Email';
      default:
        return 'Unknown';
    }
  };

  return (
    <header className="app-header">
      <div className="header-left">
        <button 
          className="menu-button"
          onClick={onMenuClick}
          data-testid="menu-toggle"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        
        <div className="header-title">
          <h1>UniFRA Diagnostics Platform</h1>
          <p className="subtitle">AI-Powered Transformer FRA Analysis</p>
        </div>
      </div>

      <div className="header-right">
        {/* System Status */}
        <div className="header-status">
          {systemStatus && (
            <div className="status-badge">
              <div className={`status-indicator ${
                systemStatus.status === 'healthy' ? 'healthy' : 'error'
              }`}>
                <div className="status-dot"></div>
                <span className="status-text">
                  {systemStatus.status === 'healthy' ? 'System OK' : 'System Error'}
                </span>
              </div>
              <div className="status-time">
                Last updated: {formatTimestamp(systemStatus.timestamp)}
              </div>
            </div>
          )}
        </div>

        {/* Refresh Button */}
        <button 
          className="refresh-button"
          onClick={onRefresh}
          data-testid="refresh-button"
          title="Refresh data"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        {/* User Menu */}
        <div className="user-menu relative">
          <button 
            className="user-button"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            data-testid="user-menu"
          >
            <div className="user-avatar">
              {getProfilePicture() ? (
                <img 
                  src={getProfilePicture()} 
                  alt="Profile"
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <div className="flex items-center justify-center w-full h-full bg-blue-600 text-white font-medium text-sm">
                  {getInitials()}
                </div>
              )}
            </div>
            <span className="user-name">{user?.full_name || 'User'}</span>
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* User Dropdown Menu */}
          {userMenuOpen && (
            <div className="user-dropdown">
              <div className="dropdown-content">
                {/* User Info */}
                <div className="user-info">
                  <div className="user-avatar-large">
                    {getProfilePicture() ? (
                      <img 
                        src={getProfilePicture()} 
                        alt="Profile"
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center w-full h-full bg-blue-600 text-white font-bold text-lg">
                        {getInitials()}
                      </div>
                    )}
                  </div>
                  <div className="user-details">
                    <h3 className="user-name-large">{user?.full_name}</h3>
                    <p className="user-email">{user?.email}</p>
                    <p className="user-auth-method">Signed in via {getAuthMethodDisplay()}</p>
                  </div>
                </div>

                <div className="dropdown-divider"></div>

                {/* Menu Items */}
                <div className="dropdown-items">
                  <button className="dropdown-item" data-testid="profile-settings">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    Profile Settings
                  </button>
                  
                  <button className="dropdown-item" data-testid="account-preferences">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Preferences
                  </button>
                  
                  <button className="dropdown-item" data-testid="help-support">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Help & Support
                  </button>
                </div>

                <div className="dropdown-divider"></div>

                {/* Logout */}
                <button 
                  className="dropdown-item logout-item"
                  onClick={() => {
                    setUserMenuOpen(false);
                    onLogout();
                  }}
                  data-testid="logout-button"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Click outside handler for dropdown */}
      {userMenuOpen && (
        <div 
          className="dropdown-overlay"
          onClick={() => setUserMenuOpen(false)}
        ></div>
      )}
    </header>
  );
};

export default Header;