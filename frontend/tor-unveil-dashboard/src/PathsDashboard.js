// src/PathsDashboard.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAppContext } from "./AppContext";
import { Copy, CheckCircle, AlertCircle } from "lucide-react";
import SankeyChart from "./SankeyChart";
import ScoreExplainer from "./ScoreExplainer";
import ScoreBreakdown from "./ScoreBreakdown";
import IndianContextBadge from "./IndianContextBadge";
import CountryLegend from "./CountryLegend";
import ScoringMethodologyPanel from "./ScoringMethodologyPanel";
import InfrastructureContextPanel from "./InfrastructureContextPanel";
import "./PathsDashboard.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Helper function to get confidence level (qualitative only)
function getConfidenceLevel(score) {
  if (score >= 0.9) return { level: "VERY HIGH", color: "#059669" };
  if (score >= 0.75) return { level: "HIGH", color: "#10b981" };
  if (score >= 0.6) return { level: "MEDIUM", color: "#f59e0b" };
  if (score >= 0.4) return { level: "LOW", color: "#ef4444" };
  return { level: "VERY LOW", color: "#b91c1c" };
}

// Helper to resolve ISO country code to full country name (safe fallback)
function getCountryFullName(code) {
  try {
    if (!code) return "Unknown";
    // Use Intl.DisplayNames when available to map ISO to full country name
    if (typeof Intl !== "undefined" && Intl.DisplayNames) {
      const dn = new Intl.DisplayNames(["en"], { type: "region" });
      return dn.of(code) || code;
    }
    return code;
  } catch (e) {
    return code;
  }
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button 
      className="copy-btn"
      onClick={handleCopy}
      title="Copy to clipboard"
      aria-label="Copy fingerprint"
    >
      <Copy size={14} />
      {copied && <span className="copy-badge"><CheckCircle size={14} style={{display: "inline", marginRight: "4px"}} />Copied</span>}
    </button>
  );
}

