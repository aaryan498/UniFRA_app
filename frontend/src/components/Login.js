import React, { useState, useEffect } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import ForgotPassword from './ForgotPassword';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ onLogin }) => {
  const [authMode, setAuthMode] = useState('choose'); // 'choose', 'email', 'register', 'forgot-password'
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    username: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [usernameStatus, setUsernameStatus] = useState(''); // 'checking', 'available', 'taken'
  const [usernameMessage, setUsernameMessage] = useState('');
  const [usernameCheckTimeout, setUsernameCheckTimeout] = useState(null);

  // Check username availability in real-time
  useEffect(() => {
    if (authMode === 'register' && formData.username && formData.username.length >= 3) {
      // Clear previous timeout
      if (usernameCheckTimeout) {
        clearTimeout(usernameCheckTimeout);
      }

      // Set checking status
      setUsernameStatus('checking');

      // Debounce the username check
      const timeout = setTimeout(async () => {
        try {
          const response = await axios.get(`${API}/auth/check-username?username=${encodeURIComponent(formData.username)}`);
          if (response.data.available) {
            setUsernameStatus('available');
            setUsernameMessage('Username is available');
          } else {
            setUsernameStatus('taken');
            setUsernameMessage(response.data.message || 'Username is already taken');
          }
        } catch (error) {
          console.error('Username check failed:', error);
          setUsernameStatus('');
          setUsernameMessage('');
        }
      }, 500);

      setUsernameCheckTimeout(timeout);
    } else if (authMode === 'register' && formData.username.length < 3 && formData.username.length > 0) {
      setUsernameStatus('taken');
      setUsernameMessage('Username must be at least 3 characters');
    } else {
      setUsernameStatus('');
      setUsernameMessage('');
    }

    return () => {
      if (usernameCheckTimeout) {
        clearTimeout(usernameCheckTimeout);
      }
    };
  }, [formData.username, authMode]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleGuestLogin = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/guest`);

      if (response.data.user && response.data.access_token) {
        onLogin(response.data.user, response.data.access_token);
      }
    } catch (error) {
      console.error('Guest login failed:', error);
      setError('Failed to create guest account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.email);
      formDataToSend.append('password', formData.password);

      const response = await axios.post(`${API}/auth/login`, formDataToSend, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      if (response.data.user && response.data.access_token) {
        onLogin(response.data.user, response.data.access_token);
      }
    } catch (error) {
      console.error('Login failed:', error);
      setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailRegister = async (e) => {
    e.preventDefault();
    
    // Check if username is available before submitting
    if (usernameStatus !== 'available') {
      setError('Please choose an available username');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/register`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        username: formData.username
      });

      if (response.data.user && response.data.access_token) {
        onLogin(response.data.user, response.data.access_token);
      }
    } catch (error) {
      console.error('Registration failed:', error);
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/google`, {
        id_token: credentialResponse.credential
      });

      if (response.data.user) {
        onLogin(response.data.user, response.data.access_token);
      }
    } catch (error) {
      console.error('Google login failed:', error);
      setError('Google authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google authentication was cancelled or failed.');
  };

  const handleEmergentAuth = () => {
    const currentUrl = window.location.origin + window.location.pathname;
    const emergentAuthUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(currentUrl)}`;
    window.location.href = emergentAuthUrl;
  };

  const getUsernameBorderClass = () => {
    if (usernameStatus === 'available') return 'border-green-500 focus:border-green-500 focus:ring-green-500';
    if (usernameStatus === 'taken') return 'border-red-500 focus:border-red-500 focus:ring-red-500';
    return 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
  };

  const getUsernameTextClass = () => {
    if (usernameStatus === 'available') return 'text-green-600';
    if (usernameStatus === 'taken') return 'text-red-600';
    return 'text-gray-500';
  };

  const renderChooseAuth = () => (
    <div className="auth-choose">
      <div className="text-center mb-8">
        <div className="unifra-logo mb-6">
          <svg className="w-20 h-20 mx-auto text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          <h1 className="text-4xl font-bold text-gray-900 mt-4">UniFRA</h1>
          <p className="text-xl text-gray-600 mt-2">Unified AI FRA Diagnostics</p>
          <p className="text-sm text-gray-500 mt-1">AI-powered transformer fault detection and analysis</p>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900 text-center mb-6">
          Choose Your Login Method
        </h2>

        {/* Guest Login */}
        <button
          onClick={handleGuestLogin}
          disabled={loading}
          className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-gradient-to-r from-blue-50 to-indigo-50 text-sm font-medium text-gray-700 hover:from-blue-100 hover:to-indigo-100 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          data-testid="guest-auth-btn"
        >
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {loading ? 'Creating Guest Account...' : 'Continue with UniFRA as Guest'}
          </div>
        </button>

        {/* Google OAuth via UniFRA */}
        <button
          onClick={handleEmergentAuth}
          className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-200"
          data-testid="google-auth-btn"
        >
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </div>
        </button>

        {/* Email/Password */}
        <button
          onClick={() => setAuthMode('email')}
          className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-200"
          data-testid="email-auth-btn"
        >
          <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Login/Signup using Email
        </button>

        <div className="text-center mt-6">
          <p className="text-xs text-gray-500">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Guest accounts expire after 24 hours if not converted to permanent accounts
          </p>
        </div>
      </div>
    </div>
  );

  const renderEmailAuth = () => (
    <div className="auth-email">
      <div className="text-center mb-8">
        <button
          onClick={() => setAuthMode('choose')}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center mx-auto"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to login options
        </button>
        
        <h2 className="text-3xl font-bold text-gray-900">
          {authMode === 'register' ? 'Create Account' : 'Sign In'}
        </h2>
        <p className="text-gray-600 mt-2">
          {authMode === 'register' 
            ? 'Enter your details to create a new account' 
            : 'Enter your email and password to sign in'
          }
        </p>
      </div>

      <form onSubmit={authMode === 'register' ? handleEmailRegister : handleEmailLogin} className="space-y-6">
        {authMode === 'register' && (
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
              Full Name
            </label>
            <input
              type="text"
              name="full_name"
              id="full_name"
              required
              value={formData.full_name}
              onChange={handleInputChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter your full name"
              data-testid="full-name-input"
            />
          </div>
        )}

        {authMode === 'register' && (
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              type="text"
              name="username"
              id="username"
              required
              minLength={3}
              maxLength={30}
              value={formData.username}
              onChange={handleInputChange}
              className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none sm:text-sm ${getUsernameBorderClass()}`}
              placeholder="Choose a unique username"
              data-testid="username-input"
            />
            {usernameMessage && (
              <p className={`mt-1 text-sm flex items-center ${getUsernameTextClass()}`}>
                {usernameStatus === 'available' && (
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
                {usernameStatus === 'taken' && (
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
                {usernameMessage}
              </p>
            )}
          </div>
        )}

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email Address
          </label>
          <input
            type="email"
            name="email"
            id="email"
            required
            value={formData.email}
            onChange={handleInputChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Enter your email"
            data-testid="email-input"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            {authMode === 'email' && (
              <button
                type="button"
                onClick={() => setAuthMode('forgot-password')}
                className="text-sm text-blue-600 hover:text-blue-800"
                data-testid="forgot-password-link"
              >
                Forgot password?
              </button>
            )}
          </div>
          <input
            type="password"
            name="password"
            id="password"
            required
            minLength={8}
            value={formData.password}
            onChange={handleInputChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder={authMode === 'register' ? 'Create a password (min 8 characters)' : 'Enter your password'}
            data-testid="password-input"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="ml-3 text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || (authMode === 'register' && usernameStatus !== 'available')}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          data-testid={authMode === 'register' ? 'register-submit' : 'login-submit'}
        >
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {authMode === 'register' ? 'Creating Account...' : 'Signing In...'}
            </div>
          ) : (
            authMode === 'register' ? 'Create Account' : 'Sign In'
          )}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          onClick={() => setAuthMode(authMode === 'register' ? 'email' : 'register')}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          data-testid="toggle-auth-mode"
        >
          {authMode === 'register' 
            ? 'Already have an account? Sign in' 
            : "Don't have an account? Create one"
          }
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white rounded-xl shadow-xl border border-gray-100 p-8">
          {authMode === 'choose' && renderChooseAuth()}
          {(authMode === 'email' || authMode === 'register') && renderEmailAuth()}
          {authMode === 'forgot-password' && (
            <ForgotPassword
              onBack={() => setAuthMode('email')}
              onSuccess={() => setAuthMode('email')}
            />
          )}
        </div>
        
        <div className="text-center">
          <p className="text-sm text-gray-500">
            UniFRA v2.0 - Advanced Transformer Diagnostics Platform
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
