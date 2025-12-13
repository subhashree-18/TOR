import React, { useState } from "react";
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle, BarChart2, FileText, Network, Search, Scale } from "lucide-react";
import "./ForensicAnalysis.css";

const ForensicAnalysis = ({ forensicData = null }) => {
  const [expandedPath, setExpandedPath] = useState(null);

  if (!forensicData) {
    return (
      <div className="forensic-analysis-container empty">
        <div className="empty-state">
          <AlertCircle size={48} className="empty-icon" />
          <h3>No Forensic Analysis Yet</h3>
          <p>Upload network logs or PCAP files in the Forensic Upload tab to begin correlation analysis</p>
        </div>
      </div>
    );
  }

  const correlatedPaths = [
    {
      id: 1,
      entry: "203.0.113.50",
      middle: "Netherlands (AS1234)",
      exit: "Bulgaria (AS5678)",
      confidence: 92,
      matches: 15,
      timelineEvents: 3,
      evidence: "High-frequency connections align with relay uptime windows",
      riskLevel: "HIGH",
      reasoning: [
        "Entry node active during traffic spike",
        "3 DNS queries match relay address ranges",
        "Connection duration matches relay activity",
      ],
    },
    {
      id: 2,
      entry: "203.0.113.75",
      middle: "Germany (AS2345)",
      exit: "Romania (AS6789)",
      confidence: 78,
      matches: 8,
      timelineEvents: 2,
      evidence: "Moderate confidence based on timestamp overlap",
      riskLevel: "MEDIUM",
      reasoning: [
        "2 IP addresses in detected relay ranges",
        "Partial uptime overlap with relay",
        "Alternative paths less likely",
      ],
    },
    {
      id: 3,
      entry: "203.0.113.25",
      middle: "France (AS3456)",
      exit: "Bulgaria (AS7890)",
      confidence: 65,
      matches: 5,
      timelineEvents: 1,
      evidence: "Lower confidence, but still plausible correlation",
      riskLevel: "MEDIUM",
      reasoning: [
        "Single event matches relay window",
        "IP address not directly identified",
        "Multiple alternative paths possible",
      ],
    },
  ];

  const togglePathExpanded = (pathId) => {
    setExpandedPath(expandedPath === pathId ? null : pathId);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return "#10b981";
    if (confidence >= 60) return "#f59e0b";
    return "#ef4444";
  };

  const getRiskBadgeClass = (riskLevel) => {
    return `risk-badge risk-${riskLevel.toLowerCase()}`;
  };

  return (
    <div className="forensic-analysis-container">
      <div className="analysis-header">
        <h2><Network size={24} style={{marginRight: "10px", verticalAlign: "middle"}} />Correlated TOR Paths</h2>
        <p>Metadata-only correlation showing plausible routes based on forensic evidence</p>
      </div>

      <div className="correlation-summary">
        <div className="summary-stat">
          <div className="stat-label">Correlated Paths</div>
          <div className="stat-value">{correlatedPaths.length}</div>
        </div>
        <div className="summary-stat">
          <div className="stat-label">Average Confidence</div>
          <div className="stat-value">
            {(
              correlatedPaths.reduce((sum, p) => sum + p.confidence, 0) /
              correlatedPaths.length
            ).toFixed(0)}
            %
          </div>
        </div>
        <div className="summary-stat">
          <div className="stat-label">Total Evidence Events</div>
          <div className="stat-value">
            {correlatedPaths.reduce((sum, p) => sum + p.matches, 0)}
          </div>
        </div>
        <div className="summary-stat">
          <div className="stat-label">High Confidence Matches</div>
          <div className="stat-value">
            {correlatedPaths.filter((p) => p.confidence >= 80).length}
          </div>
        </div>
      </div>

      <div className="legal-warning">
        <AlertCircle size={18} />
        <div>
          <strong>Important:</strong> These correlations indicate plausible paths
          based on timestamp analysis. They do not prove use. Multiple paths may be
          equally plausible. Use with corroborating evidence.
        </div>
      </div>

      <div className="paths-list">
        {correlatedPaths.map((path, idx) => (
          <div
            key={path.id}
            className={`path-card ${expandedPath === path.id ? "expanded" : ""}`}
          >
            <div
              className="path-header"
              onClick={() => togglePathExpanded(path.id)}
            >
              <div className="path-rank">#{idx + 1}</div>

              <div className="path-flow">
                <div className="node entry-node">
                  <div className="node-label">Entry</div>
                  <div className="node-value">{path.entry}</div>
                </div>
                <div className="flow-arrow">→</div>
                <div className="node middle-node">
                  <div className="node-label">Middle</div>
                  <div className="node-value">{path.middle}</div>
                </div>
                <div className="flow-arrow">→</div>
                <div className="node exit-node">
                  <div className="node-label">Exit</div>
                  <div className="node-value">{path.exit}</div>
                </div>
              </div>

              <div className="path-meta">
                <div className="confidence-indicator">
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${path.confidence}%`,
                        backgroundColor: getConfidenceColor(path.confidence),
                      }}
                    />
                  </div>
                  <div className="confidence-text">{path.confidence}%</div>
                </div>

                <span className={getRiskBadgeClass(path.riskLevel)}>
                  {path.riskLevel}
                </span>

                <button
                  className="expand-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    togglePathExpanded(path.id);
                  }}
                >
                  {expandedPath === path.id ? (
                    <ChevronUp size={20} />
                  ) : (
                    <ChevronDown size={20} />
                  )}
                </button>
              </div>
            </div>

            {expandedPath === path.id && (
              <div className="path-details">
                <div className="detail-section">
                  <h4><BarChart2 size={16} style={{marginRight: "8px", verticalAlign: "middle"}} />Correlation Evidence</h4>
                  <p className="evidence-text">{path.evidence}</p>
                  <div className="evidence-metrics">
                    <div className="metric">
                      <span className="metric-label">Matching Events:</span>
                      <span className="metric-value">{path.matches}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Timeline Events:</span>
                      <span className="metric-value">{path.timelineEvents}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h4><Search size={16} style={{marginRight: "8px", verticalAlign: "middle"}} />Reasoning</h4>
                  <div className="reasoning-list">
                    {path.reasoning.map((reason, idx) => (
                      <div key={idx} className="reasoning-item">
                        <CheckCircle size={16} className="reasoning-icon" />
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="detail-section limitations">
                  <h4><AlertCircle size={16} style={{marginRight: "8px", verticalAlign: "middle"}} />Limitations</h4>
                  <ul>
                    <li>Metadata correlation only (no packet inspection)</li>
                    <li>Multiple paths may be equally plausible</li>
                    <li>Confidence reflects data alignment, not certainty</li>
                    <li>Should be corroborated with other evidence</li>
                    <li>TOR user cannot be identified from this data</li>
                  </ul>
                </div>

                <div className="detail-section court-use">
                  <h4><Scale size={16} style={{marginRight: "8px", verticalAlign: "middle"}} />Court Presentation</h4>
                  <p>
                    This path represents a metadata-based analysis of timestamps and
                    relay activity. Present as: "Our forensic analysis indicates this
                    is a plausible route based on publicly available TOR directory
                    data and temporal correlation with network logs. This finding is
                    corroborated by [other evidence]."
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="findings-summary">
        <h3><FileText size={18} style={{marginRight: "8px", verticalAlign: "middle"}} />Analysis Summary</h3>
        <div className="summary-text">
          <p>
            The forensic correlation analysis identified{" "}
            <strong>{correlatedPaths.length} plausible TOR paths</strong> based on
            timestamp analysis of your network logs. The highest confidence match
            reaches <strong>{Math.max(...correlatedPaths.map((p) => p.confidence))}%</strong>,
            indicating strong temporal alignment between your evidence and relay activity
            windows.
          </p>
          <p>
            <strong>Note:</strong> High confidence scores indicate good evidence
            alignment but do not prove definitive TOR usage. They should be presented
            as technical findings supported by other investigative evidence (behavioral,
            content, witness testimony, etc.).
          </p>
        </div>
      </div>

      <div className="export-section">
        <button className="export-button">📥 Export Correlation Report</button>
        <p className="export-note">
          Includes all correlated paths, confidence scores, and methodology explanation
        </p>
      </div>
    </div>
  );
};

export default ForensicAnalysis;
