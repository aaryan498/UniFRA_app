import React, { useState } from 'react';

const Header = ({ user, onLogout, onMenuClick }) => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const getAuthMethodDisplay = () => {
    if (!user?.auth_method) return 'Unknown';
    const methodMap = {
      'email': 'Email',
      'google_oauth': 'Google',
      'emergent_oauth': 'Google',
      'guest': 'Guest'
    };
    return methodMap[user.auth_method] || 'Unknown';
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

  return (
    <header className="app-header sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-3 sm:px-4 lg:px-6">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo Section */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="flex items-center">
              <svg className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              <h1 className="ml-2 text-lg sm:text-xl lg:text-2xl font-bold text-gray-900">
                UniFRA
              </h1>
            </div>
            <span className="hidden sm:inline-block px-2 py-0.5 text-xs font-medium text-blue-600 bg-blue-50 rounded">
              v2.0
            </span>
          </div>

          {/* User Section */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* User Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-2 sm:space-x-3 focus:outline-none hover:bg-gray-50 rounded-lg p-1 sm:p-2 transition-colors duration-200"
                data-testid="user-menu-button"
              >
                <div className="flex items-center space-x-2">
                  <div className="user-avatar-small w-8 h-8 sm:w-10 sm:h-10">
                    {getProfilePicture() ? (
                      <img 
                        src={getProfilePicture()} 
                        alt="Profile"
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center w-full h-full bg-blue-600 text-white font-bold text-xs sm:text-sm">
                        {getInitials()}
                      </div>
                    )}
                  </div>
                  <div className="hidden md:block text-left">
                    <p className="text-xs sm:text-sm font-medium text-gray-900 truncate max-w-[120px] lg:max-w-[200px]">
                      {user?.full_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {getAuthMethodDisplay()}
                    </p>
                  </div>
                </div>
                <svg 
                  className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {isUserMenuOpen && (
                <>
                  {/* Backdrop for mobile */}
                  <div 
                    className="fixed inset-0 z-40 md:hidden"
                    onClick={() => setIsUserMenuOpen(false)}
                  />
                  
                  {/* Dropdown content */}
                  <div className="absolute right-0 mt-2 w-72 sm:w-80 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    {/* User Details Section */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="flex items-start space-x-3">
                        <div className="user-avatar-medium w-12 h-12 flex-shrink-0">
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
                        <div className="user-details flex-1 min-w-0">
                          <h3 className="user-name-large text-sm font-semibold text-gray-900 truncate">
                            {user?.full_name}
                          </h3>
                          <p className="user-username text-sm font-medium text-gray-600 truncate">
                            @{user?.username || 'username'}
                          </p>
                          <p className="user-email text-xs text-gray-500 truncate mt-1">
                            {user?.email}
                          </p>
                          <p className="user-auth-method text-xs text-gray-400 mt-1">
                            Signed in via {getAuthMethodDisplay()}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Action Items */}
                    <div className="py-2">
                      <button
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          if (onLogout) onLogout();
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 transition-colors duration-150 flex items-center space-x-2"
                        data-testid="logout-button"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;