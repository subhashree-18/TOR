// src/TamilNaduBrand.js
import React from "react";
import { ShieldAlert, Globe } from "lucide-react";
import "./TamilNaduBrand.css";

export default function TamilNaduBrand() {
  return (
    <div className="tn-brand-container">
      <div className="tn-brand-header">
        <div className="tn-logo-section">
          {/* Tamil Nadu Police Badge/Symbol */}
          <div className="tn-badge">
            <ShieldAlert size={32} className="badge-icon" />
          </div>
          <div className="tn-branding">
            <div className="tn-title-group">
              <h1 className="tn-title">
                <span className="tn-tamil">தமிழ்நாடு</span> TOR UNVEIL
              </h1>
              <p className="tn-subtitle">Tamil Nadu Police Cybercrime Investigation Unit</p>
            </div>
          </div>
        </div>
        <div className="tn-seal">
          <div className="seal-circle">
            <span className="seal-text">TN CYBER</span>
          </div>
        </div>
      </div>

      <div className="tn-mission-stripe">
        <div className="stripe-content">
          <Globe size={16} className="stripe-icon" />
          <span className="stripe-text">
            Securing Tamil Nadu's Digital Infrastructure | Cybercrime Investigation & Network Forensics
          </span>
        </div>
      </div>
    </div>
  );
}
