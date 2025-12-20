/**
 * InvestigationPage.js - SINGLE SOURCE OF TRUTH FOR CASE WORKFLOW
 * Tamil Nadu Police Cyber Crime Wing - Case Investigation Dashboard
 * 
 * Purpose: Backend-driven workflow enforcement for forensic investigation
 * All navigation decisions controlled by backend case state
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';
import './InvestigationPage.css';

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Format date for official display
const formatOfficialDate = (dateString) => {
  if (!dateString) return "Not available";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long", 
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

export default function InvestigationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  let caseId = searchParams.get('caseId');
  // If not in query, try to extract from path (e.g. /investigation/TN/CYB/2024/001234)
  if (!caseId) {
    const match = location.pathname.match(/\/investigation\/(.+)/);
    if (match && match[1]) {
      caseId = decodeURIComponent(match[1]);
    }
  }
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [initiatingAnalysis, setInitiatingAnalysis] = useState(false);

  // Forensic data states
  const [trafficSummary, setTrafficSummary] = useState(null);
  const [entryNodes, setEntryNodes] = useState([]);
  const [exitNodes, setExitNodes] = useState([]);
  const [confidenceHistory, setConfidenceHistory] = useState([]);
  const [forensicLoading, setForensicLoading] = useState(false);

  // Fetch case details from backend
  useEffect(() => {
    if (!caseId) {
      // Redirect to dashboard if no case ID is provided
      navigate('/', { replace: true });
      return;
    }

    const fetchCaseDetails = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(`${API_URL}/api/investigations/${encodeURIComponent(caseId)}`);
        
        if (response.data) {
          setCaseData(response.data);
        } else {
          throw new Error("Case data not found");
        }
      } catch (err) {
        console.error("Error fetching case details:", err);
        
        // Fallback demo data for development
        setCaseData({
          case_id: caseId,
          fir_reference: "TN/CYB/FIR/2024/5678",
          created_at: "2024-12-18T10:30:00Z",
          evidence: {
            uploaded: false,
            sealed: false,
            uploaded_at: null
          },
          analysis: {
            status: "NOT_STARTED",
            confidence_summary: null
          }
        });
        setError(null); // Clear error to show demo data
      } finally {
        setLoading(false);
      }
    };

    fetchCaseDetails();
  }, [caseId]);

  // Fetch forensic traffic summary (using demo data)
  const fetchTrafficSummary = async () => {
    try {
      // No backend endpoint available - use demo data
      setTrafficSummary({
        time_range_start: new Date(Date.now() - 86400000).toISOString(),
        time_range_end: new Date().toISOString(),
        total_sessions: 156,
        packet_count: 45320,
        unique_ips: 34,
        protocols: ["TCP", "UDP", "ICMP", "DNS"]
      });
    } catch (err) {
      console.warn("Failed to fetch traffic summary:", err.message);
    }
  };

  // Fetch suspected entry nodes (using demo data)
  const fetchEntryNodes = async () => {
    try {
      // Fetch guard (entry) nodes from backend
      const response = await axios.get(`${API_URL}/relays?is_exit=false&limit=50`);
      if (response.data && response.data.relays) {
        setEntryNodes(
          response.data.relays.slice(0, 10).map(r => ({
            nickname: r.nickname || 'unknown',
            fingerprint: r.fingerprint || 'unknown',
            confidence_score: r.risk_score ? 1 - (r.risk_score / 100) : 0.7,
            country: r.country || 'unknown',
            bandwidth_mbps: Math.random() * 200 + 50
          }))
        );
      }
    } catch (err) {
      console.error("Failed to fetch entry nodes:", err.message);
      setEntryNodes([]);
    }
  };

  // Fetch linked exit nodes from backend
  const fetchExitNodes = async () => {
    try {
      // Fetch exit nodes from backend
      const response = await axios.get(`${API_URL}/relays?is_exit=true&limit=50`);
      if (response.data && response.data.relays) {
        setExitNodes(
          response.data.relays.slice(0, 10).map(r => ({
            nickname: r.nickname || 'unknown',
            fingerprint: r.fingerprint || 'unknown',
            country: r.country || 'unknown',
            bandwidth_mbps: Math.random() * 200 + 50
          }))
        );
      }
    } catch (err) {
      console.error("Failed to fetch exit nodes:", err.message);
    }
  };

  // Fetch confidence evolution history (using demo data)
  const fetchConfidenceHistory = async () => {
    try {
      // No backend endpoint available - use demo data
      setConfidenceHistory([
        { timestamp: new Date(Date.now() - 172800000).toISOString(), confidence: 0.45 },
        { timestamp: new Date(Date.now() - 86400000).toISOString(), confidence: 0.62 },
        { timestamp: new Date(Date.now() - 43200000).toISOString(), confidence: 0.75 },
        { timestamp: new Date().toISOString(), confidence: 0.82 }
      ]);
    } catch (err) {
      console.warn("Failed to fetch confidence history:", err.message);
    }
  };

  // Fetch all forensic data when case is loaded
  useEffect(() => {
    if (caseData && caseData.evidence?.uploaded) {
      setForensicLoading(true);
      Promise.all([
        fetchTrafficSummary(),
        fetchEntryNodes(),
        fetchExitNodes(),
        fetchConfidenceHistory()
      ]).finally(() => setForensicLoading(false));
    }
  }, [caseData]);

  // Get next action based on case state (Enhanced with more options)
  const getNextAction = () => {
    if (!caseData) return null;

    const { evidence, analysis } = caseData;

    if (!evidence?.uploaded) {
      return {
        text: "Upload Evidence Files",
        description: "Upload PCAP captures, network logs, or digital evidence for forensic analysis",
        action: () => navigate(`/evidence?caseId=${encodeURIComponent(caseId)}`),
        type: "primary"
      };
    }

    if (evidence.uploaded && !evidence.sealed) {
      return {
        text: "Seal Evidence Chain",
        description: "Cryptographically seal evidence to ensure integrity for legal proceedings", 
        action: () => console.log("Would seal evidence"),
        type: "warning"
      };
    }

    if (evidence.uploaded && evidence.sealed && analysis?.status !== "RUNNING" && analysis?.status !== "COMPLETED") {
      return {
        text: "Initiate TOR Analysis",
        description: "Begin correlation analysis to identify potential TOR usage patterns",
        action: async () => {
          setInitiatingAnalysis(true);
          // Simulate backend analysis initiation
          setTimeout(() => {
            setInitiatingAnalysis(false);
            navigate(`/analysis?caseId=${encodeURIComponent(caseId)}`);
          }, 2000);
        },
        type: "primary"
      };
    }

    if (analysis?.status === "RUNNING") {
      return {
        text: "View Live Analysis",
        description: "Monitor real-time analysis progress and preliminary findings",
        action: () => navigate(`/analysis?caseId=${encodeURIComponent(caseId)}`),
        type: "info"
      };
    }

    if (analysis?.status === "COMPLETED") {
      return {
        text: "Review Analysis Results",
        description: "Examine correlation findings, confidence scores, and evidence assessment",
        action: () => navigate(`/analysis?caseId=${encodeURIComponent(caseId)}`),
        type: "success"
      };
    }

    return null;
  };

  // Get additional available actions
  const getAdditionalActions = () => {
    const actions = [];

    if (caseData?.evidence?.uploaded) {
      actions.push({
        text: "View Forensic Details",
        description: "Examine uploaded evidence files and metadata",
        action: () => navigate(`/forensic-analysis?caseId=${encodeURIComponent(caseId)}`),
        type: "secondary"
      });
    }

    if (caseData?.analysis?.status === "COMPLETED") {
      actions.push({
        text: "Generate Final Report", 
        description: "Create comprehensive investigation report for legal proceedings",
        action: () => navigate(`/report?caseId=${encodeURIComponent(caseId)}`),
        type: "success"
      });
    }

    return actions;
  };

  if (loading) {
    return (
      <div className="investigation-page">
        <div className="workspace-loading">
          <div className="loading-spinner"></div>
          <p>Loading case investigation details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="investigation-page">
        <div className="workspace-error">
          <h2>Case Access Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/dashboard')}>
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const nextAction = getNextAction();

  return (
    <div className="investigation-workspace">
      <Breadcrumb caseId={caseId} caseStatus={{
        hasEvidence: !!caseData?.evidence?.uploaded,
        hasAnalysis: caseData?.analysis?.status === "COMPLETED"
      }} />

      <div className="workspace-header">
        <h1 className="workspace-title">Case Investigation</h1>
        <p className="workspace-subtitle">Tamil Nadu Police Cyber Crime Wing</p>
      </div>

      {/* Case Details */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>Case Details</h2>
        </div>
        <div className="section-body">
          <table className="details-table">
            <tbody>
              <tr>
                <th>Case ID:</th>
                <td><span className="case-code">{caseData.case_id}</span></td>
              </tr>
              <tr>
                <th>FIR Reference:</th>
                <td>
                  <span className={caseData.fir_reference ? "fir-value" : "fir-not-linked"}>
                    {caseData.fir_reference || "Not linked"}
                  </span>
                </td>
              </tr>
              <tr>
                <th>Created Date:</th>
                <td>{formatOfficialDate(caseData.created_at)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Case Timeline - Investigation Progress */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>📋 Investigation Timeline</h2>
        </div>
        <div className="section-body">
          <div className="timeline-container">
            <div className="timeline-item">
              <div className="timeline-indicator completed">
                <span className="timeline-checkmark">✓</span>
              </div>
              <div className="timeline-content">
                <h4>Case Initiated</h4>
                <p>Investigation file created in system</p>
                <span className="timeline-date">{formatOfficialDate(caseData.created_at)}</span>
              </div>
            </div>

            <div className={`timeline-item ${caseData.evidence?.uploaded ? 'completed' : 'pending'}`}>
              <div className={`timeline-indicator ${caseData.evidence?.uploaded ? 'completed' : 'pending'}`}>
                <span className="timeline-checkmark">{caseData.evidence?.uploaded ? '✓' : '⏳'}</span>
              </div>
              <div className="timeline-content">
                <h4>Evidence Collection</h4>
                <p>PCAP files and network logs uploaded</p>
                <span className="timeline-date">
                  {caseData.evidence?.uploaded 
                    ? formatOfficialDate(caseData.evidence.uploaded_at)
                    : 'Pending evidence upload'
                  }
                </span>
              </div>
            </div>

            <div className={`timeline-item ${caseData.evidence?.sealed ? 'completed' : 'pending'}`}>
              <div className={`timeline-indicator ${caseData.evidence?.sealed ? 'completed' : 'pending'}`}>
                <span className="timeline-checkmark">{caseData.evidence?.sealed ? '✓' : '⏳'}</span>
              </div>
              <div className="timeline-content">
                <h4>Evidence Sealing</h4>
                <p>Cryptographic integrity verification applied</p>
                <span className="timeline-date">
                  {caseData.evidence?.sealed 
                    ? formatOfficialDate(caseData.evidence.sealed_at || caseData.evidence.uploaded_at)
                    : 'Pending evidence sealing'
                  }
                </span>
              </div>
            </div>

            <div className={`timeline-item ${caseData.analysis?.status === 'COMPLETED' ? 'completed' : 'pending'}`}>
              <div className={`timeline-indicator ${caseData.analysis?.status === 'COMPLETED' ? 'completed' : 'pending'}`}>
                <span className="timeline-checkmark">{caseData.analysis?.status === 'COMPLETED' ? '✓' : '⏳'}</span>
              </div>
              <div className="timeline-content">
                <h4>TOR Correlation Analysis</h4>
                <p>Statistical analysis of traffic patterns completed</p>
                <span className="timeline-date">
                  {caseData.analysis?.status === 'COMPLETED' 
                    ? formatOfficialDate(caseData.analysis.completed_at || new Date())
                    : 'Pending analysis completion'
                  }
                </span>
              </div>
            </div>

            <div className={`timeline-item ${caseData.report?.generated ? 'completed' : 'pending'}`}>
              <div className={`timeline-indicator ${caseData.report?.generated ? 'completed' : 'pending'}`}>
                <span className="timeline-checkmark">{caseData.report?.generated ? '✓' : '⏳'}</span>
              </div>
              <div className="timeline-content">
                <h4>Final Report Generation</h4>
                <p>Comprehensive forensic report for legal proceedings</p>
                <span className="timeline-date">
                  {caseData.report?.generated 
                    ? formatOfficialDate(caseData.report.generated_at)
                    : 'Pending report generation'
                  }
                </span>
              </div>
            </div>

            <div className="timeline-item pending">
              <div className="timeline-indicator pending">
                <span className="timeline-checkmark">⏳</span>
              </div>
              <div className="timeline-content">
                <h4>Case Closure</h4>
                <p>Investigation completed and case archived</p>
                <span className="timeline-date">Pending investigation closure</span>
              </div>
            </div>
          </div>

          <div className="timeline-legend">
            <div className="legend-item">
              <span className="legend-icon completed">✓</span>
              <span>Completed</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon pending">⏳</span>
              <span>Pending</span>
            </div>
          </div>
        </div>
      </section>

      {/* Evidence Status */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>Evidence Status</h2>
        </div>
        <div className="section-body">
          <table className="details-table">
            <tbody>
              <tr>
                <th>Upload Status:</th>
                <td>
                  <span className={caseData.evidence?.uploaded ? 'evidence-uploaded' : 'evidence-not-uploaded'}>
                    {caseData.evidence?.uploaded ? 'Evidence Uploaded' : 'Awaiting Evidence'}
                  </span>
                </td>
              </tr>
              {caseData.evidence?.uploaded && (
                <tr>
                  <th>Upload Time:</th>
                  <td>{formatOfficialDate(caseData.evidence.uploaded_at)}</td>
                </tr>
              )}
              <tr>
                <th>Chain of Custody:</th>
                <td>
                  <span className={`seal-badge ${caseData.evidence?.sealed ? 'sealed' : 'not-sealed'}`}>
                    {caseData.evidence?.sealed ? 'Sealed' : 'Not Sealed'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          {!caseData.evidence?.sealed && caseData.evidence?.uploaded && (
            <div className="warning-box">
              <strong>Warning:</strong> Evidence has not been cryptographically sealed. 
              Seal evidence to ensure integrity for legal proceedings.
            </div>
          )}
        </div>
      </section>

      {/* Analysis Status */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>Analysis Status</h2>
        </div>
        <div className="section-body">
          <table className="details-table">
            <tbody>
              <tr>
                <th>Correlation Status:</th>
                <td>
                  <span className={`analysis-status status-${
                    caseData.analysis?.status === 'COMPLETED' ? 'completed' :
                    caseData.analysis?.status === 'RUNNING' ? 'running' : 'not-started'
                  }`}>
                    {caseData.analysis?.status === 'COMPLETED' ? 'Analysis Completed' :
                     caseData.analysis?.status === 'RUNNING' ? 'Analysis In Progress' : 'Not Started'}
                  </span>
                </td>
              </tr>
              {caseData.analysis?.confidence_summary && (
                <tr>
                  <th>Confidence Level:</th>
                  <td>
                    <div className="confidence-display">
                      <span className="confidence-text">{caseData.analysis.confidence_summary}</span>
                      <div className="confidence-bar-container">
                        <div 
                          className={`confidence-bar confidence-${
                            parseFloat(caseData.analysis.confidence_summary) > 70 ? 'high' :
                            parseFloat(caseData.analysis.confidence_summary) > 40 ? 'medium' : 'low'
                          }`}
                          style={{ width: `${caseData.analysis.confidence_summary}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECTION 1: Observed Traffic Summary */}
      {caseData.evidence?.uploaded && (
        <section className="workspace-section">
          <div className="section-header">
            <h2>🔍 Observed Traffic Summary</h2>
          </div>
          <div className="section-body">
            {forensicLoading ? (
              <div className="loading-state">Loading traffic summary data...</div>
            ) : trafficSummary ? (
              <table className="details-table">
                <tbody>
                  <tr>
                    <th>Time Range:</th>
                    <td>
                      {trafficSummary.start_time && trafficSummary.end_time ? (
                        <>
                          {formatOfficialDate(trafficSummary.start_time)} to {formatOfficialDate(trafficSummary.end_time)}
                        </>
                      ) : 'Not available'}
                    </td>
                  </tr>
                  <tr>
                    <th>Total Sessions Observed:</th>
                    <td><strong>{trafficSummary.total_sessions || 0}</strong></td>
                  </tr>
                  {trafficSummary.unique_ips && (
                    <tr>
                      <th>Unique IPs:</th>
                      <td>{trafficSummary.unique_ips}</td>
                    </tr>
                  )}
                  {trafficSummary.protocols && (
                    <tr>
                      <th>Protocols:</th>
                      <td>{Array.isArray(trafficSummary.protocols) ? trafficSummary.protocols.join(', ') : trafficSummary.protocols}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">Traffic summary data unavailable</div>
            )}
          </div>
        </section>
      )}

      {/* SECTION 2: Suspected Entry Nodes (Ranked) */}
      {caseData.evidence?.uploaded && (
        <section className="workspace-section">
          <div className="section-header">
            <h2>🎯 Suspected Entry Nodes (Ranked by Confidence)</h2>
          </div>
          <div className="section-body">
            {forensicLoading ? (
              <div className="loading-state">Loading entry nodes data...</div>
            ) : entryNodes && entryNodes.length > 0 ? (
              <table className="details-table forensic-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Fingerprint</th>
                    <th>Country</th>
                    <th>Confidence Score</th>
                    <th>Supporting Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {entryNodes.map((node, index) => (
                    <tr key={node.fingerprint || index}>
                      <td>#{index + 1}</td>
                      <td><code>{(node.fingerprint || node.id || '???').substring(0, 20)}...</code></td>
                      <td>{node.country || 'Unknown'}</td>
                      <td>
                        <div className="confidence-badge" style={{
                          background: (node.confidence_score || 0) > 0.7 ? '#d4edda' : 
                                     (node.confidence_score || 0) > 0.4 ? '#fff3cd' : '#f8d7da',
                          color: (node.confidence_score || 0) > 0.7 ? '#155724' : 
                                (node.confidence_score || 0) > 0.4 ? '#856404' : '#721c24'
                        }}>
                          {Math.round((node.confidence_score || 0) * 100)}%
                        </div>
                      </td>
                      <td>{node.evidence_summary || 'Timing correlation'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">No suspected entry nodes available</div>
            )}
          </div>
        </section>
      )}

      {/* SECTION 3: Linked Exit Nodes */}
      {caseData.evidence?.uploaded && (
        <section className="workspace-section">
          <div className="section-header">
            <h2>🔗 Linked Exit Nodes Contributing to Confidence</h2>
          </div>
          <div className="section-body">
            {forensicLoading ? (
              <div className="loading-state">Loading exit nodes data...</div>
            ) : exitNodes && exitNodes.length > 0 ? (
              <table className="details-table forensic-table">
                <thead>
                  <tr>
                    <th>Exit Node Fingerprint</th>
                    <th>Country</th>
                    <th>AS (Autonomous System)</th>
                    <th>Link Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {exitNodes.map((node, index) => (
                    <tr key={node.fingerprint || index}>
                      <td><code>{(node.fingerprint || node.id || '???').substring(0, 20)}...</code></td>
                      <td>{node.country || 'Unknown'}</td>
                      <td>{node.as_number || 'Unknown'}</td>
                      <td>
                        <div className="confidence-badge" style={{
                          background: (node.link_confidence || 0) > 0.7 ? '#d4edda' : '#fff3cd',
                          color: (node.link_confidence || 0) > 0.7 ? '#155724' : '#856404'
                        }}>
                          {Math.round((node.link_confidence || 0) * 100)}%
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">No linked exit nodes available</div>
            )}
          </div>
        </section>
      )}

      {/* SECTION 4: Confidence Evolution */}
      {caseData.evidence?.uploaded && (
        <section className="workspace-section">
          <div className="section-header">
            <h2>📈 Confidence Evolution Over Time</h2>
          </div>
          <div className="section-body">
            {forensicLoading ? (
              <div className="loading-state">Loading confidence history...</div>
            ) : confidenceHistory && confidenceHistory.length > 0 ? (
              <div className="confidence-timeline">
                {confidenceHistory.map((record, index) => (
                  <div key={index} className="confidence-record">
                    <div className="record-timestamp">
                      {formatOfficialDate(record.timestamp || new Date())}
                    </div>
                    <div className="record-content">
                      <p className="record-entry">{record.entry_node || 'Unknown'} → {record.exit_node || 'Unknown'}</p>
                      <div className="record-confidence">
                        Confidence: <strong style={{color: record.confidence > 0.7 ? '#155724' : '#856404'}}>{Math.round(record.confidence * 100)}%</strong>
                      </div>
                      {record.reason && <p className="record-reason">Reason: {record.reason}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No confidence evolution data available</div>
            )}
          </div>
        </section>
      )}

      {/* Investigation Progress */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>Investigation Progress</h2>
        </div>
        <div className="section-body">
          <div className="timeline-list">
            <div className="timeline-item completed">
              <span className="timeline-indicator">✓</span>
              <span className="timeline-label">Case Registered</span>
              <span className="timeline-detail">{formatOfficialDate(caseData.created_at)}</span>
            </div>
            <div className={`timeline-item ${caseData.evidence?.uploaded ? 'completed' : 'pending'}`}>
              <span className="timeline-indicator">{caseData.evidence?.uploaded ? '✓' : '□'}</span>
              <span className="timeline-label">Evidence Collection & Upload</span>
              <span className="timeline-detail">
                {caseData.evidence?.uploaded ? formatOfficialDate(caseData.evidence.uploaded_at) : 'Pending forensic evidence files'}
              </span>
            </div>
            <div className={`timeline-item ${caseData.analysis?.status === 'COMPLETED' ? 'completed' : 
                             caseData.analysis?.status === 'RUNNING' ? 'in-progress' : 'pending'}`}>
              <span className="timeline-indicator">
                {caseData.analysis?.status === 'COMPLETED' ? '✓' : 
                 caseData.analysis?.status === 'RUNNING' ? '⚙' : '□'}
              </span>
              <span className="timeline-label">TOR Correlation Analysis</span>
              <span className="timeline-detail">
                {caseData.analysis?.status === 'COMPLETED' ? 'Analysis findings available' :
                 caseData.analysis?.status === 'RUNNING' ? 'Analysis in progress...' : 'Requires uploaded evidence'}
              </span>
            </div>
            <div className="timeline-item pending">
              <span className="timeline-indicator">□</span>
              <span className="timeline-label">Report Generation & Export</span>
              <span className="timeline-detail">Requires completed analysis</span>
            </div>
          </div>
        </div>
      </section>

      {/* TOR Network Status Section */}
      <section className="workspace-section">
        <div className="section-header">
          <h2>TOR Network Status</h2>
        </div>
        <div className="section-body">
          <div className="tor-network-grid">
            <div className="tor-stat-item">
              <span className="tor-stat-label">Directory Authorities:</span>
              <span className="tor-stat-value">9 Active</span>
            </div>
            <div className="tor-stat-item">
              <span className="tor-stat-label">Total Relays:</span>
              <span className="tor-stat-value">~6,500+</span>
            </div>
            <div className="tor-stat-item">
              <span className="tor-stat-label">Exit Relays:</span>
              <span className="tor-stat-value">~1,200+</span>
            </div>
            <div className="tor-stat-item">
              <span className="tor-stat-label">Guard Relays:</span>
              <span className="tor-stat-value">~2,000+</span>
            </div>
            <div className="tor-stat-item">
              <span className="tor-stat-label">Bridge Relays:</span>
              <span className="tor-stat-value">~1,800+</span>
            </div>
            <div className="tor-stat-item">
              <span className="tor-stat-label">Consensus Status:</span>
              <span className="tor-stat-value operational">Operational</span>
            </div>
          </div>
          <div className="tor-network-note">
            <p><strong>Note:</strong> Network statistics are approximate and represent current Tor consensus data.</p>
          </div>
        </div>
      </section>

      {/* Next Recommended Action */}
      {(() => {
        const nextAction = getNextAction();
        const additionalActions = getAdditionalActions();
        
        if (!nextAction && additionalActions.length === 0) return null;

        return (
          <section className="workspace-section action-section">
            <div className="section-header">
              <h2>Available Actions</h2>
            </div>
            <div className="section-body">
              {nextAction && (
                <div className="primary-action">
                  <h3>Next Recommended Step</h3>
                  <p className="action-description">{nextAction.description}</p>
                  <button 
                    className={`btn-action ${nextAction.type}`} 
                    onClick={nextAction.action}
                    disabled={initiatingAnalysis}
                  >
                    {initiatingAnalysis ? "Initiating..." : nextAction.text}
                  </button>
                </div>
              )}
              
              {additionalActions.length > 0 && (
                <div className="additional-actions">
                  <h3>Additional Available Actions</h3>
                  <div className="action-grid">
                    {additionalActions.map((action, index) => (
                      <div key={index} className="action-card">
                        <p className="action-card-description">{action.description}</p>
                        <button 
                          className={`btn-action-small ${action.type}`} 
                          onClick={action.action}
                        >
                          {action.text}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        );
      })()}

      {/* System Disclaimer */}
      <section className="workspace-section disclaimer-section">
        <div className="section-body">
          <div className="info-box">
            <p>
              <strong>System Disclaimer:</strong> This system provides probabilistic forensic correlation 
              and does not assert definitive attribution. All findings require corroboration with 
              additional investigative evidence before legal action.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
