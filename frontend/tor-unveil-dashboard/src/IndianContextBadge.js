/**
 * IndianContextBadge.js - India-Specific Context for Tamil Nadu Police
 * 
 * Highlights:
 * - Indian ASNs in TOR infrastructure
 * - Foreign exit relays
 * - Regional routing patterns
 * - Relevance to police investigations
 */

import React from "react";
import { AlertTriangle, Globe, MapPin, AlertCircle } from "lucide-react";
import "./IndianContextBadge.css";

// Indian ASN ranges and known providers
const INDIAN_ASNS = {
  "AS4755": "VSNL/Tata Communications",
  "AS9829": "National Internet Backbone (NIB)",
  "AS9498": "Bharat Sanchar Nigam (BSNL)",
  "AS18101": "Reliance Jio (Mukesh Ambani Group)",
  "AS55836": "Bharti Airtel",
  "AS24560": "Vodafone Idea",
  "AS133480": "Telemedia Networks",
  "AS45839": "MTNL",
  "AS17638": "Tripadvisor/Indian ISPs",
  "AS56399": "NET4INDIA",
  "AS58953": "Data Shack / Indian Hosting",
};

// Countries with high fraud/threat relevance to Tamil Nadu police
const HIGH_RISK_COUNTRIES = {
  BG: "Bulgaria - Known credential theft & phishing infrastructure",
  CN: "China - APT activity, state-sponsored cyber operations",
  KP: "North Korea - Cryptocurrency theft, sanctions evasion",
  IR: "Iran - Cyber espionage, infrastructure targeting",
  RU: "Russia - Financial fraud networks, ransomware distribution",
  RO: "Romania - Identity theft operations, card fraud rings",
  PK: "Pakistan - Regional threat actor coordination",
  BD: "Bangladesh - Financial fraud targeting South Asia",
};

// Helper to check if AS is Indian
function isIndianASN(as) {
  if (!as) return false;
  const asLower = as.toLowerCase();
  return Object.keys(INDIAN_ASNS).some((key) =>
    asLower.includes(key.toLowerCase())
  );
}

// Helper to get Indian ASN provider name
function getIndianASNProvider(as) {
  if (!as) return null;
  for (const [asn, provider] of Object.entries(INDIAN_ASNS)) {
    if (as.toLowerCase().includes(asn.toLowerCase())) {
      return provider;
    }
  }
  return null;
}

// Helper to check if country is high-risk
function isHighRiskCountry(country) {
  return country && country.toUpperCase() in HIGH_RISK_COUNTRIES;
}

