/**
 * Score Explainer Component
 * Shows detailed breakdown of confidence score calculation
 * Makes scoring logic transparent and audit-trail friendly
 */

import React from "react";
import { ChevronDown, ChevronUp, AlertCircle, TrendingUp } from "lucide-react";
import "./ScoreExplainer.css";

export default function ScoreExplainer({ path, expanded = false, onToggle }) {
  const [isExpanded, setIsExpanded] = React.useState(expanded);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    if (onToggle) onToggle(!isExpanded);
  };

  if (!path) {
    return (
      <div className="score-explainer-empty">
        <AlertCircle size={16} /> No path selected for explanation
      </div>
    );
  }

  const score = path.score || 0;
  
  // Determine confidence level
  let confidenceLevel, confidenceColor;
  if (score >= 0.8) {
    confidenceLevel = "HIGH";
    confidenceColor = "#10b981";
  } else if (score >= 0.5) {
    confidenceLevel = "MEDIUM";
    confidenceColor = "#f59e0b";
  } else {
    confidenceLevel = "LOW";
    confidenceColor = "#ef4444";
  }

  // Score components (from backend, or fallback values)
  const components = path.components || {
    uptime_score: 0.75,
    bandwidth_score: 0.85,
    role_score: 0.90,
    as_penalty: 0.70,
    country_penalty: 0.60,
  };

  // Calculate weights (these match backend scoring logic)
  const weights = {
    uptime: 0.30,
    bandwidth: 0.45,
    role: 0.25,
  };

  // Primary factor (highest weight contribution)
  const getTopFactor = () => {
    const factors = [
      { name: "Bandwidth", value: components.bandwidth_score * weights.bandwidth, component: "bandwidth" },
      { name: "Uptime", value: components.uptime_score * weights.uptime, component: "uptime" },
      { name: "Role", value: components.role_score * weights.role, component: "role" },
    ];
    return factors.reduce((a, b) => (a.value > b.value ? a : b));
  };

  // Secondary factor (second highest)
  const getSecondaryFactor = () => {
    const factors = [
      { name: "Bandwidth", value: components.bandwidth_score * weights.bandwidth, component: "bandwidth" },
      { name: "Uptime", value: components.uptime_score * weights.uptime, component: "uptime" },
      { name: "Role", value: components.role_score * weights.role, component: "role" },
    ];
    factors.sort((a, b) => b.value - a.value);
    return factors[1];
  };

  const topFactor = getTopFactor();
  const secondaryFactor = getSecondaryFactor();

  // Penalties applied
  const penalties = [];
  if (components.as_penalty < 1.0) {
    penalties.push({
      name: "Same Autonomous System (AS)",
      penalty: components.as_penalty,
      reduction: ((1 - components.as_penalty) * 100).toFixed(0),
    });
  }
  if (components.country_penalty < 1.0) {
    penalties.push({
      name: "Same Country",
      penalty: components.country_penalty,
      reduction: ((1 - components.country_penalty) * 100).toFixed(0),
    });
  }

  return (
    <div className="score-explainer">
      <button 
        className="explainer-header"
        onClick={toggleExpanded}
      >
        <div className="explainer-title">
          <TrendingUp size={18} />
          <span>Why This Path?</span>
        </div>
        <div className="score-display">
          <span 
            className="score-badge" 
            style={{ borderColor: confidenceColor }}
          >
            <span className="confidence-label" style={{ color: confidenceColor }}>
              {confidenceLevel} Confidence
            </span>
          </span>
          {isExpanded ? (
            <ChevronUp size={20} />
          ) : (
            <ChevronDown size={20} />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="explainer-content">
          {/* Summary */}
          <div className="summary-section">
            <h4>Assessment Summary</h4>
            <p className="summary-text">
              This TOR path has been correlated with <strong>{confidenceLevel}</strong> confidence 
              based on timing alignment, network topology, and relay characteristics. The score reflects 
              the probability that these three relays were used together to route a single TOR connection.
            </p>
          </div>

          {/* Primary Factor */}
          <div className="factor-section primary">
            <div className="factor-header">
              <span className="factor-label">PRIMARY FACTOR</span>
              <span className="factor-name">{topFactor.name}</span>
            </div>
            <div className="factor-explanation">
              <p>
                {topFactor.component === "bandwidth" && (
                  <>
                    The exit relay has <strong>high bandwidth capacity</strong> ({(components.bandwidth_score * 100).toFixed(0)}%), 
                    making it more likely to be selected for traffic routing. High-capacity exits are favored by TOR clients.
                  </>
                )}
                {topFactor.component === "uptime" && (
                  <>
                    The relays show <strong>strong uptime overlap</strong> ({(components.uptime_score * 100).toFixed(0)}%), 
                    indicating they were active during the critical observation window. Stable relays are preferred by TOR.
                  </>
                )}
                {topFactor.component === "role" && (
                  <>
                    The relays have <strong>stable operational roles</strong> ({(components.role_score * 100).toFixed(0)}%), 
                    with valid flags and consistent performance. Role stability increases likelihood of correlation.
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Secondary Factor */}
          <div className="factor-section secondary">
            <div className="factor-header">
              <span className="factor-label">SECONDARY FACTOR</span>
              <span className="factor-name">{secondaryFactor.name}</span>
            </div>
            <div className="factor-explanation">
              <p>
                Contributes {(secondaryFactor.value * 100).toFixed(0)}% to final confidence score.
              </p>
            </div>
          </div>

          {/* Penalties */}
          {penalties.length > 0 && (
            <div className="penalties-section">
              <div className="section-header">PENALTIES APPLIED</div>
              <div className="penalties-list">
                {penalties.map((penalty, idx) => (
                  <div key={idx} className="penalty-item">
                    <div className="penalty-icon">—</div>
                    <div className="penalty-info">
                      <div className="penalty-name">{penalty.name}</div>
                      <div className="penalty-detail">
                        Reduces score by {penalty.reduction}%
                        <span className="penalty-value">{(penalty.penalty * 100).toFixed(0)}x</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="penalties-explanation">
                Penalties reduce confidence when relays share infrastructure (AS) or geography. This guards against 
                false correlations from poorly isolated relay clusters.
              </p>
            </div>
          )}

          {/* Limitations */}
          <div className="limitations-section">
            <div className="section-header">LIMITATIONS & CAVEATS</div>
            <ul className="limitations-list">
              <li>Score reflects <strong>correlation probability</strong>, not certainty</li>
              <li>Based on <strong>metadata analysis only</strong> (no payload inspection)</li>
              <li>Subject to <strong>TOR relay database accuracy</strong></li>
              <li>Does not indicate <strong>actual user identity</strong></li>
              <li>Used for <strong>investigative leads only</strong></li>
            </ul>
          </div>

          {/* Score Methodology */}
          <div className="methodology-section">
            <div className="section-header">SCORING FORMULA</div>
            <code className="formula">
              final_score = (uptime × 0.30 + bandwidth × 0.45 + role × 0.25) × as_penalty × country_penalty
            </code>
            <p className="formula-explanation">
              The score compounds multiple factors: uptime overlap (30%), relay bandwidth capacity (45%), 
              and role stability (25%). Infrastructure and geographic penalties reduce overconfident scores.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
