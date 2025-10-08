import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = ({ onLogin }) => {
  const [authMode, setAuthMode] = useState('choose'); // 'choose', 'email', 'register'
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
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
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/register`, {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name
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

        {/* Emergent OAuth */}
        <button
          onClick={handleEmergentAuth}
          className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-200"
          data-testid="emergent-auth-btn"
        >
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-3 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
            Continue with Emergent Platform
          </div>
        </button>

        {/* Google OAuth */}
        <div className="google-auth-wrapper">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap={false}
            theme="outline"
            size="large"
            width="100%"
            text="continue_with"
            shape="rectangular"
          />
        </div>

        {/* Email/Password */}
        <button
          onClick={() => setAuthMode('email')}
          className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-200"
          data-testid="email-auth-btn"
        >
          <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Continue with Email
        </button>

        <div className="text-center mt-6">
          <p className="text-xs text-gray-500">
            By continuing, you agree to our Terms of Service and Privacy Policy
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
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
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
          disabled={loading}
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