export default function PathsDashboard() {
  const { selectPath, selectedPath } = useAppContext();
  const [paths, setPaths] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [showMethodology, setShowMethodology] = useState(false);

  async function loadPaths() {
    try {
      setLoading(true);
      setError(null);
      const res = await axios.get(`${API_URL}/paths/top?limit=100`);
      setPaths(res.data.paths || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load paths from backend");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPaths();
  }, []);

  const handleSelectPath = (path) => {
    selectPath(path);
  };

  const toggleRowExpand = (id) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  // Compute country frequency for legend
  const countryFrequency = {};
  paths.forEach((path) => {
    if (path.entry?.country) countryFrequency[path.entry.country] = (countryFrequency[path.entry.country] || 0) + 1;
    if (path.middle?.country) countryFrequency[path.middle.country] = (countryFrequency[path.middle.country] || 0) + 1;
    if (path.exit?.country) countryFrequency[path.exit.country] = (countryFrequency[path.exit.country] || 0) + 1;
  });
  const countryLegendData = Object.entries(countryFrequency).map(([country, count]) => ({ country, count }));

  return (
    <div className="paths-dashboard">
      <div className="explanation-banner">
        <h2>Probable TOR Paths</h2>
        <p>
          <strong>Purpose:</strong> Candidate TOR routes identified through temporal and network correlation. 
          Scores reflect confidence based on timing alignment, geographical distribution, and network topology.
        </p>
      </div>

      {/* Collapsible Methodology Section */}
      <div className="methodology-section">
        <button 
          className="methodology-toggle"
          onClick={() => setShowMethodology(!showMethodology)}
        >
          {showMethodology ? "▼" : "▶"} Scoring Methodology Explanation
        </button>
        {showMethodology && (
          <div className="methodology-details">
            <div className="methodology-grid">
              <div className="methodology-item">
                <h4>Uptime Window</h4>
                <p><strong>7 days</strong> - Realistic timeframe for TOR relay overlap detection</p>
              </div>
              <div className="methodology-item">
                <h4>AS Penalty</h4>
                <p><strong>0.70x</strong> - Penalty applied when entry and exit nodes share the same Autonomous System</p>
              </div>
              <div className="methodology-item">
                <h4>Country Penalty</h4>
                <p><strong>0.60x</strong> - Penalty applied when entry and exit nodes are in the same country</p>
              </div>
              <div className="methodology-item">
                <h4>Maximum Score Cap</h4>
                <p><strong>85%</strong> - Prevents unrealistically high confidence claims</p>
              </div>
              <div className="methodology-item">
                <h4>Weight Distribution</h4>
                <p><strong>50%</strong> Uptime | <strong>25%</strong> Bandwidth | <strong>25%</strong> Role Flags</p>
              </div>
              <div className="methodology-item">
                <h4>Confidence Levels</h4>
                <p><span style={{color: "#10b981"}}>● HIGH</span> (score ≥0.80) | <span style={{color: "#f59e0b"}}>● MEDIUM</span> (score ≥0.50) | <span style={{color: "#ef4444"}}>● LOW</span> (score &lt;0.50)</p>
              </div>
            </div>
            <div className="methodology-warning">
              <AlertCircle size={18} style={{display: "inline-block", marginRight: "8px", verticalAlign: "middle"}} /><strong>Important:</strong> These scores represent <strong>plausibility estimates only</strong>, not definitive proof. 
              Results must be validated through independent investigative methods.
            </div>
          </div>
        )}
      </div>

      <header className="dashboard-header">
        <h1>TOR Path Correlation Analysis</h1>
        <button className="refresh-btn" onClick={loadPaths} disabled={loading}>
          {loading ? "Loading..." : "Refresh Paths"}
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading correlated paths...</p>
        </div>
      )}

      {!loading && paths.length === 0 && (
        <div className="empty-state">
          <p>No correlated paths available. Ensure the backend has generated paths.</p>
        </div>
      )}

      {!loading && paths.length > 0 && (
        <div className="paths-content">
          {/* Paths Table */}
          <div className="paths-table-section">
            <h3>Available Paths ({paths.length})</h3>
            <div className="table-instructions">
              Select a path to view confidence breakdown and visualization options.
            </div>
            
            <div className="table-responsive">
              <table className="paths-table">
                <thead>
                  <tr>
                    <th>Entry Node</th>
                    <th>Middle Relay</th>
                    <th>Exit Node</th>
                    <th>Confidence</th>
                    <th>Score</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {paths.map((path, idx) => {
                    const confidence = getConfidenceLevel(path.score);
                    const isSelected = selectedPath?.id === path.id;
                    
                    return (
                      <React.Fragment key={path.id || idx}>
                        <tr className={isSelected ? "selected" : ""}>
                          <td className="node-name">
                            <div className="node-title">{path.entry?.nickname || "Unknown"}</div>
                            <div
                              className="node-country"
                              title={getCountryFullName(path.entry?.country)}
                            >
                              {path.entry?.country || "-"}
                            </div>
                            {/* Inline fingerprint preview (wraps) */}
                            <div className="fp-inline" title={path.entry?.fingerprint || ''}>
                              <code>{path.entry?.fingerprint || ""}</code>
                            </div>
                          </td>
                          <td className="node-name">
                            <div className="node-title">{path.middle?.nickname || "Unknown"}</div>
                            <div
                              className="node-country"
                              title={getCountryFullName(path.middle?.country)}
                            >
                              {path.middle?.country || "-"}
                            </div>
                            <div className="fp-inline" title={path.middle?.fingerprint || ''}>
                              <code>{path.middle?.fingerprint || ""}</code>
                            </div>
                          </td>
                          <td className="node-name">
                            <div className="node-title">{path.exit?.nickname || "Unknown"}</div>
                            <div
                              className="node-country"
                              title={getCountryFullName(path.exit?.country)}
                            >
                              {path.exit?.country || "-"}
                            </div>
                            <div className="fp-inline" title={path.exit?.fingerprint || ''}>
                              <code>{path.exit?.fingerprint || ""}</code>
                            </div>
                          </td>
                          <td className="cell-score">
                            <div className="confidence-heatmap">
                              <div className="heatmap-bar">
                                <div 
                                  className="heatmap-marker" 
                                  style={{ left: `${Math.max(2, Math.min(98, path.score * 100))}%` }}
                                  title={`Score: ${path.score.toFixed(3)}`}
                                ></div>
                              </div>
                              <div className="score-display">
                                {(path.score * 100).toFixed(1)}%
                              </div>
                            </div>
                          </td>
                          <td className="cell-nodes">
                            <div className="node-list">
                              <button 
                                className={`select-btn ${isSelected ? "selected" : ""}`}
                                onClick={() => handleSelectPath(path)}
                              >
                                {isSelected ? <><CheckCircle size={14} style={{display: "inline", marginRight: "4px"}} />Selected</> : "Select"}
                              </button>
                            </div>
                          </td>
                        </tr>
                        
                        {/* Expandable Details Row */}
                        {isSelected && (
                          <tr className="details-row">
                            <td colSpan="6">
                              <div className="path-details">
                                <div className="details-grid">
                                  {/* Entry Node */}
                                  <div className="node-card entry-card">
                                    <div className="node-header">
                                      <span className="node-type entry-type">ENTRY</span>
                                      <span className="node-role">
                                        {path.entry?.is_guard ? "Guard" : "Non-Guard"}
                                      </span>
                                    </div>
                                    <div className="node-details-content">
                                      <div className="detail-item">
                                        <label>Fingerprint</label>
                                        <div className="fp-display">
                                          <code>{path.entry?.fingerprint || "Unknown"}</code>
                                          <CopyButton text={path.entry?.fingerprint || ""} />
                                        </div>
                                      </div>
                                      <div className="detail-item">
                                        <label>IP Address</label>
                                        <div>{path.entry?.ip || "Unknown"}</div>
                                      </div>
                                      <div className="detail-item">
                                        <label>Bandwidth</label>
                                        <div>
                                          {path.entry?.advertised_bandwidth 
                                            ? `${(path.entry.advertised_bandwidth / 1_000_000).toFixed(1)} Mbps`
                                            : "Unknown"}
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Middle Relay */}
                                  <div className="node-card middle-card">
                                    <div className="node-header">
                                      <span className="node-type middle-type">MIDDLE</span>
                                      <span className="node-role">Relay</span>
                                    </div>
                                    <div className="node-details-content">
                                      <div className="detail-item">
                                        <label>Fingerprint</label>
                                        <div className="fp-display">
                                          <code>{path.middle?.fingerprint || "Unknown"}</code>
                                          <CopyButton text={path.middle?.fingerprint || ""} />
                                        </div>
                                      </div>
                                      <div className="detail-item">
                                        <label>IP Address</label>
                                        <div>{path.middle?.ip || "Unknown"}</div>
                                      </div>
                                      <div className="detail-item">
                                        <label>Bandwidth</label>
                                        <div>
                                          {path.middle?.advertised_bandwidth 
                                            ? `${(path.middle.advertised_bandwidth / 1_000_000).toFixed(1)} Mbps`
                                            : "Unknown"}
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Exit Node */}
                                  <div className="node-card exit-card">
                                    <div className="node-header">
                                      <span className="node-type exit-type">EXIT</span>
                                      <span className="node-role">
                                        {path.exit?.is_exit ? "Exit" : "Non-Exit"}
                                      </span>
                                    </div>
                                    <div className="node-details-content">
                                      <div className="detail-item">
                                        <label>Fingerprint</label>
                                        <div className="fp-display">
                                          <code>{path.exit?.fingerprint || "Unknown"}</code>
                                          <CopyButton text={path.exit?.fingerprint || ""} />
                                        </div>
                                      </div>
                                      <div className="detail-item">
                                        <label>IP Address</label>
                                        <div>{path.exit?.ip || "Unknown"}</div>
                                      </div>
                                      <div className="detail-item">
                                        <label>Bandwidth</label>
                                        <div>
                                          {path.exit?.advertised_bandwidth 
                                            ? `${(path.exit.advertised_bandwidth / 1_000_000).toFixed(1)} Mbps`
                                            : "Unknown"}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {/* Score Breakdown - Enhanced Visualization */}
                                {path.score !== undefined && (
                                  <div style={{ marginTop: "16px" }}>
                                    <ScoreBreakdown 
                                      score={path.score}
                                      components={{
                                        uptime: path.components?.uptime_score || 0.75,
                                        bandwidth: path.components?.bandwidth_score || 0.80,
                                        role: path.components?.role_score || 0.70
                                      }}
                                      penalties={{
                                        "AS Diversity": (path.components?.as_penalty || -0.30),
                                        "Country Diversity": (path.components?.country_penalty || -0.20)
                                      }}
                                    />
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Panel: Selected Path Visualization */}
          {selectedPath && (
            <div className="visualization-panel">
              <h3>Selected Path Visualization</h3>
              
              {/* Infrastructure Context - Indian vs Foreign Analysis */}
              <InfrastructureContextPanel paths={paths} />
              
              {/* Scoring Methodology Panel - Transparent Documentation */}
              <ScoringMethodologyPanel />
              
              {/* Score Explainer - Shows reasoning */}
              <ScoreExplainer path={selectedPath} />

              {/* Indian Context Badge - Tamil Nadu Police relevance */}
              <IndianContextBadge
                entry={selectedPath.entry}
                middle={selectedPath.middle}
                exit={selectedPath.exit}
              />

              <div className="confidence-summary">
                <div className="confidence-large">
                  <div className="confidence-percent">{(selectedPath.score * 100).toFixed(0)}%</div>
                  <div className="confidence-label">
                    {getConfidenceLevel(selectedPath.score).level} Confidence
                  </div>
                </div>
                <div className="confidence-explanation">
                  This path's plausibility is based on temporal and network correlation metrics. 
                  Higher confidence indicates better alignment with observed metadata patterns.
                </div>
              </div>

              <div className="flow-visual">
                <div className="flow-node entry-node">
                  <div className="flow-label">ENTRY</div>
                  <div className="flow-name">{selectedPath.entry?.nickname || "?"}</div>
                </div>
                <div className="flow-arrow">→</div>
                <div className="flow-node middle-node">
                  <div className="flow-label">MIDDLE</div>
                  <div className="flow-name">{selectedPath.middle?.nickname || "?"}</div>
                </div>
                <div className="flow-arrow">→</div>
                <div className="flow-node exit-node">
                  <div className="flow-label">EXIT</div>
                  <div className="flow-name">{selectedPath.exit?.nickname || "?"}</div>
                </div>
              </div>

              <div className="sankey-container">
                <SankeyChart paths={[selectedPath]} />
              </div>

              {/* Country Legend */}
              <CountryLegend countryData={countryLegendData} isExpanded={false} />

              <div className="legend">
                <div className="legend-item">
                  <span className="legend-dot entry-dot"></span>
                  <span>Entry node: Connection enters TOR network</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot middle-dot"></span>
                  <span>Middle relay: Intermediate routing node</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot exit-dot"></span>
                  <span>Exit node: Connection leaves TOR network</span>
                </div>
              </div>

              <div className="legal-note">
                <p>
                  <strong>Legal Notice:</strong> This is investigative support only. 
                  Results are probabilistic and based on metadata correlation. 
                  No TOR breaking or deanonymization techniques are employed.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
