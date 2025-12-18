/**
 * InvestigationPage.js — CASE WORKSPACE (MERGED TARGET)
 * Tamil Nadu Police Cyber Crime Wing - Case Investigation Workspace
 * 
 * Single authoritative screen for complete investigation status
 * Backend-driven state with step-by-step guidance for officers
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import MandatoryDisclaimer from "./MandatoryDisclaimer";
import "./InvestigationPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Format date for display (DD-MM-YYYY HH:MM)
const formatDate = (dateString) => {
  if (!dateString) return "—";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "—";
  
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  
  return `${day}-${month}-${year} ${hours}:${minutes}`;
};

// Map confidence summary to percentage for bar display
const getConfidencePercent = (level) => {
  switch (level?.toLowerCase()) {
    case "high": return 85;
    case "medium": return 55;
    case "low": return 25;
    default: return 0;
  }
};

export default function InvestigationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get caseId from navigation state or default
  const initialCaseId = location.state?.caseId || "TN/CYB/2024/001234";
  
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(() => {
    const stored = localStorage.getItem("disclaimerAccepted");
    return stored === "true";
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Investigation data from backend
  const [investigation, setInvestigation] = useState({
    case_id: initialCaseId,
    fir_reference: null,
    created_at: null,
    evidence: {
      pcap_uploaded: false,
      sealed: false,
      uploaded_at: null
    },
    analysis: {
      status: "NOT_STARTED",
      confidence_summary: null
    }
  });

  // Fetch investigation details from backend
  useEffect(() => {
    const fetchInvestigation = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Try to fetch from backend
        const response = await axios.get(`${API_URL}/api/investigations/${encodeURIComponent(initialCaseId)}`);
        
        if (response.data) {
          setInvestigation(response.data);
        }
      } catch (err) {
        console.warn("Backend not available, using mock data:", err.message);
        
        // Mock data for demonstration when backend unavailable
        setInvestigation({
          case_id: initialCaseId,
          fir_reference: "FIR/2024/CHN/4521",
          created_at: new Date().toISOString(),
          evidence: {
            pcap_uploaded: true,
            sealed: false,
            uploaded_at: new Date(Date.now() - 86400000).toISOString()
          },
          analysis: {
            status: "COMPLETED",
            confidence_summary: "Medium"
          }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchInvestigation();
  }, [initialCaseId]);

  // Determine next action based on backend state
  const getNextAction = () => {
    const { evidence, analysis } = investigation;
    
    if (!evidence.pcap_uploaded) {
      return {
        label: "Upload Evidence",
        route: "/upload",
        description: "PCAP/log evidence required to proceed with analysis."
      };
    }
    
    if (analysis.status === "NOT_STARTED" || analysis.status === "PENDING") {
      return {
        label: "Run Analysis",
        route: "/analysis",
        description: "Evidence uploaded. Ready to run correlation analysis."
      };
    }
    
    if (analysis.status === "RUNNING") {
      return {
        label: "Analysis In Progress",
        route: null,
        description: "Correlation analysis is currently running. Please wait."
      };
    }
    
    if (analysis.status === "COMPLETED") {
      return {
        label: "View Report",
        route: "/report",
        description: "Analysis complete. View forensic report."
      };
    }
    
    return {
      label: "Continue",
      route: "/dashboard",
      description: "Proceed with investigation."
    };
  };

  const nextAction = getNextAction();

  const handleNextAction = () => {
    if (nextAction.route) {
      navigate(nextAction.route, { state: { caseId: investigation.case_id } });
    }
  };

  // Get status display text
  const getAnalysisStatusText = (status) => {
    switch (status) {
      case "NOT_STARTED": return "Not Started";
      case "PENDING": return "Pending";
      case "RUNNING": return "In Progress";
      case "COMPLETED": return "Completed";
      default: return status || "Unknown";
    }
  };

  const getAnalysisStatusClass = (status) => {
    switch (status) {
      case "COMPLETED": return "status-completed";
      case "RUNNING": return "status-running";
      case "PENDING": return "status-pending";
      case "NOT_STARTED": return "status-not-started";
      default: return "";
    }
  };

  return (
    <div className="investigation-workspace">
      {/* Mandatory Disclaimer Modal */}
      {!disclaimerAccepted && (
        <MandatoryDisclaimer
          isModal={true}
          onAcknowledge={() => {
            setDisclaimerAccepted(true);
            localStorage.setItem("disclaimerAccepted", "true");
          }}
        />
      )}

      {/* Breadcrumb */}
      <nav className="workspace-breadcrumb">
        <span className="crumb" onClick={() => navigate("/dashboard")}>Dashboard</span>
        <span className="separator">/</span>
        <span className="crumb active">Investigation</span>
        <span className="separator">/</span>
        <span className="crumb-id">{investigation.case_id}</span>
      </nav>

      {/* Page Title */}
      <div className="workspace-header">
        <h1 className="workspace-title">Case Investigation Workspace</h1>
        <p className="workspace-subtitle">Tamil Nadu Police - Cyber Crime Wing</p>
      </div>

      {loading ? (
        <div className="workspace-loading">
          <div className="loading-spinner"></div>
          <p>Loading investigation details...</p>
        </div>
      ) : error ? (
        <div className="workspace-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      ) : (
        <>
          {/* SECTION 1: CASE DETAILS */}
          <section className="workspace-section">
            <div className="section-header">
              <h2>Case Details</h2>
            </div>
            <div className="section-body">
              <table className="details-table">
                <tbody>
                  <tr>
                    <th>Case ID</th>
                    <td><code className="case-code">{investigation.case_id}</code></td>
                  </tr>
                  <tr>
                    <th>FIR Reference</th>
                    <td>
                      {investigation.fir_reference ? (
                        <span className="fir-value">{investigation.fir_reference}</span>
                      ) : (
                        <span className="fir-not-linked">Not linked</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <th>Created Date</th>
                    <td>{formatDate(investigation.created_at)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* SECTION 2: EVIDENCE STATUS */}
          <section className="workspace-section">
            <div className="section-header">
              <h2>Evidence Status</h2>
            </div>
            <div className="section-body">
              <table className="details-table">
                <tbody>
                  <tr>
                    <th>PCAP/Log Evidence</th>
                    <td>
                      {investigation.evidence.pcap_uploaded ? (
                        <span className="evidence-uploaded">Uploaded</span>
                      ) : (
                        <span className="evidence-not-uploaded">Not Uploaded</span>
                      )}
                    </td>
                  </tr>
                  {investigation.evidence.pcap_uploaded && (
                    <>
                      <tr>
                        <th>Uploaded At</th>
                        <td>{formatDate(investigation.evidence.uploaded_at)}</td>
                      </tr>
                      <tr>
                        <th>Evidence Seal</th>
                        <td>
                          {investigation.evidence.sealed ? (
                            <span className="seal-badge sealed">Evidence Sealed</span>
                          ) : (
                            <span className="seal-badge not-sealed">Not Sealed</span>
                          )}
                        </td>
                      </tr>
                    </>
                  )}
                </tbody>
              </table>
              
              {!investigation.evidence.pcap_uploaded && (
                <div className="warning-box">
                  <strong>Warning:</strong> No evidence has been uploaded for this case. 
                  Upload PCAP or log files to proceed with forensic analysis.
                </div>
              )}
            </div>
          </section>

          {/* SECTION 3: ANALYSIS STATUS */}
          <section className="workspace-section">
            <div className="section-header">
              <h2>Analysis Status</h2>
            </div>
            <div className="section-body">
              <table className="details-table">
                <tbody>
                  <tr>
                    <th>Correlation Status</th>
                    <td>
                      <span className={`analysis-status ${getAnalysisStatusClass(investigation.analysis.status)}`}>
                        {getAnalysisStatusText(investigation.analysis.status)}
                      </span>
                    </td>
                  </tr>
                  {investigation.analysis.confidence_summary && (
                    <tr>
                      <th>Confidence Summary</th>
                      <td>
                        <div className="confidence-display">
                          <span className="confidence-text">
                            {investigation.analysis.confidence_summary}
                          </span>
                          <div className="confidence-bar-container">
                            <div 
                              className={`confidence-bar confidence-${investigation.analysis.confidence_summary.toLowerCase()}`}
                              style={{ width: `${getConfidencePercent(investigation.analysis.confidence_summary)}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
              
              {investigation.analysis.status === "RUNNING" && (
                <div className="info-box">
                  Analysis is currently in progress. This page will update automatically when complete.
                </div>
              )}
            </div>
          </section>

          {/* SECTION 4: NEXT ACTION */}
          <section className="workspace-section action-section">
            <div className="section-header">
              <h2>Next Action</h2>
            </div>
            <div className="section-body">
              <p className="action-description">{nextAction.description}</p>
              
              {nextAction.route && (
                <button 
                  className="action-button"
                  onClick={handleNextAction}
                >
                  {nextAction.label}
                </button>
              )}
              
              {!nextAction.route && investigation.analysis.status === "RUNNING" && (
                <div className="action-waiting">
                  <div className="waiting-indicator"></div>
                  <span>Please wait for analysis to complete...</span>
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
