/**
 * apiService.js
 * Unified API client for TOR Unveil Backend
 * 
 * Provides single source of truth for all API calls
 * Handles authentication, error handling, and base URL management
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

/**
 * Unified API client with error handling
 */
class APIService {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.timeout = 30000; // 30 seconds
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultOptions = {
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...defaultOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `API Error ${response.status}: ${errorData.detail || response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Investigation & Analysis Endpoints
   */

  // Get list of all investigations
  async getInvestigations() {
    return this.request("/api/investigations");
  }

  // Get specific investigation by case ID
  async getInvestigation(caseId) {
    return this.request(`/api/investigations/${encodeURIComponent(caseId)}`);
  }

  // Get investigation status
  async getInvestigationStatus(caseId) {
    return this.request(
      `/api/investigations/${encodeURIComponent(caseId)}/status`
    );
  }

  /**
   * Relay & Network Endpoints
   */

  // Get list of relays with optional filtering
  async getRelays(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/relays${queryString ? '?' + queryString : ''}`);
  }

  // Get relays with map coordinates
  async getRelaysMap(limit = 2000) {
    return this.request(`/api/relays/map?limit=${limit}`);
  }

  // Fetch latest relay data from Onionoo
  async fetchLatestRelays() {
    return this.request("/api/relays/fetch");
  }

  /**
   * Risk & Threat Endpoints
   */

  // Get top risk relays
  async getTopRiskRelays(limit = 50) {
    return this.request(`/api/risk/top?limit=${limit}`);
  }

  // Get malicious relays
  async getMaliciousRelays(limit = 100) {
    return this.request(`/api/intel/malicious?limit=${limit}`);
  }

  /**
   * Analytics & Statistics
   */

  // Get India-specific TOR analytics
  async getIndiaAnalytics() {
    return this.request("/api/analytics/india");
  }

  /**
   * Path Correlation Endpoints
   */

  // Generate probabilistic paths
  async generatePaths(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/paths/generate${queryString ? '?' + queryString : ''}`);
  }

  // Get probabilistic inference paths
  async getProbabilisticPaths(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/paths/inference${queryString ? '?' + queryString : ''}`);
  }

  // Get top candidate paths
  async getTopPaths(limit = 100) {
    return this.request(`/api/paths/top?limit=${limit}`);
  }

  /**
   * Timeline & Historical Endpoints
   */

  // Get timeline for specific relay
  async getRelayTimeline(fingerprint) {
    return this.request(
      `/api/relay/${encodeURIComponent(fingerprint)}/timeline`
    );
  }

  // Get timeline events
  async getTimeline(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/timeline${queryString ? '?' + queryString : ''}`);
  }

  /**
   * Metadata & Configuration Endpoints
   */

  // Get system metadata
  async getMetadata() {
    return this.request("/api/metadata");
  }

  // Get scoring methodology
  async getScoringMethodology() {
    return this.request("/api/scoring-methodology");
  }

  /**
   * File Upload Endpoints
   */

  // Upload evidence file (PCAP, logs, etc.)
  async uploadEvidence(file, caseId) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("caseId", caseId);

    const url = `${this.baseURL}/api/evidence/upload`;

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Upload Error ${response.status}: ${errorData.detail || response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  // Upload forensic data (logs, metadata)
  async uploadForensic(file) {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseURL}/api/forensic/upload`;

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Forensic Upload Error ${response.status}: ${errorData.detail || response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Export Endpoints
   */

  // Generate PDF report
  async generateReport(pathId) {
    const url = `${this.baseURL}/api/export/report?path_id=${encodeURIComponent(pathId)}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Report Generation Error ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Legal & Disclaimer Endpoints
   */

  // Get disclaimer
  async getDisclaimer() {
    return this.request("/disclaimer");
  }

  // Get methodology info
  async getMethodology() {
    return this.request("/methodology");
  }
}

// Export singleton instance
export default new APIService();
