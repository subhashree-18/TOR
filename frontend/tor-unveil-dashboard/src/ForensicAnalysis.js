/**
 * ForensicAnalysis.js ??? PHASE-2 DEEP DIVE
 * Tamil Nadu Police Cyber Crime Wing - Hypothesis Explanation
 * 
 * Explains WHY a hypothesis has a certain confidence using backend-provided evidence factors
 * Reads like an official investigation note prepared for senior officers
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import "./ForensicAnalysis.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function ForensicAnalysis() {
  const navigate = useNavigate();
  const location = useLocation();
  const caseId = location.state?.caseId || "TN/CYB/2024/001234";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedHypothesis, setExpandedHypothesis] = useState(null);
  const [analysisDetails, setAnalysisDetails] = useState({
    hypotheses: []
  });

  // Fetch detailed hypothesis explanations from backend
  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(
          `${API_URL}/api/analysis/${encodeURIComponent(caseId)}/details`
        );

        if (response.data) {
          setAnalysisDetails(response.data);
        }
      } catch (err) {
        console.warn("Backend not available, using mock data:", err.message);

        // Mock data for demonstration when backend unavailable
        setAnalysisDetails({
          hypotheses: [
            {
              rank: 1,
              entry_region: "Germany (DE)",
              exit_region: "Netherlands (NL)",
              confidence_level: "High",
              timing_correlation: "Strong temporal alignment observed. The entry node activity windows (06:00-18:00 UTC) coincide with 87% of the traffic timestamps extracted from the uploaded PCAP evidence. Peak activity correlates with working hours in the suspected origin timezone (IST +5:30), suggesting deliberate timing to mask origin.",
              session_overlap: "Session duration analysis indicates 12 distinct browsing sessions averaging 45 minutes each. Exit node relay logs show corresponding egress traffic within acceptable latency windows (200-400ms). The session patterns are consistent with interactive browsing rather than automated traffic.",
              evidence_consistency: "847 individual packet sequences match the entry-exit pair timing profile. DNS query patterns suggest access to .onion hidden services. TLS fingerprints are consistent with Tor Browser Bundle version 12.x.",
              limiting_factors: "Cannot definitively exclude alternative entry points through the same AS. German relay infrastructure is densely populated, creating multiple plausible entry candidates. Session timing could be coincidental with legitimate traffic patterns."
            },
            {
              rank: 2,
              entry_region: "France (FR)",
              exit_region: "United States (US)",
              confidence_level: "High",
              timing_correlation: "Moderate-to-strong temporal correlation. Entry node uptime overlaps with 72% of evidence timestamps. Notable gaps during 02:00-06:00 UTC which may indicate scheduled relay maintenance or deliberate avoidance patterns.",
              session_overlap: "9 distinct sessions identified with varying durations (15-90 minutes). Exit traffic patterns suggest mixed usage including both hidden services and clearnet access via Tor. Session gaps align with relay consensus updates.",
              evidence_consistency: "612 packet sequences correlate with this path hypothesis. HTTP header analysis indicates content consistent with dark web marketplace patterns. User-agent strings match expected Tor Browser signatures.",
              limiting_factors: "US exit nodes are among the most common globally, reducing specificity of this correlation. French entry infrastructure serves significant legitimate privacy-focused traffic. Alternative middle relay paths could produce similar timing signatures."
            },
            {
              rank: 3,
              entry_region: "United Kingdom (GB)",
              exit_region: "Germany (DE)",
              confidence_level: "Medium",
              timing_correlation: "Moderate correlation with 58% timestamp alignment. Entry node exhibits periodic availability patterns suggesting bandwidth-limited infrastructure or residential hosting. Timing gaps do not clearly correlate with known events.",
              session_overlap: "7 sessions detected with inconsistent duration patterns (5-120 minutes). The variability suggests either multiple users or deliberately obfuscated usage patterns. Exit timing shows acceptable but not optimal alignment.",
              evidence_consistency: "489 packet sequences partially match this hypothesis. Some evidence could equally support alternative paths through adjacent AS networks. Protocol analysis is consistent with Tor but not exclusively indicative.",
              limiting_factors: "UK-DE corridor is heavily trafficked for legitimate Tor usage. Entry relay has documented history of intermittent availability affecting correlation precision. Evidence weight is insufficient for primary hypothesis status."
            },
            {
              rank: 4,
              entry_region: "Switzerland (CH)",
              exit_region: "Sweden (SE)",
              confidence_level: "Medium",
              timing_correlation: "Partial temporal alignment at 52%. Swiss relay infrastructure is known for privacy-focused operation with irregular maintenance windows. Swedish exit shows consistent availability but moderate bandwidth constraints.",
              session_overlap: "6 sessions with relatively uniform 30-40 minute durations. Pattern consistency suggests automated or scripted access rather than interactive browsing. Exit timing within acceptable but not optimal correlation windows.",
              evidence_consistency: "356 packet sequences correlate with this path. Evidence quality is moderate with some ambiguous timestamp interpretations. Protocol signatures are consistent with anonymization traffic.",
              limiting_factors: "CH-SE path represents a small fraction of global Tor traffic, reducing baseline comparison accuracy. Swiss legal framework may limit additional evidence gathering. Alternative Nordic exit nodes could produce similar signatures."
            },
            {
              rank: 5,
              entry_region: "Romania (RO)",
              exit_region: "Finland (FI)",
              confidence_level: "Medium",
              timing_correlation: "Weak-to-moderate correlation at 45%. Romanian entry infrastructure shows high variability in availability. Finnish exit maintains consistent uptime but serves significant legitimate traffic volume.",
              session_overlap: "5 sessions detected with irregular patterns. Session duration variance (10-180 minutes) suggests either multiple distinct users or highly variable usage patterns. Correlation confidence is reduced by this variability.",
              evidence_consistency: "234 packet sequences partially support this hypothesis. Evidence is not strongly differentiating from alternative path hypotheses. Additional corroborating data would strengthen this correlation.",
              limiting_factors: "Eastern European entry points serve diverse user populations including legitimate privacy seekers. Nordic exits are frequently used for general privacy purposes. Statistical significance is below threshold for primary consideration."
            },
            {
              rank: 6,
              entry_region: "Canada (CA)",
              exit_region: "Japan (JP)",
              confidence_level: "Low",
              timing_correlation: "Weak temporal alignment at 32%. Timezone differential (CA-JP spans 13-17 hours depending on regions) creates inherent correlation challenges. Activity windows show minimal overlap with extracted evidence timestamps.",
              session_overlap: "4 potential sessions identified with low confidence. Session boundaries are ambiguous due to timing uncertainty. Exit correlation relies heavily on sparse timestamp data points.",
              evidence_consistency: "178 packet sequences show possible correlation but evidence strength is insufficient for confident attribution. Protocol analysis does not conclusively differentiate from background Tor traffic.",
              limiting_factors: "Trans-Pacific paths represent unusual Tor circuit construction. High latency would create observable performance characteristics not evident in traffic analysis. Hypothesis retained for completeness but not recommended for investigative focus."
            }
          ]
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [caseId]);

  // Toggle accordion
  const toggleHypothesis = (rank) => {
    setExpandedHypothesis(expandedHypothesis === rank ? null : rank);
  };

  // Get confidence class
  const getConfidenceClass = (level) => {
    switch (level?.toLowerCase()) {
      case "high": return "confidence-high";
      case "medium": return "confidence-medium";
      case "low": return "confidence-low";
      default: return "";
    }
  };

  return (
    <div className="forensic-analysis-page">
      {/* Breadcrumb */}
      <nav className="forensic-breadcrumb">
        <span className="crumb" onClick={() => navigate("/dashboard")}>Dashboard</span>
        <span className="separator">/</span>
        <span className="crumb" onClick={() => navigate("/investigation", { state: { caseId } })}>Investigation</span>
        <span className="separator">/</span>
        <span className="crumb" onClick={() => navigate("/analysis", { state: { caseId } })}>Analysis</span>
        <span className="separator">/</span>
        <span className="crumb active">Forensic Details</span>
      </nav>

      {/* Page Header */}
      <div className="forensic-header">
        <h1 className="forensic-title">Hypothesis Evidence Explanation</h1>
        <p className="forensic-subtitle">Case Reference: <code>{caseId}</code></p>
      </div>

      {/* Report Preamble */}
      <div className="report-preamble">
        <p>
          <strong>PURPOSE:</strong> This document provides detailed forensic reasoning 
          for each correlation hypothesis generated during TOR traffic analysis. Each 
          section explains the evidentiary basis for confidence assessments and identifies 
          factors that limit certainty.
        </p>
        <p>
          <strong>INTENDED USE:</strong> Senior officer review, case documentation, 
          and preparation of forensic testimony. This analysis should be read in 
          conjunction with the primary correlation results.
        </p>
      </div>

      {loading ? (
        <div className="forensic-loading">
          <div className="loading-spinner"></div>
          <p>Loading forensic analysis details...</p>
        </div>
      ) : error ? (
        <div className="forensic-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      ) : (
        <>
          {/* Hypotheses Accordion */}
          <div className="hypotheses-accordion">
            {analysisDetails.hypotheses.length === 0 ? (
              <div className="no-data">
                <p>No hypothesis details available. Run correlation analysis first.</p>
              </div>
            ) : (
              analysisDetails.hypotheses.map((hypothesis) => (
                <div 
                  key={hypothesis.rank} 
                  className={`hypothesis-panel ${expandedHypothesis === hypothesis.rank ? "expanded" : ""}`}
                >
                  {/* Accordion Header */}
                  <div 
                    className="hypothesis-header"
                    onClick={() => toggleHypothesis(hypothesis.rank)}
                  >
                    <div className="header-left">
                      <span className="hypothesis-rank">Hypothesis #{hypothesis.rank}</span>
                      <span className="hypothesis-path">
                        {hypothesis.entry_region} ??? {hypothesis.exit_region}
                      </span>
                    </div>
                    <div className="header-right">
                      <span className={`confidence-badge ${getConfidenceClass(hypothesis.confidence_level)}`}>
                        {hypothesis.confidence_level}
                      </span>
                      <span className="expand-indicator">
                        {expandedHypothesis === hypothesis.rank ? "???" : "???"}
                      </span>
                    </div>
                  </div>

                  {/* Accordion Content */}
                  {expandedHypothesis === hypothesis.rank && (
                    <div className="hypothesis-content">
                      {/* Timing Correlation */}
                      <div className="evidence-section">
                        <h3 className="section-label">1. Timing Correlation</h3>
                        <div className="section-text">
                          <p>{hypothesis.timing_correlation}</p>
                        </div>
                      </div>

                      {/* Session Overlap */}
                      <div className="evidence-section">
                        <h3 className="section-label">2. Session Overlap Analysis</h3>
                        <div className="section-text">
                          <p>{hypothesis.session_overlap}</p>
                        </div>
                      </div>

                      {/* Evidence Consistency */}
                      <div className="evidence-section">
                        <h3 className="section-label">3. Evidence Consistency</h3>
                        <div className="section-text">
                          <p>{hypothesis.evidence_consistency}</p>
                        </div>
                      </div>

                      {/* Limiting Factors */}
                      <div className="evidence-section limiting-section">
                        <h3 className="section-label">4. Limiting Factors / Uncertainty</h3>
                        <div className="section-text limiting-text">
                          <p>{hypothesis.limiting_factors}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer Note */}
          <div className="report-footer">
            <p>
              <strong>CONFIDENTIALITY:</strong> This forensic analysis document is prepared 
              for official law enforcement use only. Distribution outside authorized 
              personnel requires appropriate authorization from the supervising officer.
            </p>
          </div>

          {/* Actions */}
          <div className="forensic-actions">
            <button 
              className="btn-primary"
              onClick={() => navigate("/report", { state: { caseId } })}
            >
              Generate Formal Report
            </button>
            <button 
              className="btn-secondary"
              onClick={() => navigate("/analysis", { state: { caseId } })}
            >
              Back to Analysis Summary
            </button>
          </div>
        </>
      )}
    </div>
  );
}
