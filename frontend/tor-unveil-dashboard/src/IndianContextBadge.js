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
  "AS9829": "National Internet Backbone",
  "AS9498": "Bharat Sanchar Nigam (BSNL)",
  "AS18101": "Reliance Jio",
  "AS55836": "Airtel",
  "AS24560": "Vodafone Idea",
  "AS133480": "Telemedia",
};

// Countries with high fraud/threat relevance to Tamil Nadu police
const HIGH_RISK_COUNTRIES = {
  BG: "Bulgaria - Credential theft infrastructure",
  CN: "China - Advanced persistent threats",
  KP: "North Korea - Sanctions evasion",
  IR: "Iran - Cyber espionage targeting",
  RU: "Russia - Financial fraud networks",
  RO: "Romania - Identity theft operations",
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

  // Check entry node
  if (entry && isIndianASN(entry.as)) {
    badges.push({
      type: "indian-entry",
      label: `Indian Entry: ${getIndianASNProvider(entry.as) || entry.as}`,
      description: "TOR entry node hosted in India",
      icon: "flag",
    });
  }

  // Check middle node
  if (middle && isIndianASN(middle.as)) {
    badges.push({
      type: "indian-middle",
      label: `Indian Relay: ${getIndianASNProvider(middle.as) || middle.as}`,
      description: "TOR middle relay hosted in India",
      icon: "flag",
    });
  }

  // Check exit node
  if (exit && isIndianASN(exit.as)) {
    badges.push({
      type: "indian-exit",
      label: `Indian Exit: ${getIndianASNProvider(exit.as) || exit.as}`,
      description: "TOR exit node hosted in India",
      icon: "flag",
    });
  } else if (exit && isHighRiskCountry(exit.country)) {
    badges.push({
      type: "high-risk-exit",
      label: `High-Risk Exit: ${exit.country}`,
      description: HIGH_RISK_COUNTRIES[exit.country.toUpperCase()],
      icon: "alert",
    });
  }

  // Check for India-Foreign-Foreign pattern (suspicious for financial fraud)
  if (
    entry &&
    entry.country === "IN" &&
    exit &&
    exit.country !== "IN" &&
    isHighRiskCountry(exit.country)
  ) {
    badges.push({
      type: "india-foreign-fraud",
      label: "India→Foreign High-Risk Pattern",
      description:
        "Indian user routing through high-risk country. Common in financial fraud targeting India.",
      icon: "alert",
    });
  }

  if (badges.length === 0) {
    return null;
  }

  return (
    <div className="indian-context-container">
      {badges.map((badge, idx) => (
        <div key={idx} className={`context-badge badge-${badge.type}`}>
          <div className="badge-content">
            <span className="badge-icon">
              {badge.icon === "alert" && <AlertTriangle size={16} />}
              {badge.icon === "flag" && <MapPin size={16} />}
              {badge.icon === "globe" && <Globe size={16} />}
            </span>
            <div className="badge-text">
              <div className="badge-label">{badge.label}</div>
              <div className="badge-description">{badge.description}</div>
            </div>
          </div>
        </div>
      ))}

      {/* Info panel about Indian context */}
      <div className="india-context-info">
        <h4>🇮🇳 Tamil Nadu Police Context</h4>
        <p>
          Indian TOR infrastructure is relevant to investigation of:
          <ul>
            <li>Online financial fraud targeting Indian residents</li>
            <li>TOR-based anonymous threats and cyber harassment</li>
            <li>Cross-border routing patterns in criminal networks</li>
            <li>Foreign exit nodes used to mask attribution</li>
          </ul>
        </p>
        <p>
          <strong>Key Pattern:</strong> India→ High-Risk Country routing often
          indicates financial fraud operations (phishing, scams, etc.)
        </p>
      </div>
    </div>
  );
}
