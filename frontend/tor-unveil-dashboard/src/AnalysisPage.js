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
  const [analysisData, setAnalysisData] = useState({
    hypotheses: []
  });

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
              confidence_level: "High"
            },
            {
              rank: 2,
              entry_region: "France (FR)",
              exit_region: "United States (US)",
              evidence_count: 612,
              confidence_level: "High"
            },
            {
              rank: 3,
              entry_region: "United Kingdom (GB)",
              exit_region: "Germany (DE)",
              evidence_count: 489,
              confidence_level: "Medium"
            },
            {
              rank: 4,
              entry_region: "Switzerland (CH)",
              exit_region: "Sweden (SE)",
              evidence_count: 356,
              confidence_level: "Medium"
            },
            {
              rank: 5,
              entry_region: "Romania (RO)",
              exit_region: "Finland (FI)",
              evidence_count: 234,
              confidence_level: "Medium"
            },
            {
              rank: 6,
              entry_region: "Canada (CA)",
              exit_region: "Japan (JP)",
              evidence_count: 178,
              confidence_level: "Low"
            },
            {
              rank: 7,
              entry_region: "Australia (AU)",
              exit_region: "Singapore (SG)",
              evidence_count: 124,
              confidence_level: "Low"
            },
            {
              rank: 8,
              entry_region: "Brazil (BR)",
              exit_region: "Poland (PL)",
              evidence_count: 89,
              confidence_level: "Low"
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
        leads only and must be corroborated with additional evidence.
      </div>

      {loading ? (
        <div className="analysis-loading">
          <div className="loading-spinner"></div>
          <p>Loading analysis results...</p>
        </div>
      ) : error ? (
        <div className="analysis-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      ) : (
        <>
          {/* Hypotheses Table Section */}
          <section className="analysis-section">
            <div className="section-header">
              <h2>Correlation Hypotheses</h2>
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
                          <th className="th-entry">Entry Node Region</th>
                          <th className="th-exit">Exit Node Region</th>
                          <th className="th-evidence">Evidence Count</th>
                          <th className="th-confidence">Confidence Level</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisData.hypotheses.map((hypothesis, index) => (
                          <tr key={index} className={`hypothesis-row rank-${hypothesis.rank}`}>
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
                              </div>
                            </td>
                          </tr>
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
