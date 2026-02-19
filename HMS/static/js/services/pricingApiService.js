/**
 * Pricing API Service Module
 * 
 * Handles all HTTP calls to the backend pricing endpoints (Phase 1).
 * Methods return Promise-based responses for Vue component integration.
 * 
 * Backend Endpoints:
 * - GET /api/v1/bookings/pricing/predict/
 * - GET /api/v1/bookings/pricing/history/
 * - POST /api/v1/bookings/pricing/scenario/
 * - GET /api/v1/bookings/pricing/models/
 */

class PricingApiService {
  constructor(baseUrl = '/api/v1/bookings') {
    this.baseUrl = baseUrl;
    this.timeout = 15000; // 15 second timeout
  }

  /**
   * Helper method for API calls with timeout and error handling
   */
  async _apiCall(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this._getCsrfToken(),
        ...options.headers
      },
      timeout: this.timeout,
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`
        );
        error.status = response.status;
        error.data = errorData;
        throw error;
      }

      return await response.json();
    } catch (error) {
      this._logError('API Call Failed', { endpoint, error });
      throw error;
    }
  }

  /**
   * Get CSRF token from DOM or cookies
   */
  _getCsrfToken() {
    // Try to get from DOM first (Django default)
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (token) return token;

    // Fall back to cookie
    const cookies = document.cookie
      .split(';')
      .map(c => c.trim())
      .find(c => c.startsWith('csrftoken='));
    
    return cookies ? cookies.split('=')[1] : '';
  }

  /**
   * Log errors to console (can be extended for error tracking)
   */
  _logError(context, data) {
    console.error(`[PricingApiService] ${context}:`, data);
  }

  // ========================================
  // PUBLIC API METHODS
  // ========================================

  /**
   * Get AI pricing prediction and analysis
   * 
   * @param {number} roomId - Room ID to analyze
   * @param {string} date - Date in YYYY-MM-DD format
   * @param {number} occupancyRate - Occupancy rate 0-100 (optional)
   * @param {string} season - Season override (optional)
   * 
   * @returns {Promise<Object>} Prediction data with ensemble_prediction, factors, confidence, etc.
   */
  async getPricingPrediction(roomId, date, occupancyRate = null, season = null) {
    const params = new URLSearchParams({
      room_id: roomId,
      date: date
    });

    if (occupancyRate !== null) {
      params.append('occupancy_rate', occupancyRate);
    }
    if (season !== null) {
      params.append('season', season);
    }

    return this._apiCall(`/pricing/predict/?${params.toString()}`, {
      method: 'GET'
    });
  }

  /**
   * Get historical pricing trend
   * 
   * @param {number} roomId - Room ID to retrieve history for
   * @param {number} days - Number of days to return (default 30)
   * 
   * @returns {Promise<Object>} History data with trend array and statistics
   */
  async getPricingHistory(roomId, days = 30) {
    const params = new URLSearchParams({
      room_id: roomId,
      days: days
    });

    return this._apiCall(`/pricing/history/?${params.toString()}`, {
      method: 'GET'
    });
  }

  /**
   * Analyze pricing scenario (what-if analysis)
   * 
   * @param {number} roomId - Room ID to analyze
   * @param {string} date - Date in YYYY-MM-DD format
   * @param {Object} overrides - Parameter overrides
   *   - occupancy_rate: number 0-100
   *   - season: string (low|medium|high|peak)
   *   - competitor_price: number (price in dollars)
   * 
   * @returns {Promise<Object>} Scenario result with price_change and revenue_impact
   */
  async analyzeScenario(roomId, date, overrides = {}) {
    return this._apiCall('/pricing/scenario/', {
      method: 'POST',
      body: JSON.stringify({
        room_id: roomId,
        date: date,
        ...overrides
      })
    });
  }

  /**
   * Get list of available models and their metrics
   * 
   * @returns {Promise<Array>} Array of model info with accuracy, rmse, etc.
   */
  async getAvailableModels() {
    return this._apiCall('/pricing/models/', {
      method: 'GET'
    });
  }

  /**
   * Save pricing decision with audit trail
   * Note: This is handled by existing RoomAvailability endpoints, not Phase 1 pricing APIs
   * 
   * @param {number} roomId - Room ID
   * @param {string} date - Date in YYYY-MM-DD format
   * @param {number} price - Selected price
   * @param {string} reason - Reason for override (if applicable)
   * @param {string} modelUsed - Model name if AI-recommended
   * 
   * @returns {Promise<Object>} Save confirmation
   */
  async savePricingDecision(roomId, date, price, reason = '', modelUsed = null) {
    // This would call the standard update_or_create view for RoomAvailability
    return this._apiCall(`/`, {
      method: 'POST',
      body: JSON.stringify({
        room_id: roomId,
        date: date,
        dynamic_price: price,
        price_override_reason: reason,
        model_version: modelUsed
      })
    });
  }
}

// Export as singleton
export default new PricingApiService();
