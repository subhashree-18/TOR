/**
 * CasesDashboard.js - SUBMITTED CASES MANAGEMENT
 * Tamil Nadu Police Cyber Crime Wing - Case Repository
 * 
 * Display all submitted forensic cases with status, analysis, and actions
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';
import './CasesDashboard.css';

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

// Get confidence badge color
const getConfidenceColor = (confidence) => {
  switch (confidence?.toLowerCase()) {
    case 'high':
      return '#059669';
    case 'medium':
      return '#f59e0b';
    case 'low':
      return '#ef4444';
    default:
      return '#6b7280';
  }
};

// Get status badge color
const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return '#059669';
    case 'in progress':
      return '#3b82f6';
    case 'pending':
      return '#f59e0b';
    default:
      return '#6b7280';
  }
};

export default function CasesDashboard() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState('submitted_at'); // Sort by last updated
  const [filterStatus, setFilterStatus] = useState('all');

  // Fetch cases from backend
  const fetchCases = async () => {
    try {
      setRefreshing(true);
      const response = await axios.get(`${API_URL}/api/cases`);
      
      if (response.data.cases) {
        // Transform and enrich case data
        const enrichedCases = response.data.cases.map((caseItem, idx) => {
          // Extract case type from case_id if possible
          let caseType = 'General';
          if (caseItem.case_title) {
            if (caseItem.case_title.toLowerCase().includes('narcotics')) caseType = 'Narcotics';
            else if (caseItem.case_title.toLowerCase().includes('fraud')) caseType = 'Financial Fraud';
            else if (caseItem.case_title.toLowerCase().includes('identity')) caseType = 'Identity Theft';
            else if (caseItem.case_title.toLowerCase().includes('cyber')) caseType = 'Cyber Crime';
          }

          return {
            ...caseItem,
            case_type: caseType,
            evidence_status: caseItem.session_summary?.total_packets ? 'Uploaded' : 'Pending',
            analysis_status: caseItem.status === 'SUBMITTED' ? 'Completed' : 'In Progress',
            confidence_level: caseItem.report_data?.confidence_level || 'Medium',
            last_updated: caseItem.submitted_at,
            unique_ips: caseItem.session_summary?.unique_ip_addresses || 0,
            total_packets: caseItem.session_summary?.total_packets || 0,
            protocols: caseItem.session_summary?.protocols_detected?.join(', ') || 'Unknown'
          };
        });

        // Sort cases
        const sorted = enrichedCases.sort((a, b) => {
          if (sortBy === 'submitted_at') {
            return new Date(b.submitted_at) - new Date(a.submitted_at);
          }
          return 0;
        });

        setCases(sorted);
        setError(null);
      }
    } catch (err) {
      console.error("Failed to fetch cases:", err);
      setError(`Failed to load cases: ${err.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchCases();
  }, []);

  // Filter cases based on status
  const filteredCases = filterStatus === 'all' 
    ? cases 
    : cases.filter(c => c.analysis_status.toLowerCase() === filterStatus.toLowerCase());

  // Handle case row click - view case details
  const handleViewCase = (caseId) => {
    navigate(`/report?caseId=${encodeURIComponent(caseId)}`);
  };

  // Render loading state
  if (loading) {
    return (
      <div className="cases-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading cases from database...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cases-dashboard">
      {/* Breadcrumb Navigation */}
      <Breadcrumb 
        items={[
          { label: 'Dashboard', link: '/dashboard' },
          { label: 'Cases', active: true }
        ]}
      />

      {/* Header Section */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1>📋 Submitted Cases</h1>
          <p>Forensic investigation cases submitted to the database</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn-refresh"
            onClick={fetchCases}
            disabled={refreshing}
            title="Refresh cases list"
          >
            {refreshing ? '⟳ Refreshing...' : '🔄 Refresh'}
          </button>
          <button 
            className="btn-back"
            onClick={() => navigate('/dashboard')}
            title="Return to dashboard"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>

      {/* Filters Section */}
      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="status-filter">Filter by Analysis Status:</label>
          <select 
            id="status-filter"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All Cases</option>
            <option value="completed">Completed</option>
            <option value="in progress">In Progress</option>
            <option value="pending">Pending</option>
          </select>
        </div>
        <div className="stats">
          <div className="stat-item">
            <span className="stat-label">Total Cases:</span>
            <span className="stat-value">{cases.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Showing:</span>
            <span className="stat-value">{filteredCases.length}</span>
          </div>
        </div>
      </div>

      {/* Cases Table */}
      <div className="cases-table-container">
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {filteredCases.length === 0 ? (
          <div className="empty-state">
            <p>No cases found.</p>
            <small>Submit a forensic analysis to add cases to this dashboard.</small>
          </div>
        ) : (
          <table className="cases-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Case Type</th>
                <th>Evidence Status</th>
                <th>Analysis Status</th>
                <th>Confidence</th>
                <th>Evidence</th>
                <th>Last Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((caseItem, idx) => (
                <tr key={idx} className="case-row">
                  <td className="case-id">
                    <strong>{caseItem.case_id}</strong>
                    <br />
                    <small>{caseItem.case_title}</small>
                  </td>
                  <td className="case-type">{caseItem.case_type}</td>
                  <td className="evidence-status">
                    <span className={`badge badge-${caseItem.evidence_status.toLowerCase()}`}>
                      {caseItem.evidence_status}
                    </span>
                  </td>
                  <td className="analysis-status">
                    <span 
                      className="badge badge-status"
                      style={{ backgroundColor: getStatusColor(caseItem.analysis_status) }}
                    >
                      {caseItem.analysis_status}
                    </span>
                  </td>
                  <td className="confidence">
                    <span 
                      className="badge badge-confidence"
                      style={{ backgroundColor: getConfidenceColor(caseItem.confidence_level) }}
                    >
                      {caseItem.confidence_level}
                    </span>
                  </td>
                  <td className="evidence-detail">
                    <small>
                      {caseItem.total_packets} packets<br />
                      {caseItem.unique_ips} IPs<br />
                      {caseItem.protocols}
                    </small>
                  </td>
                  <td className="last-updated">
                    <small>{formatDate(caseItem.last_updated)}</small>
                  </td>
                  <td className="actions">
                    <button
                      className="action-btn view-btn"
                      onClick={() => handleViewCase(caseItem.case_id)}
                      title="View case details and report"
                    >
                      👁️ View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Section */}
      <div className="dashboard-footer">
        <p>Total: <strong>{cases.length}</strong> cases | Last updated: <strong>{new Date().toLocaleTimeString()}</strong></p>
      </div>
    </div>
  );
}
