/**
 * Centralized API Client for In-Tuned
 * Handles all HTTP communication with the backend
 */

const API = (function() {
  'use strict';

  const BASE_URL = '';

  // Request configuration
  const defaultHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };

  /**
   * Make an API request
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<Object>} Response data
   */
  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;

    const config = {
      credentials: 'same-origin',
      headers: { ...defaultHeaders, ...options.headers },
      ...options
    };

    // Don't set Content-Type for FormData
    if (options.body instanceof FormData) {
      delete config.headers['Content-Type'];
    } else if (options.body && typeof options.body === 'object') {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);
      let data;

      try {
        data = await response.json();
      } catch (e) {
        data = null;
      }

      if (!response.ok) {
        const error = new Error(
          (data && (data.error?.message || data.error || data.message)) ||
          `Request failed with status ${response.status}`
        );
        error.status = response.status;
        error.code = data?.error?.code || 'UNKNOWN_ERROR';
        throw error;
      }

      return data || {};
    } catch (error) {
      if (!error.status) {
        error.status = 0;
        error.code = 'NETWORK_ERROR';
      }
      throw error;
    }
  }

  // HTTP method shortcuts
  const get = (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'GET' });

  const post = (endpoint, body, options = {}) =>
    request(endpoint, { ...options, method: 'POST', body });

  const put = (endpoint, body, options = {}) =>
    request(endpoint, { ...options, method: 'PUT', body });

  const del = (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'DELETE' });

  const patch = (endpoint, body, options = {}) =>
    request(endpoint, { ...options, method: 'PATCH', body });

  // Auth endpoints
  const auth = {
    login: (identifier, password) =>
      post('/api/auth/login', { identifier, password }),

    register: (userData) =>
      post('/api/auth/register', userData),

    logout: () =>
      post('/api/auth/logout'),

    getCurrentUser: () =>
      get('/api/auth/me'),

    updateSettings: (settings) =>
      post('/api/auth/update-settings', settings),

    resetPassword: (email, firstName, lastName, newPassword) =>
      post('/api/auth/reset-password', { email, first_name: firstName, last_name: lastName, new_password: newPassword }),

    changePassword: (currentPassword, newPassword) =>
      post('/api/auth/change-password', { current_password: currentPassword, new_password: newPassword })
  };

  // Journal endpoints
  const journals = {
    list: (page = 1, perPage = 50) =>
      get(`/api/journals?page=${page}&per_page=${perPage}`),

    get: (id) =>
      get(`/api/journals/${id}`),

    create: (data) =>
      post('/api/journals', data),

    update: (id, data) =>
      put(`/api/journals/${id}`, data),

    delete: (id) =>
      del(`/api/journals/${id}`),

    togglePin: (id) =>
      post(`/api/journals/${id}/pin`),

    getStats: () =>
      get('/api/journals/stats'),

    export: (format = 'json') =>
      get(`/api/journals/export?format=${format}`)
  };

  // Detector endpoints
  const detector = {
    analyze: (text, language = 'en') =>
      post('/api/analyze', { text, language })
  };

  // Site endpoints
  const site = {
    getState: () =>
      get('/api/site-state'),

    health: () =>
      get('/api/health'),

    version: () =>
      get('/api/version')
  };

  // Feedback endpoints
  const feedback = {
    submit: (data) =>
      post('/api/feedback', data)
  };

  // User endpoints
  const users = {
    getProfile: () =>
      get('/api/users/profile'),

    updateProfile: (data) =>
      put('/api/users/profile', data),

    updateEmail: (email, password) =>
      put('/api/users/email', { email, password }),

    deleteAccount: (password, confirmation) =>
      del('/api/users/account', { body: JSON.stringify({ password, confirmation }) }),

    getStats: () =>
      get('/api/users/stats'),

    exportData: () =>
      get('/api/users/export')
  };

  // Analytics endpoints (for dashboard)
  const analytics = {
    getEmotionTrends: (period = '30d') =>
      get(`/api/analytics/emotions?period=${period}`),

    getActivityStats: (period = '30d') =>
      get(`/api/analytics/activity?period=${period}`),

    getInsights: () =>
      get('/api/analytics/insights')
  };

  return {
    request,
    get,
    post,
    put,
    delete: del,
    patch,
    auth,
    journals,
    detector,
    site,
    feedback,
    users,
    analytics
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API;
}
