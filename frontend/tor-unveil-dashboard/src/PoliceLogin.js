/**
 * PoliceLogin.js ??? DISCLAIMER & ACCESS PAGE
 * Tamil Nadu Police Cyber Crime Wing - TOR???Unveil
 *
 * Purpose: Display mandatory legal disclaimer before system access
 * NOT a real authentication system - backend has no auth
 *
 * This is a splash/disclaimer page that:
 * 1. Shows official government branding
 * 2. Displays legal disclaimer
 * 3. Requires acknowledgment before proceeding
 * 4. Collects officer identifier for audit trail (local only)
 */

import React, { useState } from "react";
import "./PoliceLogin.css";

function PoliceLogin({ onLoginSuccess }) {
  const [officerId, setOfficerId] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [error, setError] = useState("");

  const handleProceed = (e) => {
    e.preventDefault();
    setError("");

    if (!officerId.trim()) {
      setError("Please enter your Officer ID for audit purposes");
      return;
    }

    if (!acknowledged) {
      setError("Please acknowledge the disclaimer to proceed");
      return;
    }

    // Pass to parent - no real auth, just audit trail
    onLoginSuccess({
      loginId: officerId.trim().toUpperCase(),
      timestamp: new Date().toISOString(),
      acknowledged: true,
    });
  };

  return (
    <div className="login-container">
      <div className="login-panel">
        {/* Government Header */}
        <div className="login-header">
          <div className="login-emblem">
            <div className="emblem-box">
              <span className="emblem-text">TN</span>
              <span className="emblem-subtext">POLICE</span>
            </div>
          </div>
          <div className="login-title-block">
            <h1 className="login-title">TOR UNVEIL</h1>
            <p className="login-subtitle">
              Cyber Crime Wing, Tamil Nadu Police
            </p>
            <p className="login-dept">Government of Tamil Nadu</p>
          </div>
        </div>

        {/* System Description */}
        <div className="login-description">
          <h2>Forensic Intelligence System</h2>
          <p>
            TOR Unveil is a probabilistic analysis tool for correlating TOR
            network traffic with known relay infrastructure. This system
            provides investigative intelligence only and does not establish
            definitive attribution.
          </p>
        </div>

        {/* Mandatory Disclaimer */}
        <div className="login-disclaimer">
          <h3>ANDATORY DISCLAIMER</h3>
          <div className="disclaimer-content">
            <p>
              <strong>AUTHORIZED ACCESS ONLY</strong>
            </p>
            <p>
              This system is restricted to authorized Tamil Nadu Police
              personnel for official law enforcement purposes only. Unauthorized
              access is prohibited and punishable under the Information
              Technology Act, 2000.
            </p>

            <p>
              <strong>PROBABILISTIC ANALYSIS</strong>
            </p>
            <p>
              All analysis results are probabilistic hypotheses based on timing
              correlations and geographic inference. Results DO NOT establish:
            </p>
            <ul>
              <li>Definitive user identity</li>
              <li>Exact network paths</li>
              <li>Legal proof of attribution</li>
            </ul>

            <p>
              <strong>EVIDENTIARY LIMITATIONS</strong>
            </p>
            <p>
              Outputs from this system must be corroborated with independent
              forensic evidence before being presented in legal proceedings.
              Confidence assessments indicate statistical likelihood, not
              certainty.
            </p>

            <p>
              <strong>AUDIT TRAIL</strong>
            </p>
            <p>All system access and queries are logged for audit purposes.</p>
          </div>
        </div>

        {/* Access Form */}
        <form className="login-form" onSubmit={handleProceed}>
          <div className="form-group">
            <label htmlFor="officerId">Officer ID (for audit trail):</label>
            <input
              type="text"
              id="officerId"
              value={officerId}
              onChange={(e) => setOfficerId(e.target.value.toUpperCase())}
              placeholder="e.g., TN001, SI-CYBER-042"
              className="form-input"
              maxLength={20}
            />
          </div>

          <div className="form-checkbox">
            <input
              type="checkbox"
              id="acknowledge"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
            />
            <label htmlFor="acknowledge">
              I acknowledge that I am an authorized officer and understand that
              all analysis results are probabilistic and require independent
              corroboration before legal use.
            </label>
          </div>

          {error && <div className="form-error">{error}</div>}

          <button
            type="submit"
            className="btn-proceed"
            disabled={!officerId.trim() || !acknowledged}
          >
            Proceed to System
          </button>
        </form>

        {/* Footer */}
        <div className="login-footer">
          <p>
            Cyber Crime Helpline: <strong>1930</strong>
          </p>
          <p>
            © {new Date().getFullYear()} Tamil Nadu Police. All Rights Reserved.
          </p>
        </div>
      </div>
    </div>
  );
}

export default PoliceLogin;
