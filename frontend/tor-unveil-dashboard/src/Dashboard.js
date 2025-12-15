import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAppContext } from "./AppContext";
import { Copy, CheckCircle, X } from "lucide-react";
import "./Dashboard.css";
import CountryLegend from "./CountryLegend";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Semantic colors
const SEMANTIC_COLORS = {
  entryNode: "#3b82f6",     // Blue
  middleNode: "#f59e0b",    // Amber
  exitNode: "#ef4444",      // Red
  highConfidence: "#10b981", // Green
  medConfidence: "#f59e0b",  // Amber
  lowConfidence: "#ef4444",  // Red
};

export default function Dashboard() {
  const { selectRelay, selectedRelay } = useAppContext();
  const [relays, setRelays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [countryData, setCountryData] = useState([]);
  const [error, setError] = useState(null);
  const [copiedFp, setCopiedFp] = useState(null);
  const [drawerRelay, setDrawerRelay] = useState(null); // For left-side panel
  const [showAllCountries, setShowAllCountries] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(`${API_URL}/relays?limit=1000`);
      const data = response.data?.data || [];
      setRelays(data);

      if (!data.length) throw new Error("No relay data received");

      // build country count chart
      const counts = {};
      data.forEach((relay) => {
        const c = relay.country || "Unknown";
        counts[c] = (counts[c] || 0) + 1;
      });

      // Separate India and other countries
      const indiaCount = counts["IN"] || 0;
      const otherCounts = { ...counts };
      delete otherCounts["IN"];

      let formatted = Object.keys(counts)
        .map((c) => ({ country: c, count: counts[c] }))
        .sort((a, b) => b.count - a.count);

      // Always show India first if present, then others
      if (indiaCount > 0) {
        formatted = [
          { country: "IN", count: indiaCount, isIndia: true },
          ...formatted.filter((c) => c.country !== "IN"),
        ];
      }

      // Limit to top 15 by default, but allow showing all
      const displayData = showAllCountries ? formatted : formatted.slice(0, 15);

      setCountryData(displayData);
    } catch (err) {
      console.error("Error loading data:", err);
      setError("Failed to load data from backend");
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    try {
      await axios.get(`${API_URL}/relays/fetch`);
      await loadData();
    } catch (err) {
      setError("Failed to refresh TOR data");
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedFp(id);
    setTimeout(() => setCopiedFp(null), 2000);
  };
  
  useEffect(() => {
    loadData();
  }, [showAllCountries]);

  const handleSelectRelay = (relay) => {
    setDrawerRelay(relay); // Open left-side drawer instead of navigating
  };

  const handleInvestigateRelay = (relay) => {
    selectRelay(relay); // This will navigate to timeline
    setDrawerRelay(null); // Close drawer
  };

  return (
    <div className="dashboard-container">
      <div className="explanation-banner">
        <h2>Investigation Overview</h2>
        <p>
          <strong>Purpose:</strong> Overview of TOR network relays and their geographic distribution. 
          Select a relay to investigate its activity timeline and potential network correlations.
        </p>
      </div>

      <header className="dashboard-header">
        <h1>TOR Unveil - Network Relay Analysis</h1>
        <button className="refresh-btn" onClick={refresh} disabled={loading}>
          {loading ? "Loading..." : "Refresh Data"}
        </button>
      </header>

      {error && (
        <div className="error-banner">
          <span style={{marginRight: "8px"}}>Error</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading relay data...</p>
        </div>
      ) : (
        <>
          <div className="relay-stats">
            <div className="stat-card">
              <div className="stat-value">{relays.length}</div>
              <div className="stat-label">Total Relays Indexed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{countryData.length}</div>
              <div className="stat-label">Countries Represented</div>
            </div>
          </div>

          {selectedRelay && (
            <div className="selected-relay-banner">
              <div className="banner-header">Under Investigation</div>
              <div className="relay-info-compact">
                <div className="relay-fp">
                  <span className="label">Fingerprint</span>
                  <code 
                    className="fp-value"
                    onClick={() => copyToClipboard(selectedRelay.fingerprint, "main")}
                    title="Click to copy full fingerprint"
                  >
                    {selectedRelay.fingerprint}
                  </code>
                  {copiedFp === "main" && <span className="copy-indicator"><CheckCircle size={14} style={{display: "inline", marginRight: "4px"}} />Copied</span>}
                </div>
                <div className="info-row">
                  <span><strong>Nickname:</strong> {selectedRelay.nickname || "N/A"}</span>
                  <span><strong>Country:</strong> {selectedRelay.country}</span>
                  <span><strong>Role:</strong> {selectedRelay.is_exit ? "Exit" : "Entry/Guard"}</span>
                </div>
              </div>
            </div>
          )}

          <CountryLegend countryData={countryData} isExpanded={false} />

          <div className="section">
            <div className="section-header">
              <div>
                <h3 className="section-title">Geographic Distribution</h3>
                <p className="section-description">
                  Distribution of TOR relays across participating countries.
                  {!showAllCountries && countryData.length > 15 && (
                    <> (Top 15 of {countryData.length} shown) </>
                  )}
                </p>
              </div>
              {countryData.length > 15 && (
                <button
                  className="toggle-countries-btn"
                  onClick={() => setShowAllCountries(!showAllCountries)}
                >
                  {showAllCountries ? "Show Top 15" : "Show All Countries"}
                </button>
              )}
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={countryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="country" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip 
                    contentStyle={{ 
                      background: "#1e293b", 
                      border: "1px solid #0ea5e9",
                      borderRadius: "6px"
                    }}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="#0ea5e9" 
                    radius={[8, 8, 0, 0]}
                    isAnimationActive={true}
                  >
                    {countryData.map((entry, idx) => {
                      const isIndia = entry.country === "IN";
                      return (
                        <Cell 
                          key={`cell-${idx}`} 
                          fill={isIndia ? "#ef4444" : "#0ea5e9"}
                        />
                      );
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="section">
            <h3 className="section-title">Select a Relay to Investigate</h3>
            <p className="section-description">
              Choose any relay below to begin investigation. You'll be able to view its activity timeline and potential network paths.
            </p>
            <div className="table-responsive">
              <table className="relays-table">
                <thead>
                  <tr>
                    <th>Fingerprint</th>
                    <th>Nickname</th>
                    <th>Country</th>
                    <th>Role</th>
                    <th>Bandwidth</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {relays.slice(0, 30).map((relay, i) => (
                    <tr 
                      key={i}
                      className={selectedRelay?.fingerprint === relay.fingerprint ? "selected" : ""}
                      title={relay.nickname}
                    >
                      <td className="fp-cell">
                        <div className="fp-container">
                          <code 
                            className="fp-full"
                            onClick={() => copyToClipboard(relay.fingerprint, `fp-${i}`)}
                            title="Click to copy full fingerprint"
                          >
                            {relay.fingerprint}
                          </code>
                          <button
                            className="fp-copy-btn"
                            onClick={() => copyToClipboard(relay.fingerprint, `fp-${i}`)}
                            title="Copy fingerprint"
                            aria-label="Copy fingerprint"
                          >
                            <Copy size={14} strokeWidth={2} stroke="currentColor" fill="none" />
                          </button>
                          {copiedFp === `fp-${i}` && <span className="copy-badge"><CheckCircle size={14} style={{display: "inline", marginRight: "4px"}} />Copied</span>}
                        </div>
                      </td>
                      <td className="nickname-cell">{relay.nickname || "—"}</td>
                      <td className="country-cell">{relay.country}</td>
                      <td>
                        <div className="role-tags">
                          {relay.is_exit && <span className="role-tag exit">Exit</span>}
                          {relay.is_guard && <span className="role-tag guard">Guard</span>}
                          {!relay.is_exit && !relay.is_guard && <span className="role-tag middle">Middle</span>}
                        </div>
                      </td>
                      <td className="bandwidth">
                        {(relay.advertised_bandwidth / 1_000_000).toFixed(1)} Mbps
                      </td>
                      <td>
                        <button 
                          className="investigate-btn"
                          onClick={() => handleSelectRelay(relay)}
                        >
                          ▶ Investigate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Left-Side Drawer for Relay Details */}
      {drawerRelay && (
        <>
          <div 
            className="drawer-overlay" 
            onClick={() => setDrawerRelay(null)}
          ></div>
          <div className="drawer-panel">
            <div className="drawer-header">
              <h2>Relay Details</h2>
              <button 
                className="drawer-close-btn"
                onClick={() => setDrawerRelay(null)}
                title="Close"
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="drawer-content">
              <div className="detail-section">
                <h3>Fingerprint</h3>
                <code className="fp-block">{drawerRelay.fingerprint}</code>
                <button 
                  className="copy-button"
                  onClick={() => copyToClipboard(drawerRelay.fingerprint, "drawer")}
                >
                  <Copy size={16} />
                  {copiedFp === "drawer" ? "Copied!" : "Copy"}
                </button>
              </div>

              <div className="detail-section">
                <h3>Basic Information</h3>
                <div className="detail-row">
                  <span className="label">Nickname:</span>
                  <span className="value">{drawerRelay.nickname || "N/A"}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Country:</span>
                  <span className="value">{drawerRelay.country}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Role:</span>
                  <span className="value">
                    {drawerRelay.is_exit ? "Exit Node" : drawerRelay.is_guard ? "Guard Node" : "Middle Node"}
                  </span>
                </div>
              </div>

              <div className="detail-section">
                <h3>Network Metrics</h3>
                <div className="detail-row">
                  <span className="label">Bandwidth:</span>
                  <span className="value">{(drawerRelay.advertised_bandwidth / 1_000_000).toFixed(2)} Mbps</span>
                </div>
                <div className="detail-row">
                  <span className="label">Uptime:</span>
                  <span className="value">{(drawerRelay.uptime || 0).toFixed(0)} seconds</span>
                </div>
              </div>

              <div className="detail-section">
                <h3>Operational Details</h3>
                <div className="detail-row">
                  <span className="label">Platform:</span>
                  <span className="value">{drawerRelay.platform || "Unknown"}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Contact:</span>
                  <span className="value">{drawerRelay.contact || "Not provided"}</span>
                </div>
              </div>

              <div className="drawer-actions">
                <button 
                  className="action-btn investigate-btn"
                  onClick={() => handleInvestigateRelay(drawerRelay)}
                >
                  Begin Investigation
                </button>
                <button 
                  className="action-btn secondary-btn"
                  onClick={() => setDrawerRelay(null)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
