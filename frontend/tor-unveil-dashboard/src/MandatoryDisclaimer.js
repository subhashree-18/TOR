/**
 * MandatoryDisclaimer.js - Legal Compliance & Deanonymization Warning
 * 
 * CRITICAL: This component ensures police officers understand:
 * 1. NO TOR deanonymization is claimed or possible
 * 2. Analysis is metadata-only (no packet inspection)
 * 3. Results are correlation assistance only
 * 4. Scores indicate plausibility, not certainty
 * 5. Legal and technical limitations of the system
 */

import React, { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Shield,
  AlertTriangle,
  X,
  CheckCircle,
  Scale,
} from "lucide-react";
import "./MandatoryDisclaimer.css";

export default function MandatoryDisclaimer({ onAcknowledge, isModal = false }) {
  const [acknowledged, setAcknowledged] = useState(false);

  const handleAcknowledge = () => {
    setAcknowledged(true);
    if (onAcknowledge) {
      onAcknowledge();
    }
  };

  return (
    <div className={`mandatory-disclaimer ${isModal ? "modal" : ""}`}>
      <div className="disclaimer-container">
        {/* Header */}
        <div className="disclaimer-header">
          <AlertTriangle size={32} className="warning-icon" />
          <h2><Scale size={28} style={{marginRight: "10px", verticalAlign: "middle"}} />MANDATORY LEGAL DISCLAIMER</h2>
          <p className="header-subtitle">
            Read carefully before analyzing TOR network paths
          </p>
        </div>

        {/* Critical: No Deanonymization */}
        <div className="disclaimer-section critical">
          <div className="section-icon">
            <Shield size={20} />
          </div>
          <div className="section-content">
            <h3><AlertTriangle size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />CRITICAL: NO TOR DEANONYMIZATION</h3>
            <ul>
              <li>
                <strong>This system CANNOT identify TOR users.</strong>
              </li>
              <li>
                <strong>
                  This system does NOT break TOR encryption or anonymity.
                </strong>
              </li>
              <li>
                <strong>
                  Any claim that this system deanonymizes TOR users is FALSE.
                </strong>
              </li>
              <li>
                TOR UNVEIL performs <em>metadata correlation only</em> using
                publicly available information.
              </li>
              <li>
                Results show <em>plausible path combinations</em>, not confirmed
                paths used by specific individuals.
              </li>
            </ul>
          </div>
        </div>

        {/* Metadata-Only Analysis */}
        <div className="disclaimer-section">
          <div className="section-icon">
            <FileText size={20} />
          </div>
          <div className="section-content">
            <h3><FileText size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Metadata-Only Analysis</h3>
            <p>
              This system analyzes <strong>ONLY</strong> the following publicly
              available metadata:
            </p>
            <ul>
              <li>Relay fingerprints and nicknames (from Onionoo directory)</li>
              <li>Geographic location (country/AS)</li>
              <li>Bandwidth capacity</li>
              <li>Uptime intervals (when relays were online)</li>
              <li>Relay flags (Guard, Exit, Stable, Fast, etc.)</li>
            </ul>
            <p>
              <strong>NOT analyzed:</strong> Packet content, user traffic, IP
              addresses, encryption keys, or any private data.
            </p>
          </div>
        </div>

        {/* What This System Does */}
        <div className="disclaimer-section">
          <div className="section-icon">
            <CheckCircle2 size={20} />
          </div>
          <div className="section-content">
            <h3><CheckCircle size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />What TOR UNVEIL Actually Does</h3>
            <ul>
              <li>
                <strong>Time-based correlation:</strong> Identifies which relays
                were online simultaneously
              </li>
              <li>
                <strong>Path plausibility scoring:</strong> Ranks potential
                Entry-Middle-Exit combinations
              </li>
              <li>
                <strong>Forensic assistance:</strong> Helps correlate with
                timestamps from network logs or PCAP files
              </li>
              <li>
                <strong>Investigation support:</strong> Provides technical
                context for TOR-based threat investigations
              </li>
              <li>
                <strong>Non-technical explanation:</strong> Makes TOR network
                structure understandable to non-technical investigators
              </li>
            </ul>
          </div>
        </div>

        {/* Limitations */}
        <div className="disclaimer-section warning">
          <div className="section-icon">
            <AlertCircle size={20} />
          </div>
          <div className="section-content">
            <h3><AlertCircle size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Technical & Legal Limitations</h3>
            <ul>
              <li>
                <strong>Multiple paths plausible:</strong> Many paths may match
                a given timestamp, making certainty impossible
              </li>
              <li>
                <strong>High score ≠ certainty:</strong> 95% confidence means
                "likely based on metadata," not "proven"
              </li>
              <li>
                <strong>Relay churn:</strong> TOR directory changes constantly;
                historical data has gaps
              </li>
              <li>
                <strong>Correlation != causation:</strong> Path plausibility
                alone does not prove user identity or activity
              </li>
              <li>
                <strong>No SIGINT value:</strong> Cannot be used to target
                individuals or mass surveillance
              </li>
              <li>
                <strong>Metadata analysis limitations:</strong> Does not
                establish causal link between user actions and TOR paths
              </li>
            </ul>
          </div>
        </div>

        {/* Appropriate Use Cases */}
        <div className="disclaimer-section">
          <div className="section-icon">
            <FileText size={20} />
          </div>
          <div className="section-content">
            <h3><CheckCircle size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Appropriate Use Cases</h3>
            <ul>
              <li>
                <strong>Forensic correlation:</strong> Match timestamps from
                logs with relay activity to understand network context
              </li>
              <li>
                <strong>Investigation support:</strong> Provide technical
                context for warrant applications or investigative reports
              </li>
              <li>
                <strong>TOR network education:</strong> Help officers
                understand how TOR routing works
              </li>
              <li>
                <strong>Threat profiling:</strong> Understand suspicious
                routing patterns (e.g., India→High-Risk Country)
              </li>
              <li>
                <strong>Evidence collection:</strong> Support documented
                investigation process with technical findings
              </li>
            </ul>
          </div>
        </div>

        {/* Inappropriate Use */}
        <div className="disclaimer-section critical">
          <div className="section-icon">
            <AlertTriangle size={20} />
          </div>
          <div className="section-content">
            <h3><X size={20} style={{marginRight: "8px", verticalAlign: "middle", color: "#ef4444"}} />PROHIBITED USE CASES</h3>
            <ul>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} /><strong>Mass surveillance</strong> of TOR users
              </li>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} />
                <strong>
                  Claiming the system deanonymizes TOR users in any context
                </strong>
              </li>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} /><strong>Using results as sole evidence</strong> for
                prosecution without corroborating evidence
              </li>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} /><strong>Targeting individuals</strong> based solely on
                metadata correlation
              </li>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} /><strong>Sharing results publicly</strong> as "TOR
                deanonymization proof"
              </li>
              <li>
                <X size={16} style={{display: "inline", marginRight: "6px", color: "#ef4444"}} /><strong>Court testimony</strong> claiming certainty beyond
                technical limitations
              </li>
            </ul>
          </div>
        </div>

        {/* Court Presentation */}
        <div className="disclaimer-section">
          <div className="section-icon">
            <Shield size={20} />
          </div>
          <div className="section-content">
            <h3><Scale size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Court Presentation Guidelines</h3>
            <ul>
              <li>
                Always explain that this is <strong>metadata correlation</strong>, not
                deanonymization
              </li>
              <li>
                Present alongside <strong>corroborating evidence</strong>
                (logs, PCAP, behavioral evidence)
              </li>
              <li>
                Clearly state{" "}
                <strong>
                  "This indicates a plausible path, not a confirmed path"
                </strong>
              </li>
              <li>
                Explain the <strong>score limitations</strong> and what each
                percentage means
              </li>
              <li>
                Acknowledge <strong>alternative explanations</strong> and why
                this path was selected
              </li>
              <li>
                Frame as <strong>technical investigative support</strong>, not
                definitive proof
              </li>
            </ul>
          </div>
        </div>

        {/* Legal Compliance */}
        <div className="disclaimer-section">
          <div className="section-icon">
            <FileText size={20} />
          </div>
          <div className="section-content">
            <h3><FileText size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Legal Compliance</h3>
            <p>
              TOR UNVEIL is designed to comply with:
            </p>
            <ul>
              <li>
                <strong>ITA 2000 Section 79:</strong> Cooperation with law
                enforcement using technical investigation tools
              </li>
              <li>
                <strong>Privacy protections:</strong> No personal data beyond
                publicly available relay information
              </li>
              <li>
                <strong>Due process:</strong> Findings should be corroborated
                with additional evidence
              </li>
              <li>
                <strong>Forensic standards:</strong> All analysis reproducible
                and auditable
              </li>
            </ul>
            <p style={{ marginTop: "12px", fontWeight: "600", color: "#fca5a5" }}>
              <Scale size={16} style={{display: "inline", marginRight: "6px", verticalAlign: "middle"}} />For specific legal questions, consult your agency's legal
              counsel and prosecutor.
            </p>
          </div>
        </div>

        {/* Acknowledgment Checkbox */}
        <div className="disclaimer-acknowledgment">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="disclaimer-checkbox"
            />
            <span>
              I have read and understood the limitations and appropriate use
              cases for TOR UNVEIL. I understand that{" "}
              <strong>
                this system does NOT deanonymize TOR users
              </strong>
              , and I will use this system only for legitimate forensic
              investigation purposes within legal boundaries.
            </span>
          </label>
        </div>

        {/* Action Button */}
        <button
          className="proceed-btn"
          onClick={handleAcknowledge}
          disabled={!acknowledged}
        >
          I Acknowledge and Understand These Limitations
        </button>

        {!acknowledged && (
          <p className="disclaimer-note">
            <CheckCircle size={14} style={{display: "inline", marginRight: "6px", verticalAlign: "middle"}} />Check the box above to proceed with the investigation
          </p>
        )}
      </div>
    </div>
  );
}
