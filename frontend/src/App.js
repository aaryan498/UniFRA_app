import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import axios from 'axios';
import Cookies from 'js-cookie';
import './App.css';

// Import components
import Login from './components/Login';
import Dashboard from './components/Dashboard';
// Lazy load heavy components
import {
  LazyUploadAnalysis,
  LazyAssetHistory,
  LazySystemStatus
} from './components/LazyComponents';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "your-google-client-id.apps.googleusercontent.com";

// Configure axios defaults
axios.defaults.timeout = 30000;
axios.defaults.withCredentials = true;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [assets, setAssets] = useState([]);

  // Auth token management
  const setAuthToken = useCallback((token) => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('access_token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('access_token');
    }
  }, []);

  // Check for existing authentication
  const checkAuthStatus = useCallback(async () => {
    try {
      // Check for session_id in URL fragment (Emergent OAuth)
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      const sessionId = hashParams.get('session_id');
      
      if (sessionId) {
        // Process Emergent OAuth session
        console.log('Processing Emergent OAuth session...');
        const response = await axios.post(`${API}/auth/emergent/session`, null, {
          headers: { 'X-Session-ID': sessionId }
        });
        
        if (response.data) {
          // Set access token if provided
          if (response.data.access_token) {
            setAuthToken(response.data.access_token);
          }
          
          setUser({
            id: response.data.id,
            email: response.data.email,
            full_name: response.data.name,
            profile_picture: response.data.picture,
            auth_method: 'emergent_oauth'
          });
          
          // Clean URL
          window.history.replaceState({}, document.title, window.location.pathname);
          setLoading(false);
          return;
        }
      }
      
      // Check for existing session or token
      const token = localStorage.getItem('access_token');
      if (token) {
        setAuthToken(token);
      }
      
      // Try to get current user
      const response = await axios.get(`${API}/auth/me`);
      if (response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.log('No active session found');
      // Clear any invalid tokens
      setAuthToken(null);
      Cookies.remove('session_token');
    } finally {
      setLoading(false);
    }
  }, [setAuthToken]);

  // Load initial data
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // Load app data when user is authenticated
  useEffect(() => {
    if (user) {
      checkSystemHealth();
      loadAssets();
      
      // Set up periodic health checks
      const healthInterval = setInterval(checkSystemHealth, 30000);
      return () => clearInterval(healthInterval);
    }
  }, [user]);

  const checkSystemHealth = async () => {
    try {
      const response = await axios.get(`${API}/health`);
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Health check failed:', error);
      setSystemStatus({ status: 'error', message: 'API connection failed' });
    }
  };

  const loadAssets = async () => {
    try {
      const response = await axios.get(`${API}/assets`);
      setAssets(response.data.assets || []);
    } catch (error) {
      console.error('Failed to load assets:', error);
      setAssets([]);
    }
  };

  const refreshData = () => {
    loadAssets();
    checkSystemHealth();
  };

  const handleLogin = (userData, token) => {
    setUser(userData);
    if (token) {
      setAuthToken(token);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setAuthToken(null);
      Cookies.remove('session_token');
      setActiveView('dashboard');
    }
  };

  if (loading) {
    return (
      <div className="loading-container" data-testid="loading-spinner">
        <div className="unifra-logo">
          <svg className="w-16 h-16 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          <h1 className="text-2xl font-bold text-gray-800 mt-4">UniFRA</h1>
          <p className="text-gray-600">Unified AI FRA Diagnostics</p>
        </div>
        <div className="loading-spinner mt-8"></div>
        <p className="text-gray-600 mt-4">Loading UniFRA system...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
          <Login onLogin={handleLogin} />
        </div>
      </GoogleOAuthProvider>
    );
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Router>
        <div className="App">
          <div className="app-layout">
            {/* Sidebar */}
            <Sidebar 
              isOpen={sidebarOpen}
              activeView={activeView}
              onViewChange={setActiveView}
              onToggle={() => setSidebarOpen(!sidebarOpen)}
              systemStatus={systemStatus}
            />

            {/* Main Content */}
            <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
              {/* Header */}
              <Header 
                user={user}
                onMenuClick={() => setSidebarOpen(!sidebarOpen)}
                onRefresh={refreshData}
                onLogout={handleLogout}
                systemStatus={systemStatus}
              />

              {/* Content Area */}
              <div className="content-area">
                <Routes>
                  <Route path="/" element={
                    <>
                      {activeView === 'dashboard' && (
                        <Dashboard 
                          user={user}
                          assets={assets}
                          systemStatus={systemStatus}
                          onRefresh={refreshData}
                        />
                      )}
                      
                      {activeView === 'upload' && (
                        <LazyUploadAnalysis 
                          user={user}
                          onAnalysisComplete={refreshData}
                        />
                      )}
                      
                      {activeView === 'history' && (
                        <LazyAssetHistory 
                          user={user}
                          assets={assets}
                        />
                      )}
                      
                      {activeView === 'system-status' && (
                        <LazySystemStatus 
                          systemStatus={systemStatus}
                          onRefresh={checkSystemHealth}
                        />
                      )}
                    </>
                  } />
                  <Route path="/dashboard" element={<Navigate to="/" />} />
                  <Route path="/upload" element={<Navigate to="/" />} />
                  <Route path="/history" element={<Navigate to="/" />} />
                  <Route path="/system-status" element={<Navigate to="/" />} />
                </Routes>
              </div>
            </div>
          </div>
        </div>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;