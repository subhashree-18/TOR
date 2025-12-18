/**
 * Dashboard.js ??? CASE REGISTRY (POLICE RECORDS STYLE)
 * Tamil Nadu Police Cyber Crime Wing - TOR???Unveil
 * 
 * This UI is for a Tamil Nadu Police / Government forensic system.
 * 
 * Constraints:
 * - No mock data - all data from backend APIs
 * - No flashy UI, animations, charts, or maps
 * - Text-first, table-first design
 * - All actions and messages must sound official and professional
 * - Target users are police officers, not developers
 */

import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

export default function Dashboard() {
  const navigate = useNavigate();
  
  // State - all driven by backend
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);

  // Fetch cases from backend
  const fetchCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch("/api/investigations");
      if (response.ok) {
        const data = await response.json();
        setCases(data.investigations || data || []);
      } else {
        throw new Error("Unable to retrieve case records from server");
      }
    } catch (err) {
      console.warn("Backend unavailable, showing empty state:", err.message);
      setError("Case records unavailable. Backend service may be offline.");
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // Determine next recommended action based on case status
  const getNextAction = () => {
    if (cases.length === 0) {
      return {
        message: "Register a new case to begin investigation.",
        action: "Register New Case",
        path: "/investigation"
      };
    }

    // Find cases needing attention
    const pendingEvidence = cases.find(c => 
      c.evidenceStatus === "Pending" || !c.evidenceStatus
    );
    if (pendingEvidence) {
      return {
        message: `Case ${pendingEvidence.caseId}: Upload forensic evidence to proceed.`,
        action: "Upload Evidence",
        path: `/forensic-upload/${pendingEvidence.caseId}`
      };
    }

    const pendingAnalysis = cases.find(c => 
      c.analysisStatus === "Not Started" || c.analysisStatus === "Pending"
    );
    if (pendingAnalysis) {
      return {
        message: `Case ${pendingAnalysis.caseId}: Initiate correlation analysis.`,
        action: "Initiate Analysis",
        path: `/analysis/${pendingAnalysis.caseId}`
      };
    }

    const completedAnalysis = cases.find(c => 
      c.analysisStatus === "Completed" && c.reportStatus !== "Exported"
    );
    if (completedAnalysis) {
      return {
        message: `Case ${completedAnalysis.caseId}: Review findings and export report.`,
        action: "View Findings",
        path: `/report/${completedAnalysis.caseId}`
      };
    }

    return {
      message: "All cases are up to date. Register a new case or review existing records.",
      action: "Register New Case",
      path: "/investigation"
    };
  };

  const nextAction = getNextAction();

  // Navigation handlers
  const handleRowClick = (caseItem) => {
    setSelectedCase(caseItem.caseId === selectedCase ? null : caseItem.caseId);
  };

  const handleViewCase = (caseItem) => {
    navigate(`/investigation/${caseItem.caseId}`);
  };

  const handleRegisterNewCase = () => {
    navigate("/investigation");
  };

  const handleNextAction = () => {
    navigate(nextAction.path);
  };

  // Status styling helpers
  const getEvidenceStatusClass = (status) => {
    if (!status || status === "Pending") return "status-pending";
    if (status === "Uploaded" || status === "Sealed") return "status-uploaded";
    return "";
  };

  const getAnalysisStatusClass = (status) => {
    if (status === "Completed") return "status-completed";
    if (status === "In Progress") return "status-in-progress";
    return "status-not-started";
  };

  const getConfidenceClass = (level) => {
    if (level === "High" || level >= 0.7) return "confidence-high";
    if (level === "Medium" || level >= 0.4) return "confidence-medium";
    return "confidence-low";
  };

  // Summary counts
  const totalCases = cases.length;
  const pendingEvidenceCount = cases.filter(c => 
    !c.evidenceStatus || c.evidenceStatus === "Pending"
  ).length;
  const inProgressCount = cases.filter(c => 
    c.analysisStatus === "In Progress"
  ).length;
  const completedCount = cases.filter(c => 
    c.analysisStatus === "Completed"
  ).length;

  return (
    <div className="records-dashboard">
      {/* Hackathon Demo Banner */}
      <div className="demo-banner">
        Demonstration Prototype – TN Police Hackathon 2025
      </div>

      {/* Page Header */}
      <div className="records-header">
        <div className="header-left">
          <h1 className="page-title">Case Registry</h1>
          <p className="page-subtitle">Cyber Crime Investigation Management System</p>
        </div>
        <div className="header-right">
          <button className="btn-register" onClick={handleRegisterNewCase}>
            + Register New Case
          </button>
        </div>
      </div>

      {/* System Status Section */}
      <div className="system-status-section">
        <div className="system-status-header">System Status</div>
        <div className="system-status-grid">
          <div className="status-item">
            <span className="status-label">TOR Data:</span>
            <span className="status-value operational">Auto-updated</span>
          </div>
          <div className="status-item">
            <span className="status-label">Correlation Engine:</span>
            <span className="status-value operational">Ready</span>
          </div>
          <div className="status-item">
            <span className="status-label">Evidence Storage:</span>
            <span className="status-value operational">Available</span>
          </div>
          <div className="status-item">
            <span className="status-label">Backend Services:</span>
            <span className="status-value operational">Active</span>
          </div>
        </div>
      </div>

      {/* Next Recommended Action */}
      <div className="next-action-section">
        <div className="next-action-header">Next Recommended Action</div>
        <div className="next-action-content">
          <p className="next-action-message">{nextAction.message}</p>
          <button className="btn-next-action" onClick={handleNextAction}>
            {nextAction.action}
          </button>
        </div>
      </div>

      {/* Summary Bar */}
      <div className="summary-bar">
        <div className="summary-item">
          <span className="summary-label">Total Cases:</span>
          <span className="summary-value">{totalCases}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Pending Evidence:</span>
          <span className="summary-value">{pendingEvidenceCount}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Analysis In Progress:</span>
          <span className="summary-value">{inProgressCount}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Completed:</span>
          <span className="summary-value">{completedCount}</span>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <p>Retrieving case records from server...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="error-state">
          <p>{error}</p>
          <button className="btn-retry" onClick={fetchCases}>
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && cases.length === 0 && (
        <div className="empty-state">
          <p className="empty-title">No Case Records Found</p>
          <p className="empty-message">
            Register a new case to begin investigation. All case data will be 
            stored securely and tracked through the investigation workflow.
          </p>
          <button className="btn-register-empty" onClick={handleRegisterNewCase}>
            Register New Case
          </button>
        </div>
      )}

      {/* Case Records Table */}
      {!loading && cases.length > 0 && (
        <>
          <div className="records-table-container">
            <table className="records-table">
              <thead>
                <tr>
                  <th className="th-serial">S.No</th>
                  <th className="th-caseid">Case ID</th>
                  <th className="th-casetype">Case Type</th>
                  <th className="th-evidence">Evidence Status</th>
                  <th className="th-analysis">Analysis Status</th>
                  <th className="th-confidence">Confidence Assessment</th>
                  <th className="th-updated">Last Updated</th>
                  <th className="th-action">Action</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((caseItem, index) => (
                  <tr 
                    key={caseItem.caseId || index}
                    className={`case-row ${selectedCase === caseItem.caseId ? "row-selected" : ""}`}
                    onClick={() => handleRowClick(caseItem)}
                  >
                    <td className="td-serial">{index + 1}</td>
                    <td className="td-caseid">
                      <code>{caseItem.caseId || "???"}</code>
                    </td>
                    <td className="td-casetype">{caseItem.caseType || "Cyber Crime"}</td>
                    <td className="td-evidence">
                      <span className={`status-badge ${getEvidenceStatusClass(caseItem.evidenceStatus)}`}>
                        {caseItem.evidenceStatus || "Pending"}
                      </span>
                    </td>
                    <td className="td-analysis">
                      <span className={`status-badge ${getAnalysisStatusClass(caseItem.analysisStatus)}`}>
                        {caseItem.analysisStatus || "Not Started"}
                      </span>
                    </td>
                    <td className="td-confidence">
                      <span className={`confidence-badge ${getConfidenceClass(caseItem.confidenceLevel)}`}>
                        {caseItem.confidenceLevel || "???"}
                      </span>
                    </td>
                    <td className="td-updated">{caseItem.lastUpdated || "???"}</td>
                    <td className="td-action">
                      <button 
                        className="btn-view"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewCase(caseItem);
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="records-footer">
            <div className="footer-info">
              Displaying {cases.length} case record(s)
            </div>
            <div className="footer-note">
              * Select a row to highlight. Click "View" to open case workspace.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
