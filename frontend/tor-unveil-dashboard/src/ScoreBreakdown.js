/**
 * ScoreBreakdown.js - Visual Score Component Analysis
 * 
 * Shows the detailed breakdown of path plausibility scores:
 * - Component contributions (uptime, bandwidth, role)
 * - Penalties applied
 * - Confidence level interpretation
 * - Probabilistic nature clearly indicated
 */

import React from "react";
import { AlertCircle, Info } from "lucide-react";
import "./ScoreBreakdown.css";

const ScoreBreakdown = ({ score = 0.75, components = {}, penalties = {} }) => {
  const confidenceLevel = (score) => {
    if (score >= 0.8) return { label: "HIGH", color: "#10b981", bg: "rgba(16, 185, 129, 0.1)" };
    if (score >= 0.5) return { label: "MEDIUM", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.1)" };
    return { label: "LOW", color: "#ef4444", bg: "rgba(239, 68, 68, 0.1)" };
  };

  const conf = confidenceLevel(score);

  // Default components if not provided
  const defaultComponents = {
    uptime: 0.85,
    bandwidth: 0.90,
    role: 0.75,
  };
  const finalComponents = Object.keys(defaultComponents).length === 0 ? defaultComponents : components;

  // Default penalties
  const defaultPenalties = {
    "AS Diversity": -0.30,
    "Country Diversity": -0.20,
  };
  const finalPenalties = Object.keys(defaultPenalties).length === 0 ? defaultPenalties : penalties;

  return (
    <div className="score-breakdown">
      {/* Main Score Display */}
      <div className="score-header">
        <div className="score-circle" style={{ background: conf.bg, borderColor: conf.color }}>
          <div className="score-label" style={{ color: conf.color }}>
            {conf.label}
          </div>
        </div>
        <div className="score-info">
          <p className="score-title">Path Plausibility Assessment</p>
          <p className="score-subtitle">Confidence level based on correlation analysis</p>
          <div className="confidence-badge" style={{ background: conf.bg, color: conf.color }}>
            {conf.label} Confidence
          </div>
        </div>
      </div>

      {/* Components Section */}
      <div className="breakdown-section">
        <h4 className="section-title">Score Components</h4>
        <div className="components-grid">
          {Object.entries(finalComponents).map(([name, value]) => (
            <div key={name} className="component-item">
              <div className="component-header">
                <span className="component-name">
                  {name.charAt(0).toUpperCase() + name.slice(1)}
                </span>
                <span className="component-value">{Math.round(value * 100)}%</span>
              </div>
              <div className="component-bar-bg">
                <div
                  className="component-bar"
                  style={{ width: `${value * 100}%` }}
                ></div>
              </div>
              <span className="component-weight">
                {name === "uptime" && "30% weight"}
                {name === "bandwidth" && "45% weight"}
                {name === "role" && "25% weight"}
              </span>
            </div>
          ))}
        </div>
        <p className="section-explanation">
          Components measure temporal overlap, network capacity, and relay role (entry/middle/exit).
        </p>
      </div>

      {/* Penalties Section */}
      {Object.keys(finalPenalties).length > 0 && (
        <div className="breakdown-section">
          <h4 className="section-title">Adjustments Applied</h4>
          <div className="penalties-list">
            {Object.entries(finalPenalties).map(([name, value]) => (
              <div key={name} className="penalty-item">
                <span className="penalty-name">{name}</span>
                <span className="penalty-value" style={{ color: "#ef4444" }}>
                  {value > 0 ? "+" : ""}{Math.round(value * 100)}%
                </span>
              </div>
            ))}
          </div>
          <p className="section-explanation">
            Penalties reduce score if relays share ASN or geographic location, reducing plausibility.
          </p>
        </div>
      )}

      {/* Interpretation Section */}
      <div className="breakdown-section interpretation">
        <div className="interpretation-header">
          <AlertCircle size={18} style={{ color: "#06b6d4" }} />
          <h4 className="section-title">What This Score Means</h4>
        </div>
        <div className="interpretation-content">
          <div className="interpretation-item">
            <span className="interpretation-label">Confidence:</span>
            <span className="interpretation-value">
              <strong>
                {conf.label === "HIGH"
                  ? "Strong correlation match"
                  : conf.label === "MEDIUM"
                  ? "Moderate correlation"
                  : "Weak correlation"}
              </strong>
            </span>
          </div>
          <div className="interpretation-item warning">
            <Info size={16} />
            <span className="interpretation-value">
              <strong>Important:</strong> High scores indicate plausibility, NOT proof of actual usage.
              Multiple paths may score highly for the same timestamp window.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoreBreakdown;
