/**
 * ScoringMethodologyPanel.js - Transparent Scoring Documentation
 * Displays the scoring methodology and backend metadata for police review
 */

import React, { useState } from "react";
import { ChevronDown, AlertCircle, BookOpen } from "lucide-react";
import "./ScoringMethodologyPanel.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function ScoringMethodologyPanel() {
  const [expanded, setExpanded] = useState(false);
  const [methodology, setMethodology] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMethodology = async () => {
    if (methodology) {
      setExpanded(!expanded);
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/scoring-methodology`);
      if (!res.ok) throw new Error("Failed to fetch methodology");
      const data = await res.json();
      setMethodology(data);
      setExpanded(true);
    } catch (err) {
      console.error("Error fetching methodology:", err);
      setError("Could not load methodology documentation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scoring-methodology-panel">
      <button
        className="methodology-toggle-btn"
        onClick={fetchMethodology}
        disabled={loading}
      >
        <BookOpen size={16} />
        <span>Scoring Methodology</span>
        <ChevronDown
          size={18}
          className={`chevron ${expanded ? "expanded" : ""}`}
        />
      </button>

      {expanded && (
        <div className="methodology-content">
          {error && (
            <div className="error-banner">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          {methodology && (
            <>
              {/* Header */}
              <div className="methodology-header">
                <h3>{methodology.title}</h3>
                <p className="version">v{methodology.version}</p>
                <div className="disclaimer">
                  <AlertCircle size={16} />
                  <strong>Important:</strong> {methodology.important_disclaimer}
                </div>
              </div>

              {/* Score Range */}
              <div className="section">
                <h4>Score Range</h4>
                <div className="score-range-table">
                  <div className="range-row">
                    <div className="range-label">Minimum Score:</div>
                    <div className="range-value">{methodology.score_range.minimum}</div>
                  </div>
                  <div className="range-row">
                    <div className="range-label">Maximum Score:</div>
                    <div className="range-value">{methodology.score_range.maximum}</div>
                  </div>
                  <div className="range-reason">{methodology.score_range.reason}</div>
                </div>
              </div>

              {/* Confidence Levels */}
              <div className="section">
                <h4>Confidence Level Ranges</h4>
                <div className="confidence-grid">
                  {Object.entries(methodology.confidence_levels).map(([level, data]) => (
                    <div key={level} className={`confidence-card ${level.toLowerCase()}`}>
                      <div className="confidence-name">{level}</div>
                      <div className="confidence-range">
                        {data.range[0]} – {data.range[1]}
                      </div>
                      <div className="confidence-interpretation">
                        {data.interpretation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Score Components */}
              <div className="section">
                <h4>Score Components</h4>
                <div className="components-table">
                  {Object.entries(methodology.score_components).map(([key, component]) => {
                    if (typeof component !== "object" || !component.weight) return null;
                    return (
                      <div key={key} className="component-card">
                        <div className="component-header">
                          <div className="component-name">{key}</div>
                          <div className="component-weight">
                            Weight: {(component.weight * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div className="component-factors">
                          {component.factors.map((factor, idx) => (
                            <div key={idx} className="factor">• {factor}</div>
                          ))}
                        </div>
                        {component.note && (
                          <div className="component-note">{component.note}</div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Penalties */}
                <div className="penalties-section">
                  <h5>Applied Penalties</h5>
                  <div className="penalties-list">
                    {Object.entries(methodology.score_components).map(([key, component]) => {
                      if (!component.applied_when) return null;
                      return (
                        <div key={key} className="penalty-item">
                          <div className="penalty-name">{component.applied_when}</div>
                          <div className="penalty-value">
                            Multiplier: {component.value}
                            <span className="penalty-reduction">
                              (−{((1 - component.value) * 100).toFixed(0)}%)
                            </span>
                          </div>
                          <div className="penalty-reason">{component.reason}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Calculation */}
              <div className="section">
                <h4>Scoring Formula</h4>
                <div className="formula-box">
                  <code>{methodology.calculation.formula}</code>
                </div>
                <div className="formula-details">
                  <p><strong>Post-processing:</strong> {methodology.calculation.post_processing}</p>
                  <p><strong>Unit:</strong> {methodology.calculation.unit}</p>
                </div>
              </div>

              {/* Limitations */}
              <div className="section limitations">
                <h4>Limitations & Disclaimers</h4>
                <div className="limitations-list">
                  {methodology.limitations &&
                    Object.entries(methodology.limitations).map(([key, value]) => (
                      <div key={key} className="limitation-item">
                        <strong>{key}:</strong> {value}
                      </div>
                    ))}
                </div>
              </div>

              {/* Explainability */}
              <div className="section explainability">
                <h4>Transparency & Auditability</h4>
                <div className="explainability-list">
                  {methodology.explainability &&
                    Object.entries(methodology.explainability).map(([key, value]) => (
                      <div key={key} className="explainability-item">
                        <strong>{key}:</strong> {value}
                      </div>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
