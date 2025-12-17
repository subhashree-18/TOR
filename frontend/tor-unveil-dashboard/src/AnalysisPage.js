// src/AnalysisPage.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAppContext } from "./AppContext";
import { AlertCircle } from "lucide-react";
import SankeyChart from "./SankeyChart";
import CountryLegend from "./CountryLegend";
import "./AnalysisPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function AnalysisPage() {
  const { selectedRelay, selectedPath } = useAppContext();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("timeline");
  const [showMethodology, setShowMethodology] = useState(false);

  useEffect(() => {
    if (!selectedRelay && !selectedPath) return;

    async function loadTimeline() {
      try {
        setLoading(true);
        setError(null);

        const res = await axios.get(`${API_URL}/api/timeline?limit=100`);
        const allEvents = res.data.events || [];

        if (selectedRelay) {
          const filtered = allEvents.filter(
            (e) =>
              e.fingerprint === selectedRelay.fingerprint.slice(0, 6) ||
              e.type === "relay"
          );
          setEvents(filtered.slice(0, 50));
        } else if (selectedPath) {
          const filtered = allEvents.filter((e) =>
            e.type === "path" ||
            e.entry === selectedPath.entry.fingerprint.slice(0, 6) ||
            e.exit === selectedPath.exit.fingerprint.slice(0, 6)
          );
          setEvents(filtered.slice(0, 50));
        }
      } catch (err) {
        console.error("Error loading timeline:", err);
        setError("Failed to load timeline data");
      } finally {
        setLoading(false);
      }
    }

    loadTimeline();
  }, [selectedRelay, selectedPath]);

  // Copy fingerprint to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (!selectedRelay && !selectedPath) {
    return (
      <div className="analysis-container">
        <div className="explanation-banner">
          <h2>Investigation Analysis</h2>
          <p>
            <strong>Purpose:</strong> Detailed analysis view combining timeline reconstruction 
            and TOR flow visualization. Select a relay or path to begin analysis.
          </p>
        </div>
        <div className="empty-state">
          <h3>No Data Selected</h3>
          <p>
            Please select a relay from the Dashboard or a path from the Paths page to view the analysis.
          </p>
          <p style={{ fontSize: "14px", color: "var(--text-muted)" }}>
            The Analysis page will display both chronological events and network flow visualization.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-container">
      <div className="explanation-banner">
        <h2>Investigation Analysis</h2>
        <p>
          <strong>Purpose:</strong> Detailed analysis view combining timeline reconstruction 
          and TOR flow visualization for comprehensive investigation support.
        </p>
      </div>

      {/* Collapsible Methodology */}
      <div className="methodology-section">
        <button 
          className="methodology-toggle"
          onClick={() => setShowMethodology(!showMethodology)}
        >
          {showMethodology ? "▼" : "▶"} Scoring Methodology
        </button>
        {showMethodology && (
          <div className="methodology-details">
            <div className="methodology-grid">
              <div className="methodology-item">
                <h4>Uptime Window</h4>
                <p><strong>7 days</strong> - Realistic timeframe</p>
              </div>
              <div className="methodology-item">
                <h4>AS Penalty</h4>
                <p><strong>0.70x</strong> - Same AS penalization</p>
              </div>
              <div className="methodology-item">
                <h4>Country Penalty</h4>
                <p><strong>0.60x</strong> - Same country penalization</p>
              </div>
              <div className="methodology-item">
                <h4>Score Cap</h4>
                <p><strong>85%</strong> - Maximum confidence</p>
              </div>
            </div>
            <div className="methodology-warning">
              <AlertCircle size={18} style={{display: "inline-block", marginRight: "8px", verticalAlign: "middle"}} /><strong>Important:</strong> Plausibility estimates only, not proof.
            </div>
          </div>
        )}
      </div>

      {/* Selected Information */}
      {selectedRelay && (
        <div className="selected-info">
          <h3>Relay Under Investigation</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>Fingerprint</label>
              <code 
                className="fingerprint-display"
                onClick={() => copyToClipboard(selectedRelay.fingerprint)}
                title="Click to copy"
              >
                {selectedRelay.fingerprint}
              </code>
            </div>
            <div className="info-item">
              <label>Nickname</label>
              <div>{selectedRelay.nickname || "N/A"}</div>
            </div>
            <div className="info-item">
              <label>Country</label>
              <div>{selectedRelay.country}</div>
            </div>
            <div className="info-item">
              <label>IP Address</label>
              <div>{selectedRelay.ip}</div>
            </div>
            <div className="info-item">
              <label>Role</label>
              <div>
                {selectedRelay.role && selectedRelay.role.split(',').map((r, i) => (
                  <span key={i} className="role-badge">{r.trim()}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedPath && (
        <div className="selected-info">
          <h3>Path Under Investigation</h3>
          <div className="path-flow">
            <div className="node entry-node" title={selectedPath.entry.fingerprint}>
              <div className="node-label">Entry</div>
              <div className="node-name">{selectedPath.entry.nickname || selectedPath.entry.fingerprint.slice(0, 8)}</div>
              <div className="node-country">{selectedPath.entry.country}</div>
            </div>
            <div className="flow-arrow">→</div>
            <div className="node middle-node" title={selectedPath.middle.fingerprint}>
              <div className="node-label">Middle</div>
              <div className="node-name">{selectedPath.middle.nickname || selectedPath.middle.fingerprint.slice(0, 8)}</div>
              <div className="node-country">{selectedPath.middle.country}</div>
            </div>
            <div className="flow-arrow">→</div>
            <div className="node exit-node" title={selectedPath.exit.fingerprint}>
              <div className="node-label">Exit</div>
              <div className="node-name">{selectedPath.exit.nickname || selectedPath.exit.fingerprint.slice(0, 8)}</div>
              <div className="node-country">{selectedPath.exit.country}</div>
            </div>
          </div>
          
          <div className="score-section">
            <div className="score-display">
              <div className="score-value">{(selectedPath.score * 100).toFixed(0)}%</div>
              <div className="score-label">Confidence Score</div>
              <div className="confidence-level">
                {selectedPath.score >= 0.8 ? "HIGH" : selectedPath.score >= 0.5 ? "MEDIUM" : "LOW"}
              </div>
            </div>
            {selectedPath.components && (
              <div className="components-breakdown">
                <h4>Score Components</h4>
                <div className="components-list">
                  {Object.entries(selectedPath.components).map(([key, value]) => (
                    <div key={key} className="component-row">
                      <span className="component-label">{key}</span>
                      <span className="component-value">
                        {typeof value === "number" ? value.toFixed(3) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-btn ${activeTab === "timeline" ? "active" : ""}`}
          onClick={() => setActiveTab("timeline")}
        >
          Timeline
        </button>
        <button
          className={`tab-btn ${activeTab === "sankey" ? "active" : ""}`}
          onClick={() => setActiveTab("sankey")}
        >
          Flow Visualization
        </button>
      </div>

      {/* Timeline Tab */}
      {activeTab === "timeline" && (
        <div className="tab-content">
          <h3>Chronological Events</h3>
          {loading && <div className="loading">Loading timeline data...</div>}
          {error && <div className="error">{error}</div>}
          {!loading && events.length === 0 && (
            <div className="empty-timeline">
              <p>No events available for the selected item.</p>
            </div>
          )}
          {!loading && events.length > 0 && (
            <div className="timeline">
              {events.map((event, idx) => (
                <div key={idx} className="timeline-event">
                  <div className="event-time">
                    {event.timestamp ? new Date(event.timestamp).toLocaleString() : "Unknown Time"}
                  </div>
                  <div className="event-dot"></div>
                  <div className="event-content">
                    <div className="event-type">{event.type || event.label || "Event"}</div>
                    <div className="event-description">{event.description || ""}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sankey Tab */}
      {activeTab === "sankey" && selectedPath && (
        <div className="tab-content">
          <h3>TOR Flow Visualization</h3>
          <p className="sankey-description">
            The flow thickness represents the plausibility score. Wider flows indicate higher confidence in the path.
          </p>
          <div className="sankey-chart-container">
            <SankeyChart paths={[selectedPath]} />
          </div>

          {/* Country Legend */}
          <CountryLegend
            countryData={[
              { country: selectedPath.entry?.country, count: 1 },
              { country: selectedPath.middle?.country, count: 1 },
              { country: selectedPath.exit?.country, count: 1 },
            ].filter((c) => c.country)}
            isExpanded={false}
          />

          <div className="sankey-legend">
            <div className="legend-item">
              <span className="legend-color entry-color"></span>
              <span>Entry Node - Connection enters TOR network</span>
            </div>
            <div className="legend-item">
              <span className="legend-color middle-color"></span>
              <span>Middle Relay - Intermediate routing node</span>
            </div>
            <div className="legend-item">
              <span className="legend-color exit-color"></span>
              <span>Exit Node - Connection leaves TOR network</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === "sankey" && !selectedPath && (
        <div className="tab-content">
          <div className="empty-timeline">
            <p>Please select a path to visualize the TOR flow.</p>
          </div>
        </div>
      )}
    </div>
  );
}
