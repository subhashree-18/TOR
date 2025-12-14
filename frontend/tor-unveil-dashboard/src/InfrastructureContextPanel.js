/**
 * InfrastructureContextPanel.js - Indian vs Foreign Infrastructure Analysis
 * 
 * Highlights the geographic split between Indian and foreign TOR infrastructure,
 * tailored for Chennai Cyber Wing investigations
 */

import React, { useMemo } from "react";
import { Globe, MapPin, AlertTriangle, TrendingUp } from "lucide-react";
import "./InfrastructureContextPanel.css";

const INDIAN_COUNTRIES = ["IN"];
const HIGH_RISK_COUNTRIES = ["BG", "CN", "KP", "IR", "RU", "RO", "PK", "BD"];

const CYBERCRIME_TAGS = {
  "Financial Fraud": "phishing, UPI scams, OTP theft, card fraud",
  "Anonymous Threats": "extortion, cyberstalking, blackmail",
  "Ransomware Ops": "infrastructure coordination, C2 servers",
  "Data Theft": "stolen credentials, confidential data exfiltration",
  "Cross-Border": "foreign money mule networks, coordination",
};

const InfrastructureContextPanel = ({ paths = [] }) => {
  const analysis = useMemo(() => {
    if (!paths || paths.length === 0) {
      return {
        indianEntries: 0,
        indianMiddles: 0,
        indianExits: 0,
        highRiskExits: 0,
        hybridPaths: 0,
        totalPaths: 0,
      };
    }

    let indianEntries = 0;
    let indianMiddles = 0;
    let indianExits = 0;
    let highRiskExits = 0;
    let hybridPaths = 0;

    paths.forEach((path) => {
      if (path.entry?.country === "IN") indianEntries++;
      if (path.middle?.country === "IN") indianMiddles++;
      if (path.exit?.country === "IN") indianExits++;
      if (HIGH_RISK_COUNTRIES.includes(path.exit?.country)) highRiskExits++;
      
      // Hybrid: Indian entry/middle + Foreign high-risk exit
      const hasIndian = [path.entry?.country, path.middle?.country, path.exit?.country].includes("IN");
      const hasRisk = HIGH_RISK_COUNTRIES.includes(path.exit?.country);
      if (hasIndian && hasRisk) hybridPaths++;
    });

    return {
      indianEntries,
      indianMiddles,
      indianExits,
      highRiskExits,
      hybridPaths,
      totalPaths: paths.length,
    };
  }, [paths]);

  const indianPercentage =
    analysis.totalPaths > 0
      ? Math.round(
          ((analysis.indianEntries +
            analysis.indianMiddles +
            analysis.indianExits) /
            (analysis.totalPaths * 3)) *
            100
        )
      : 0;

  const riskPercentage =
    analysis.totalPaths > 0 ? Math.round((analysis.highRiskExits / analysis.totalPaths) * 100) : 0;

  return (
    <div className="infrastructure-context">
      {/* Header */}
      <div className="context-header">
        <MapPin size={20} className="header-icon" />
        <h3>Infrastructure Analysis</h3>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card indian">
          <div className="stat-label">Indian Nodes</div>
          <div className="stat-value">{analysis.indianEntries + analysis.indianMiddles + analysis.indianExits}</div>
          <div className="stat-percent">{indianPercentage}% of relays</div>
        </div>

        <div className="stat-card risk">
          <div className="stat-label">High-Risk Exits</div>
          <div className="stat-value">{analysis.highRiskExits}</div>
          <div className="stat-percent">{riskPercentage}% of paths</div>
        </div>

        <div className="stat-card hybrid">
          <div className="stat-label">India→Risk Patterns</div>
          <div className="stat-value">{analysis.hybridPaths}</div>
          <div className="stat-percent">Fraud indicator</div>
        </div>
      </div>

      {/* Infrastructure Breakdown */}
      <div className="breakdown">
        <h4>Geographic Distribution</h4>
        <div className="breakdown-items">
          <div className="breakdown-item">
            <span className="item-label">Indian Entry Nodes</span>
            <span className="item-badge indian-badge">{analysis.indianEntries}</span>
          </div>
          <div className="breakdown-item">
            <span className="item-label">Indian Middle Relays</span>
            <span className="item-badge indian-badge">{analysis.indianMiddles}</span>
          </div>
          <div className="breakdown-item">
            <span className="item-label">Indian Exit Nodes</span>
            <span className="item-badge indian-badge">{analysis.indianExits}</span>
          </div>
          <div className="breakdown-item">
            <span className="item-label">Foreign High-Risk Exits</span>
            <span className="item-badge risk-badge">{analysis.highRiskExits}</span>
          </div>
        </div>
      </div>

      {/* Investigative Context */}
      <div className="investigation-context">
        <div className="context-alert">
          <AlertTriangle size={18} />
          <div>
            <h5>Investigation Patterns</h5>
            <p>
              India→Foreign-Risk routing is commonly associated with financial fraud targeting Indian residents.
              Consider correlating with:
            </p>
            <ul className="crime-tags">
              {Object.entries(CYBERCRIME_TAGS).map(([tag, desc]) => (
                <li key={tag}>
                  <strong>{tag}:</strong> {desc}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Legal Notice */}
      <div className="context-notice">
        <p>
          <strong>⚖️ Metadata-only analysis.</strong> This pattern analysis is based on public TOR directory data
          (relay locations, AS information). Findings support investigative leads only. Requires independent
          corroboration and court authorization for enforcement action.
        </p>
      </div>
    </div>
  );
};

export default InfrastructureContextPanel;