export default function IndianContextBadge({ relay, entry, middle, exit }) {
  const badges = [];
  let hasIndianNode = false;
  let hasRiskPattern = false;

  // Check entry node for Indian ASN
  if (entry && isIndianASN(entry.as)) {
    hasIndianNode = true;
    badges.push({
      type: "indian-entry",
      label: `🇮🇳 INDIAN ENTRY NODE`,
      subtitle: `${getIndianASNProvider(entry.as) || entry.as}`,
      description: "TOR circuit initiated from Indian network infrastructure",
      severity: "high",
      icon: "flag",
    });
  }

  // Check middle node for Indian ASN
  if (middle && isIndianASN(middle.as)) {
    hasIndianNode = true;
    badges.push({
      type: "indian-middle",
      label: `🇮🇳 INDIAN RELAY NODE`,
      subtitle: `${getIndianASNProvider(middle.as) || middle.as}`,
      description: "TOR circuit routed through Indian network infrastructure",
      severity: "medium",
      icon: "flag",
    });
  }

  // Check exit node
  if (exit) {
    if (isIndianASN(exit.as)) {
      hasIndianNode = true;
      badges.push({
        type: "indian-exit",
        label: `🇮🇳 INDIAN EXIT NODE`,
        subtitle: `${getIndianASNProvider(exit.as) || exit.as}`,
        description: "TOR circuit exits from Indian network infrastructure",
        severity: "high",
        icon: "flag",
      });
    } else if (isHighRiskCountry(exit.country)) {
      hasRiskPattern = true;
      badges.push({
        type: "high-risk-exit",
        label: `HIGH-RISK EXIT JURISDICTION`,
        subtitle: exit.country,
        description: HIGH_RISK_COUNTRIES[exit.country.toUpperCase()],
        severity: "critical",
        icon: "alert",
      });
    }
  }

  // Check for India→Foreign→Risk pattern (highly suspicious for financial fraud)
  if (
    entry &&
    entry.country === "IN" &&
    exit &&
    exit.country !== "IN" &&
    isHighRiskCountry(exit.country)
  ) {
    hasRiskPattern = true;
    badges.push({
      type: "india-foreign-fraud",
      label: `INDIA→FOREIGN HIGH-RISK PATTERN`,
      subtitle: `${exit.country} (Known fraud jurisdiction)`,
      description:
        "Indian user routing through high-risk country jurisdiction. STRONG INDICATOR of financial fraud targeting Indian residents (phishing, UPI scams, OTP theft, etc.)",
      severity: "critical",
      icon: "alert",
    });
  }

  if (badges.length === 0) {
    return null;
  }

  return (
    <div className={`indian-context-container ${hasRiskPattern ? "has-risk-pattern" : ""} ${hasIndianNode ? "has-indian-node" : ""}`}>
      {/* Severity banner at top */}
      {hasRiskPattern && (
        <div className="severity-banner critical">
          <AlertTriangle size={16} style={{display: 'inline-block', marginRight: '6px'}} />
          INVESTIGATIVE ALERT: Pattern detected relevant to Tamil Nadu Cyber Crime Wing
        </div>
      )}

      {/* Main badges */}
      <div className="badges-grid">
        {badges.map((badge, idx) => (
          <div key={idx} className={`context-badge badge-${badge.type} severity-${badge.severity}`}>
            <div className="badge-header">
              <span className="badge-icon">
                {badge.icon === "alert" && <AlertTriangle size={20} />}
                {badge.icon === "flag" && <MapPin size={20} />}
                {badge.icon === "globe" && <Globe size={20} />}
              </span>
              <div className="badge-header-text">
                <div className="badge-label">{badge.label}</div>
                <div className="badge-subtitle">{badge.subtitle}</div>
              </div>
            </div>
            <div className="badge-body">
              <p className="badge-description">{badge.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Info panel about Indian context and Tamil Nadu Police relevance */}
      <div className="india-context-info">
        <div className="info-header">
          <AlertCircle size={18} />
          <h4>🇮🇳 Tamil Nadu Cyber Crime Wing - Investigation Support</h4>
        </div>
        
        <div className="info-content">
          <div className="info-section">
            <strong>Relevance to Investigation:</strong>
            <ul>
              <li>🔴 <strong>Financial Fraud:</strong> Online phishing, UPI scams, OTP theft, ATM fraud</li>
              <li>🔴 <strong>Cybercrime:</strong> Anonymous threats, extortion, ransomware coordination</li>
              <li>🔴 <strong>Attribution Patterns:</strong> Cross-border routing to mask origin/accountability</li>
              <li>🔴 <strong>Network Forensics:</strong> Indian node involvement indicates local infrastructure use</li>
            </ul>
          </div>

          {hasRiskPattern && (
            <div className="info-section pattern-alert">
              <strong>Critical Pattern Indicators:</strong>
              <ul>
                <li>India→High-Risk Country routing = Strong correlation with financial fraud</li>
                <li>Multiple Indian nodes = Infrastructure reuse or deliberate network routing</li>
                <li>Foreign exit + high-risk ASN = Evasion of attribution and jurisdiction</li>
              </ul>
            </div>
          )}

          <div className="info-section legal-notice">
            <strong>⚖️ Legal & Investigative Notice:</strong>
            <p>
              This analysis is <strong>metadata-only</strong> (TOR network topology + GeoIP data). 
              No content inspection, packet analysis, or TOR deanonymization is performed.
              Findings support investigative leads only; court authorization required for enforcement action.
              Compliance: Tamil Nadu Police, IPC § 43 (Instrument), § 66 (Computer systems), § 120 (Conspiracy).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
