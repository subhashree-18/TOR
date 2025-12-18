/**
 * AnalysisPage.js ??? CORE PROBLEM STATEMENT UI
 * Tamil Nadu Police Cyber Crime Wing - TOR Traffic Correlation Analysis
 * 
 * Presents backend-generated TOR correlation results as probabilistic forensic intelligence
 * Aligned with TN Police Hackathon problem statement
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import "./AnalysisPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Map confidence level to percentage for bar display
const getConfidencePercent = (level) => {
  switch (level?.toLowerCase()) {
    case "high": return 85;
    case "medium": return 55;
    case "low": return 25;
    default: return 0;
  }
};

// Get confidence bar class
const getConfidenceClass = (level) => {
  switch (level?.toLowerCase()) {
    case "high": return "confidence-high";
    case "medium": return "confidence-medium";
    case "low": return "confidence-low";
    default: return "";
  }
};

export default function AnalysisPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const caseId = location.state?.caseId || "TN/CYB/2024/001234";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedHypothesis, setExpandedHypothesis] = useState(null);
  const [limitationsExpanded, setLimitationsExpanded] = useState(false);
  const [analysisData, setAnalysisData] = useState({
    hypotheses: []
  });
  const [caseStatus, setCaseStatus] = useState(null);

  // Route guard - check if evidence is uploaded
  useEffect(() => {
    const checkCaseStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/investigations/${encodeURIComponent(caseId)}`);
        const caseData = response.data;
        
        if (!caseData.evidence?.uploaded) {
          setError("Please complete the previous investigation stage to proceed.");
          setLoading(false);
          return;
        }
        
        setCaseStatus(caseData);
      } catch (err) {
        console.warn("Could not verify case status, proceeding with analysis");
        setCaseStatus({ evidence: { uploaded: true } }); // Allow demo mode
      }
    };
    
    checkCaseStatus();
  }, [caseId]);

  // Fetch analysis results from backend
  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(
          `${API_URL}/api/analysis/${encodeURIComponent(caseId)}`
        );

        if (response.data) {
          setAnalysisData(response.data);
        }
      } catch (err) {
        console.warn("Backend not available, using mock data:", err.message);

        // Mock data for demonstration when backend unavailable
        setAnalysisData({
          hypotheses: [
            {
              rank: 1,
              entry_region: "Germany (DE)",
              exit_region: "Netherlands (NL)",
              evidence_count: 847,
              confidence_level: "High",
              explanation: {
                timing_consistency: "Strong temporal alignment observed in 87% of traffic samples",
                guard_persistence: "Entry node maintained consistent uptime during analysis window",
                evidence_strength: "High correlation between session timing and known Tor relay patterns"
              }
            },
            {
              rank: 2,
              entry_region: "France (FR)",
              exit_region: "United States (US)",
              evidence_count: 612,
              confidence_level: "High",
              explanation: {
                timing_consistency: "Moderate-to-strong temporal correlation in 72% of samples",
                guard_persistence: "French relay showed stable operation with minimal downtime",
                evidence_strength: "Clear session boundaries with expected latency patterns"
              }
            },
            {
              rank: 3,
              entry_region: "United Kingdom (GB)",
              exit_region: "Germany (DE)",
              evidence_count: 489,
              confidence_level: "Medium",
              explanation: {
                timing_consistency: "Moderate correlation with some timing gaps",
                guard_persistence: "UK relay exhibited intermittent availability",
                evidence_strength: "Evidence supports hypothesis but with some uncertainty"
              }
            },
            {
              rank: 4,
              entry_region: "Switzerland (CH)",
              exit_region: "Sweden (SE)",
              evidence_count: 356,
              confidence_level: "Medium",
              explanation: {
                timing_consistency: "Partial temporal alignment with acceptable deviation",
                guard_persistence: "Swiss infrastructure shows privacy-focused operation",
                evidence_strength: "Moderate evidence weight with good protocol signatures"
              }
            },
            {
              rank: 5,
              entry_region: "Romania (RO)",
              exit_region: "Finland (FI)",
              evidence_count: 234,
              confidence_level: "Medium",
              explanation: {
                timing_consistency: "Weak-to-moderate correlation patterns",
                guard_persistence: "Romanian relay shows high variability",
                evidence_strength: "Limited evidence but consistent with Tor usage"
              }
            },
            {
              rank: 6,
              entry_region: "Canada (CA)",
              exit_region: "Japan (JP)",
              evidence_count: 178,
              confidence_level: "Low",
              explanation: {
                timing_consistency: "Weak temporal alignment due to timezone differences",
                guard_persistence: "Trans-Pacific path shows unusual characteristics",
                evidence_strength: "Insufficient evidence for confident attribution"
              }
            }
          ]
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [caseId]);

  // Navigate to report
  const handleViewReport = () => {
    navigate("/report", { state: { caseId, analysisData } });
  };

  return (
    <div className="analysis-page">
      {/* Breadcrumb */}
      <nav className="analysis-breadcrumb">
        <span className="crumb" onClick={() => navigate("/dashboard")}>Dashboard</span>
        <span className="separator">/</span>
        <span className="crumb" onClick={() => navigate("/investigation", { state: { caseId } })}>Investigation</span>
        <span className="separator">/</span>
        <span className="crumb active">Analysis</span>
      </nav>

      {/* Page Header */}
      <div className="analysis-header">
        <h1 className="analysis-title">TOR Traffic Correlation Analysis</h1>
        <p className="analysis-subtitle">Case Reference: <code>{caseId}</code></p>
      </div>

      {/* Disclaimer - Always Visible */}
      <div className="analysis-disclaimer">
        <strong>DISCLAIMER:</strong> This analysis provides probabilistic correlation 
        and does not assert definitive attribution. Results are intended as investigative 
        intelligence only and require corroboration with additional evidence.
      </div>

      {/* Correlation Method Summary */}
      <section className="analysis-section">
        <div className="section-header">
          <h2>Correlation Method Summary</h2>
        </div>
        <div className="section-body">
          <p className="method-description">
            Time-based correlation of observed traffic with TOR relay activity across entry and exit nodes.
          </p>
        </div>
      </section>

      {/* Confidence Evolution Note */}
      <section className="analysis-section">
        <div className="section-header">
          <h2>Confidence Evolution</h2>
        </div>
        <div className="section-body">
          <p className="confidence-note">
            Confidence improves as additional exit-node evidence is correlated.
          </p>
        </div>
      </section>

      {loading ? (
        <div className="analysis-loading">
          <div className="loading-spinner"></div>
          <p>Loading analysis findings...</p>
        </div>
      ) : error ? (
        <div className="analysis-error">
          <h2>Access Restricted</h2>
          <p>{error}</p>
          <div className="error-actions">
            <button 
              className="btn-primary"
              onClick={() => navigate(`/investigation/${caseId}`)}
            >
              Go to Investigation Page
            </button>
            <button 
              className="btn-secondary"
              onClick={() => navigate('/dashboard')}
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      ) : caseStatus && (
        <>
          {/* Ranked Hypotheses Table Section */}
          <section className="analysis-section">
            <div className="section-header">
              <h2>Ranked Hypotheses</h2>
            </div>
            <div className="section-body">
              {analysisData.hypotheses.length === 0 ? (
                <div className="no-data">
                  <p>No correlation hypotheses available. Ensure evidence has been uploaded and processed.</p>
                </div>
              ) : (
                <>
                  <div className="table-container">
                    <table className="hypotheses-table">
                      <thead>
                        <tr>
                          <th className="th-rank">Rank</th>
                          <th className="th-entry">Probable Entry Node Region</th>
                          <th className="th-exit">Exit Node Region</th>
                          <th className="th-evidence">Evidence Count</th>
                          <th className="th-confidence">Confidence Level</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisData.hypotheses.map((hypothesis, index) => (
                          <React.Fragment key={index}>
                            <tr className={`hypothesis-row rank-${hypothesis.rank}`}>
                              <td className="td-rank">
                                <span className="rank-number">{hypothesis.rank}</span>
                              </td>
                              <td className="td-entry">{hypothesis.entry_region}</td>
                              <td className="td-exit">{hypothesis.exit_region}</td>
                              <td className="td-evidence">{hypothesis.evidence_count.toLocaleString()}</td>
                              <td className="td-confidence">
                                <div className="confidence-cell">
                                  <span className={`confidence-text ${getConfidenceClass(hypothesis.confidence_level)}`}>
                                    {hypothesis.confidence_level}
                                  </span>
                                  <div className="confidence-bar-container">
                                    <div 
                                      className={`confidence-bar ${getConfidenceClass(hypothesis.confidence_level)}`}
                                      style={{ width: `${getConfidencePercent(hypothesis.confidence_level)}%` }}
                                    ></div>
                                  </div>
                                  {hypothesis.explanation && (
                                    <button 
                                      className="btn-explain"
                                      onClick={() => setExpandedHypothesis(
                                        expandedHypothesis === hypothesis.rank ? null : hypothesis.rank
                                      )}
                                    >
                                      Why this confidence?
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                            
                            {/* Collapsible Explanation Row */}
                            {expandedHypothesis === hypothesis.rank && hypothesis.explanation && (
                              <tr className="explanation-row">
                                <td colSpan="5">
                                  <div className="explanation-content">
                                    <h4>Why this confidence?</h4>
                                    <div className="explanation-factors">
                                      <div className="factor-item">
                                        <strong>Evidence Count:</strong> {hypothesis.evidence_count.toLocaleString()} packet sequences analyzed
                                      </div>
                                      <div className="factor-item">
                                        <strong>Timing Correlation:</strong> {hypothesis.explanation.timing_consistency}
                                      </div>
                                      <div className="factor-item">
                                        <strong>Guard Persistence:</strong> {hypothesis.explanation.guard_persistence}
                                      </div>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Table Footer Note */}
                  <div className="table-note">
                    * Hypotheses are ranked by correlation strength. Higher evidence counts 
                    indicate more observed traffic patterns matching the entry-exit pair.
                  </div>
                </>
              )}
            </div>
          </section>

          {/* Summary Section */}
          <section className="analysis-section">
            <div className="section-header">
              <h2>Analysis Summary</h2>
            </div>
            <div className="section-body">
              <table className="summary-table">
                <tbody>
                  <tr>
                    <th>Total Hypotheses Generated</th>
                    <td>{analysisData.hypotheses.length}</td>
                  </tr>
                  <tr>
                    <th>High Confidence</th>
                    <td>{analysisData.hypotheses.filter(h => h.confidence_level === "High").length}</td>
                  </tr>
                  <tr>
                    <th>Medium Confidence</th>
                    <td>{analysisData.hypotheses.filter(h => h.confidence_level === "Medium").length}</td>
                  </tr>
                  <tr>
                    <th>Low Confidence</th>
                    <td>{analysisData.hypotheses.filter(h => h.confidence_level === "Low").length}</td>
                  </tr>
                  <tr>
                    <th>Total Evidence Points</th>
                    <td>{analysisData.hypotheses.reduce((sum, h) => sum + h.evidence_count, 0).toLocaleString()}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Analytical Limitations */}
          <section className="analysis-section analysis-limitations">
            <div className="section-header">
              <h2>Analytical Limitations</h2>
              <button 
                className="btn-expand"
                onClick={() => setLimitationsExpanded(!limitationsExpanded)}
              >
                {limitationsExpanded ? 'Hide' : 'Show'} Limitations
              </button>
            </div>
            
            {limitationsExpanded && (
              <div className="section-body">
                <div className="limitation-box">
                  <div className="limitation-item">
                    <strong>This analysis does NOT deanonymize TOR users.</strong> All correlations are probabilistic estimates based on traffic patterns and timing analysis. Individual user identification is not possible through this system.
                  </div>
                  <div className="limitation-item">
                    <strong>Confidence levels reflect statistical correlation strength,</strong> not certainty of criminal activity. High confidence indicates strong pattern matches but requires additional investigative verification.
                  </div>
                  <div className="limitation-item">
                    <strong>Analysis quality improves with larger datasets.</strong> Single-session captures may yield lower confidence results. Extended monitoring periods provide more reliable correlation patterns.
                  </div>
                  <div className="limitation-item">
                    <strong>Geographic precision varies by infrastructure density.</strong> Rural or lower-infrastructure regions may show broader location estimates compared to metropolitan areas.
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Disclaimer */}
          <section className="analysis-section disclaimer-section">
            <div className="disclaimer">
              <p><strong>MANDATORY DISCLAIMER:</strong> This analysis is for investigative guidance only. All findings require verification through standard investigative procedures before legal action.</p>
            </div>
          </section>

          {/* Actions Section */}
          <section className="analysis-section action-section">
            <div className="section-header">
              <h2>Next Steps</h2>
            </div>
            <div className="section-body">
              <p className="action-text">
                Analysis complete. Review the hypotheses above and proceed to generate 
                a formal forensic report for case documentation.
              </p>
              <div className="action-buttons">
                <button className="btn-primary" onClick={handleViewReport}>
                  Generate Forensic Report
                </button>
                <button 
                  className="btn-secondary" 
                  onClick={() => navigate("/investigation", { state: { caseId } })}
                >
                  Back to Investigation
                </button>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
