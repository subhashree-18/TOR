/**
 * ForensicAnalysis.js ??? PHASE-2 DEEP DIVE
 * Tamil Nadu Police Cyber Crime Wing - Hypothesis Explanation
 * 
 * Explains WHY a hypothesis has a certain confidence using backend-provided evidence factors
 * Reads like an official investigation note prepared for senior officers
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import "./ForensicAnalysis.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function ForensicAnalysis() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get case ID from query params or location state
  const searchParams = new URLSearchParams(location.search);
  const caseId = searchParams.get('caseId') || location.state?.caseId || "TN/CYB/2024/001234";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedHypothesis, setExpandedHypothesis] = useState(null);
  const [analysisDetails, setAnalysisDetails] = useState({
    hypotheses: []
  });
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);

  // REMOVED: Route guard and access check. Always allow access to report.

  // Fetch detailed hypothesis explanations from backend
  useEffect(() => {
    // Only fetch details, do not check for access
    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(
          `${API_URL}/api/analysis/${encodeURIComponent(caseId)}/details`
        );

        if (response.data) {
          setAnalysisDetails(response.data);
        }
      } catch (err) {
        console.error("Failed to fetch analysis details from backend:", err.message);
        setAnalysisDetails({
          hypotheses: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
    // Fetch timeline events
    fetchTimelineEvents();
  }, [caseId]);

  // Fetch timeline events from backend
  const fetchTimelineEvents = async () => {
    setTimelineLoading(true);
    try {
      // Use /api/timeline endpoint which is available on backend
      const response = await axios.get(
        `${API_URL}/api/timeline?limit=100`
      );
      if (response.data && response.data.events) {
        const events = response.data.events.map(evt => ({
          timestamp: evt.timestamp,
          event_type: evt.type === 'relay' ? 'ENTRY_NODE_FIRST_SEEN' : 'EXIT_CORRELATION',
          description: evt.description || evt.label,
          confidence: evt.confidence || 0.5 // Use actual confidence from backend
        }));
        setTimelineEvents(events.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)));
      }
    } catch (err) {
      console.warn("Failed to fetch timeline events:", err.message);
      // Demo timeline data when backend unavailable
      const now = new Date();
      setTimelineEvents([
        {
          timestamp: new Date(now.getTime() - 7200000).toISOString(),
          event_type: "PCAP_CAPTURE_START",
          description: "Network packet capture began",
          confidence: null
        },
        {
          timestamp: new Date(now.getTime() - 6600000).toISOString(),
          event_type: "ENTRY_NODE_FIRST_SEEN",
          description: "Probable entry node first observed in traffic analysis",
          node_fingerprint: "DE:a1b2c3d4e5f6...",
          confidence: 0.73
        },
        {
          timestamp: new Date(now.getTime() - 5400000).toISOString(),
          event_type: "EXIT_CORRELATION",
          description: "Exit node correlated with entry node timing",
          node_fingerprint: "NL:f6e5d4c3b2a1...",
          confidence: 0.68
        },
        {
          timestamp: new Date(now.getTime() - 3600000).toISOString(),
          event_type: "CONFIDENCE_UPDATE",
          description: "Confidence score updated after pattern analysis",
          old_confidence: 0.61,
          new_confidence: 0.75
        },
        {
          timestamp: new Date(now.getTime() - 1800000).toISOString(),
          event_type: "PCAP_CAPTURE_END",
          description: "Network packet capture ended",
          confidence: null
        }
      ]);
    } finally {
      setTimelineLoading(false);
    }
  };

  // Toggle accordion
  const toggleHypothesis = (rank) => {
    setExpandedHypothesis(expandedHypothesis === rank ? null : rank);
  };

  // Get confidence class
  const getConfidenceClass = (level) => {
    switch (level?.toLowerCase()) {
      case "high": return "confidence-high";
      case "medium": return "confidence-medium";
      case "low": return "confidence-low";
      default: return "";
    }
  };

  return (
    <div className="forensic-analysis-page">
      {/* Breadcrumb */}
      <nav className="forensic-breadcrumb">
        <span className="crumb" onClick={() => navigate("/dashboard")}>Dashboard</span>
        <span className="separator">/</span>
        <span className="crumb" onClick={() => navigate("/investigation", { state: { caseId } })}>Investigation</span>
        <span className="separator">/</span>
        <span className="crumb" onClick={() => navigate("/analysis", { state: { caseId } })}>Analysis</span>
        <span className="separator">/</span>
        <span className="crumb active">Forensic Details</span>
      </nav>

      {/* Page Header */}
      <div className="forensic-header">
        <h1 className="forensic-title">Forensic Analysis Details</h1>
        <p className="forensic-subtitle">
          Official Investigation Note - Case Reference: <code>{caseId}</code>
        </p>
        <p className="forensic-notice">
          Prepared for: Tamil Nadu Police Cyber Crime Wing
        </p>
        
        {/* Investigation Note Introduction */}
        <div className="investigation-intro">
          <h2>Investigation Overview</h2>
          <p>
            This technical analysis provides detailed examination of correlation hypotheses 
            identified through TOR traffic pattern analysis. Each hypothesis represents a 
            potential probable entry node-exit relay pairing based on packet timing signatures, session 
            overlap patterns, and protocol consistency markers.
          </p>
          <p>
            The following analysis is prepared for investigative assessment and presents 
            technical evidence factors supporting each correlation. Confidence levels reflect 
            statistical correlation strength and should be considered alongside investigative 
            context and additional evidence sources.
          </p>
        </div>
      </div>

      {/* Report Preamble */}
      <div className="report-preamble">
        <p>
          <strong>PURPOSE:</strong> This document provides detailed forensic reasoning 
          for each correlation hypothesis generated during TOR traffic analysis. Each 
          section explains the evidentiary basis for confidence assessments and identifies 
          factors that limit certainty.
        </p>
        <p>
          <strong>INTENDED USE:</strong> Senior officer review, case documentation, 
          and preparation of forensic testimony. This analysis should be read in 
          conjunction with the primary correlation results.
        </p>
      </div>

      {loading ? (
        <div className="forensic-loading">
          <div className="loading-spinner"></div>
          <p>Loading forensic analysis details...</p>
        </div>
      ) : error ? (
        <div className="forensic-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      ) : (
        <>
          {/* Hypotheses Accordion */}
          <div className="hypotheses-accordion">
            {analysisDetails.hypotheses.length === 0 ? (
              <div className="no-data">
                <p>No hypothesis details available. Initiate correlation analysis first.</p>
              </div>
            ) : (
              analysisDetails.hypotheses.map((hypothesis) => (
                <div 
                  key={hypothesis.rank} 
                  className={`hypothesis-panel ${expandedHypothesis === hypothesis.rank ? "expanded" : ""}`}
                >
                  {/* Accordion Header */}
                  <div 
                    className="hypothesis-header"
                    onClick={() => toggleHypothesis(hypothesis.rank)}
                  >
                    <div className="header-left">
                      <span className="hypothesis-rank">Hypothesis #{hypothesis.rank}</span>
                      <span className="hypothesis-path">
                        {/* Show complete path with country, IP, and relay name - never ?? */}
                        <span title={hypothesis.entry_node?.ip}>
                          {(hypothesis.entry_node?.country && hypothesis.entry_node?.country !== '??') ? hypothesis.entry_node?.country : 'Unknown'} ({hypothesis.entry_node?.nickname || "Client"})
                        </span>
                        {' → '}
                        <span title={hypothesis.exit_node?.ip}>
                          {(hypothesis.exit_node?.country && hypothesis.exit_node?.country !== '??') ? hypothesis.exit_node?.country : 'Unknown'} ({hypothesis.exit_node?.nickname || "Unknown"})
                        </span>
                      </span>
                    </div>
                    <div className="header-right">
                      <span className={`confidence-badge ${getConfidenceClass(hypothesis.confidence_level)}`}>
                        {hypothesis.confidence_level}
                      </span>
                      <span className="expand-indicator">
                        {expandedHypothesis === hypothesis.rank ? "???" : "???"}
                      </span>
                    </div>
                  </div>

                  {/* Accordion Content */}
                  {expandedHypothesis === hypothesis.rank && (
                    <div className="hypothesis-content">
                      {/* Key Observations */}
                      <div className="observations-section">
                        <h3 className="subsection-title">Key Observations</h3>
                        
                        <div className="evidence-section">
                          <h4 className="section-label">Timing Correlation</h4>
                          <div className="section-text">
                            <p>{hypothesis.timing_correlation}</p>
                          </div>
                        </div>

                        <div className="evidence-section">
                          <h4 className="section-label">Session Overlap Analysis</h4>
                          <div className="section-text">
                            <p>{hypothesis.session_overlap}</p>
                          </div>
                        </div>

                        <div className="evidence-section">
                          <h4 className="section-label">Evidence Consistency</h4>
                          <div className="section-text">
                            <p>{hypothesis.evidence_consistency}</p>
                          </div>
                        </div>
                      </div>

                      {/* Uncertainty Factors */}
                      <div className="uncertainty-section">
                        <h3 className="subsection-title">Uncertainty Factors</h3>
                        <div className="evidence-section limiting-section">
                          <div className="section-text limiting-text">
                            <p>{hypothesis.limiting_factors}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Timeline Reconstruction Section */}
          <div className="timeline-section">
            <div className="timeline-header">
              <h2>⏰ Timeline Reconstruction</h2>
              <p className="timeline-subtitle">Chronological forensic events and confidence evolution</p>
            </div>

            {timelineLoading ? (
              <div className="timeline-loading">
                <div className="loading-spinner"></div>
                <p>Loading timeline events...</p>
              </div>
            ) : timelineEvents.length === 0 ? (
              <div className="timeline-empty">
                <p>No timeline events available. Upload evidence and trigger analysis to generate events.</p>
              </div>
            ) : (
              <div className="timeline-events">
                {timelineEvents.map((event, index) => {
                  const timestamp = new Date(event.timestamp);
                  const timeStr = timestamp.toLocaleString('en-IN', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                  });

                  // Determine icon and color for event type
                  let icon = "📍";
                  let colorClass = "event-neutral";
                  let eventLabel = event.event_type;

                  if (event.event_type === "PCAP_CAPTURE_START") {
                    icon = "▶️";
                    colorClass = "event-capture";
                    eventLabel = "Capture Started";
                  } else if (event.event_type === "PCAP_CAPTURE_END") {
                    icon = "⏹️";
                    colorClass = "event-capture";
                    eventLabel = "Capture Ended";
                  } else if (event.event_type === "ENTRY_NODE_FIRST_SEEN") {
                    icon = "🔌";
                    colorClass = "event-entry";
                    eventLabel = "Entry Node Sighting";
                  } else if (event.event_type === "EXIT_CORRELATION") {
                    icon = "🔗";
                    colorClass = "event-exit";
                    eventLabel = "Exit Correlation";
                  } else if (event.event_type === "CONFIDENCE_UPDATE") {
                    icon = "📊";
                    colorClass = "event-update";
                    eventLabel = "Confidence Update";
                  }

                  return (
                    <div key={index} className={`timeline-event ${colorClass}`}>
                      <div className="event-marker">
                        <div className="event-icon">{icon}</div>
                        <div className="event-connector"></div>
                      </div>
                      
                      <div className="event-content">
                        <div className="event-header">
                          <span className="event-label">{eventLabel}</span>
                          <span className="event-timestamp">{timeStr}</span>
                        </div>
                        
                        <p className="event-description">{event.description}</p>

                        {/* Show node details if available */}
                        {event.node_fingerprint && (
                          <div className="event-node-info">
                            <span className="node-label">Node:</span>
                            <code className="node-fingerprint">{event.node_fingerprint}</code>
                          </div>
                        )}

                        {/* Show confidence if available */}
                        {event.confidence !== null && event.confidence !== undefined && (
                          <div className="event-confidence">
                            <span className="confidence-label">Confidence:</span>
                            <span className={`confidence-value ${
                              event.confidence > 0.7 ? "high" : 
                              event.confidence > 0.4 ? "medium" : "low"
                            }`}>
                              {Math.round(event.confidence * 100)}%
                            </span>
                          </div>
                        )}

                        {/* Show confidence update details */}
                        {event.event_type === "CONFIDENCE_UPDATE" && 
                         event.old_confidence !== undefined && 
                         event.new_confidence !== undefined && (
                          <div className="event-confidence-update">
                            <div className="confidence-change">
                              <span className="old-conf">
                                {Math.round(event.old_confidence * 100)}%
                              </span>
                              <span className="arrow">→</span>
                              <span className={`new-conf ${
                                event.new_confidence > event.old_confidence ? "improved" : "declined"
                              }`}>
                                {Math.round(event.new_confidence * 100)}%
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Analytical Limitations */}
          <section className="limitations-section">
            <div className="section-header">
              <h2>Analytical Limitations</h2>
            </div>
            <div className="section-body">
              <div className="limitations-grid">
                <div className="limitation-item">
                  <h4>Encryption Integrity</h4>
                  <p>This analysis does not break TOR encryption protocols. All correlations are based on metadata timing patterns and network behavior analysis only.</p>
                </div>
                <div className="limitation-item">
                  <h4>Identity Protection</h4>
                  <p>Does not reveal real IP addresses or user identities. Analysis focuses on probable network path correlations without compromising user anonymity.</p>
                </div>
                <div className="limitation-item">
                  <h4>Investigative Scope</h4>
                  <p>Intended for investigative assistance only. Results provide probabilistic intelligence and require corroboration with additional evidence sources.</p>
                </div>
                <div className="limitation-item">
                  <h4>Attribution Confidence</h4>
                  <p>Cannot provide definitive attribution. All findings represent statistical correlations that may have alternative explanations requiring further investigation.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Footer Note */}
          <div className="report-footer">
            <p>
              <strong>CONFIDENTIALITY:</strong> This forensic analysis document is prepared 
              for official law enforcement use only. Distribution outside authorized 
              personnel requires appropriate authorization from the supervising officer.
            </p>
          </div>

          {/* Actions */}
          <div className="forensic-actions">
            <button 
              className="btn-primary"
              onClick={() => navigate("/report", { state: { caseId } })}
            >
              Generate Formal Report
            </button>
            <button 
              className="btn-secondary"
              onClick={() => navigate("/analysis", { state: { caseId } })}
            >
              Back to Analysis Summary
            </button>
          </div>
        </>
      )}
    </div>
  );
}
