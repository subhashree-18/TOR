/**
 * EvidenceSummaryMap.js - Dynamic Evidence & Node Visualization
 * Displays forensic evidence metadata with TOR entry/exit node visualization on world map
 * 
 * Features:
 * - Dynamically populated session summary (Time Range, Sessions, Packets, IPs, Protocols)
 * - World map showing entry and exit node locations
 * - Color-coded nodes (Green=Entry, Red=Exit)
 * - Tooltips and interactive elements
 * - Real-time data binding from API responses
 */

import React, { useState, useEffect } from 'react';
import './EvidenceSummaryMap.css';

/**
 * Generate realistic forensic timeline based on current time
 * Reference time: 22/12/2025, 02:15:49 am IST
 */
function generateRealisticTimeline() {
  // Reference timestamp: Case submission time
  const referenceTime = new Date('2025-12-22T02:15:49');
  
  // Helper function to subtract minutes from a date
  const subtractMinutes = (date, minutes) => {
    const result = new Date(date);
    result.setMinutes(result.getMinutes() - minutes);
    return result;
  };
  
  // Helper function to format date-time as DD/MM/YYYY, HH:MM:SS am/pm
  const formatDateTime = (date) => {
    if (!date || !(date instanceof Date)) {
      return 'Unknown time';
    }
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    let hour = date.getHours();
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');
    const period = hour >= 12 ? 'pm' : 'am';
    
    if (hour > 12) {
      hour -= 12;
    } else if (hour === 0) {
      hour = 12;
    }
    
    const hourStr = String(hour).padStart(2, '0');
    
    return `${day}/${month}/${year}, ${hourStr}:${minute}:${second} ${period}`;
  };
  
  // Generate timeline events working backwards from reference time
  const events = [
    // Event 1: Case submission (most recent) - T+0
    {
      time: referenceTime,
      type: 'Case Submission',
      description: "Forensic file 'narcotics_case_002.csv' uploaded with 8 relay events. Event range: 2025-12-22T02:10:15 to 2025-12-22T02:14:30."
    },
    // Event 2: Path correlation analysis - T-1min 26sec (1.43 minutes ago)
    {
      time: subtractMinutes(referenceTime, 1),
      type: 'Path Correlated',
      description: 'A plausible path was generated linking entry 038ABBB752B1CBEE to exit 1F2E3D4C5B6A7F8E (score: High confidence 92%).'
    },
    // Event 3: Relay observation - T-2min 31sec
    {
      time: subtractMinutes(referenceTime, 2),
      type: 'Relay Last Seen',
      description: 'Relay lisdex (000004) was last observed at relay uptime tracker. Last confirmed: 2025-12-22 02:13:18 UTC+5:30.'
    },
    // Event 4: Relay observation - T-3min 30sec
    {
      time: subtractMinutes(referenceTime, 3),
      type: 'Relay Last Seen',
      description: 'Relay SharingIsCaring (000077) was last observed with packet transmission. Last confirmed: 2025-12-22 02:12:04 UTC+5:30.'
    },
    // Event 5: Analysis started - T-5min
    {
      time: subtractMinutes(referenceTime, 5),
      type: 'Analysis Started',
      description: 'TOR traffic correlation analysis initiated for case CID/TN/CCW/2024/002. Processing 1,827 packets across 47 relays.'
    },
    // Event 6: Relay observation - T-7min 18sec
    {
      time: subtractMinutes(referenceTime, 7),
      type: 'Relay Last Seen',
      description: 'Relay seele (000A10) was last observed at consensus time. Last confirmed: 2025-12-22 02:08:31 UTC+5:30.'
    },
    // Event 7: Relay observation - T-9min 14sec
    {
      time: subtractMinutes(referenceTime, 9),
      type: 'Relay Last Seen',
      description: 'Relay hubbabubbaABC (000D11) was last observed with active connections. Last confirmed: 2025-12-22 02:06:35 UTC+5:30.'
    },
    // Event 8: Relay observation - T-11min 8sec
    {
      time: subtractMinutes(referenceTime, 11),
      type: 'Relay Last Seen',
      description: 'Relay SENDNOOSEplz (000F3E) was last observed updating descriptor. Last confirmed: 2025-12-22 02:04:41 UTC+5:30.'
    },
    // Event 9: Relay observation - T-15min
    {
      time: subtractMinutes(referenceTime, 15),
      type: 'Relay Last Seen',
      description: 'Relay titamon3 (001125) was last observed in circuit construction. Last confirmed: 2025-12-22 02:00:49 UTC+5:30.'
    },
    // Event 10: Relay observation - T-18min 35sec
    {
      time: subtractMinutes(referenceTime, 18),
      type: 'Relay Last Seen',
      description: 'Relay skylarkRelay (00240E) was last observed with exit traffic. Last confirmed: 2025-12-22 01:57:14 UTC+5:30.'
    },
    // Event 11: Relay observation - T-21min 22sec
    {
      time: subtractMinutes(referenceTime, 21),
      type: 'Relay Last Seen',
      description: 'Relay 9g4net3 (0024E9) was last observed in relay pool. Last confirmed: 2025-12-22 01:54:27 UTC+5:30.'
    },
    // Event 12: Relay observation - T-24min 4sec
    {
      time: subtractMinutes(referenceTime, 24),
      type: 'Relay Last Seen',
      description: 'Relay Quetzalcoatl (00251F) was last observed with bandwidth announcement. Last confirmed: 2025-12-22 01:51:45 UTC+5:30.'
    },
    // Event 13: File upload - T-30min
    {
      time: subtractMinutes(referenceTime, 30),
      type: 'File Upload',
      description: "Forensic file 'packet_capture_v2.csv' uploaded with 12 connection events. Event range: 2025-12-21T20:45:20 to 2025-12-21T21:02:15 IST."
    },
    // Event 14: Case creation - T-40min
    {
      time: subtractMinutes(referenceTime, 40),
      type: 'Investigation Opened',
      description: 'New investigation case CID/TN/CCW/2024/002 created: Dark Web Narcotics Investigation. Assigned to Sub-Inspector Priya Sharma.'
    }
  ];
  
  // Convert to display format and reverse (most recent first)
  return events.map(event => ({
    timestamp: formatDateTime(event.time),
    type: event.type,
    description: event.description
  })).reverse();
}

// Generate mock timeline on module load
const MOCK_TIMELINE_EVENTS = generateRealisticTimeline();

// Mock session data
const MOCK_SESSION_DATA = {
  timeStart: '21-12-2025 19:37:09',
  timeEnd: '21-12-2025 20:37:09',
  sessions: 124,
  packets: 8734,
  ips: 23,
  protocols: 'TCP, UDP, DNS'
};

const EvidenceSummaryMap = ({ sessionData, analysisData, caseId }) => {
  const [entryNodes, setEntryNodes] = useState([]);
  const [exitNodes, setExitNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [timelineEvents, setTimelineEvents] = useState(MOCK_TIMELINE_EVENTS);
  const [showTimeline, setShowTimeline] = useState(true);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  // API URL
  const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

  // Fetch real timeline data from backend
  useEffect(() => {
    const fetchTimelineData = async () => {
      try {
        setLoadingTimeline(true);
        const response = await fetch(`${API_URL}/api/timeline?limit=100`);
        
        if (response.ok) {
          const data = await response.json();
          // Handle both array and object response formats
          const events = Array.isArray(data) ? data : data.events || data.timeline || [];
          
          if (events.length > 0) {
            const formattedEvents = events.map(event => {
              // Format timestamp to readable format
              const timestamp = event.timestamp ? new Date(event.timestamp).toLocaleString('en-GB', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
              }).replace(/,/, '') : 'Unknown';

              return {
                timestamp: timestamp,
                type: event.label || event.event_type || event.type || 'Event',
                description: event.description || event.details || ''
              };
            });
            
            setTimelineEvents(formattedEvents);
            console.log(`✓ Loaded ${formattedEvents.length} real timeline events from backend`);
          } else {
            console.log("No timeline events from backend, using mock data");
            setTimelineEvents(MOCK_TIMELINE_EVENTS);
          }
        } else {
          console.log(`Timeline API returned status ${response.status}, using mock data`);
          setTimelineEvents(MOCK_TIMELINE_EVENTS);
        }
      } catch (error) {
        console.log("Failed to fetch timeline data from backend:", error.message);
        console.log("Falling back to mock data");
        setTimelineEvents(MOCK_TIMELINE_EVENTS);
      } finally {
        setLoadingTimeline(false);
      }
    };

    // Fetch timeline data on component mount
    fetchTimelineData();
  }, [API_URL]);

  // Extract entry and exit nodes from analysis data
  useEffect(() => {
    if (!analysisData) {
      console.log("No analysisData provided to EvidenceSummaryMap");
      return;
    }

    // Handle both 'hypotheses' and 'entry_node'/'exit_node' formats
    let hypotheses = analysisData.hypotheses || [];
    
    // If hypotheses is empty but analysisData has TOR relay data, use that
    if (hypotheses.length === 0 && analysisData.tor_relays) {
      console.log("Using TOR relay data for visualization");
      hypotheses = (analysisData.tor_relays || []).map((relay, idx) => ({
        entry_region: relay.country || 'Unknown',
        exit_region: relay.country || 'Unknown',
        confidence_score: 0.5,
        rank: idx + 1
      }));
    }

    if (hypotheses.length === 0) {
      console.log("No hypotheses available");
      return;
    }

    const entries = [];
    const exits = [];

    hypotheses.forEach((hypothesis, idx) => {
      // Handle entry region (format: "Country (fingerprint...)" or just "Country")
      let entryCountry = null;
      if (hypothesis.entry_region) {
        const entryMatch = hypothesis.entry_region.match(/([A-Z]{2})/);
        entryCountry = entryMatch ? entryMatch[0] : null;
      } else if (hypothesis.entry_node) {
        const entryMatch = hypothesis.entry_node.match(/([A-Z]{2})/);
        entryCountry = entryMatch ? entryMatch[0] : null;
      }

      // Handle exit region
      let exitCountry = null;
      if (hypothesis.exit_region) {
        const exitMatch = hypothesis.exit_region.match(/([A-Z]{2})/);
        exitCountry = exitMatch ? exitMatch[0] : null;
      } else if (hypothesis.exit_node) {
        const exitMatch = hypothesis.exit_node.match(/([A-Z]{2})/);
        exitCountry = exitMatch ? exitMatch[0] : null;
      }

      if (entryCountry) {
        entries.push({
          id: `entry-${idx}`,
          country: entryCountry,
          fullText: hypothesis.entry_region || hypothesis.entry_node,
          confidence: hypothesis.confidence_score || 0.5,
          rank: hypothesis.rank || idx + 1,
          latitude: getCountryLatitude(entryCountry),
          longitude: getCountryLongitude(entryCountry)
        });
      }

      if (exitCountry) {
        exits.push({
          id: `exit-${idx}`,
          country: exitCountry,
          fullText: hypothesis.exit_region || hypothesis.exit_node,
          confidence: hypothesis.confidence_score || 0.5,
          rank: hypothesis.rank || idx + 1,
          latitude: getCountryLatitude(exitCountry),
          longitude: getCountryLongitude(exitCountry)
        });
      }
    });

    console.log(`Extracted ${entries.length} entry nodes and ${exits.length} exit nodes`);
    setEntryNodes(entries);
    setExitNodes(exits);
  }, [analysisData]);

  // Get approximate latitude for country (simplified mapping)
  const getCountryLatitude = (countryCode) => {
    const map = {
      'US': 37.0902, 'GB': 55.3781, 'DE': 51.1657, 'FR': 46.2276, 'NL': 52.1326,
      'CA': 56.1304, 'AU': -25.2744, 'JP': 36.2048, 'SG': 1.3521, 'IN': 20.5937,
      'RU': 61.5240, 'CN': 35.8617, 'BR': -14.2350, 'MX': 23.6345, 'ZA': -30.5595,
      'IT': 41.8719, 'ES': 40.4637, 'SE': 60.1282, 'NO': 60.4720, 'CH': 46.8182
    };
    return map[countryCode] || 0;
  };

  // Get approximate longitude for country (simplified mapping)
  const getCountryLongitude = (countryCode) => {
    const map = {
      'US': -95.7129, 'GB': -3.4360, 'DE': 10.4515, 'FR': 2.2137, 'NL': 5.2913,
      'CA': -106.3468, 'AU': 133.7751, 'JP': 138.2529, 'SG': 103.8198, 'IN': 78.9629,
      'RU': 105.3188, 'CN': 104.1954, 'BR': -51.9253, 'MX': -102.5528, 'ZA': 22.9375,
      'IT': 12.5674, 'ES': -3.7492, 'SE': 18.6435, 'NO': 8.4689, 'CH': 8.2275
    };
    return map[countryCode] || 0;
  };

  // Convert lat/lon to SVG coordinates
  const latLonToSvg = (lat, lon) => {
    // Mercator projection approximation
    const x = ((lon + 180) / 360) * 800;
    const y = ((90 - lat) / 180) * 400;
    return { x: Math.max(10, Math.min(790, x)), y: Math.max(10, Math.min(390, y)) };
  };

  // Format timestamp
  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${day}-${month}-${year} ${hours}:${minutes}:${seconds}`;
  };

  const sessionInfo = {
    timeStart: formatDateTime(sessionData?.time_range_start) || MOCK_SESSION_DATA.timeStart,
    timeEnd: formatDateTime(sessionData?.time_range_end) || MOCK_SESSION_DATA.timeEnd,
    sessions: sessionData?.total_sessions_captured || sessionData?.total_sessions || MOCK_SESSION_DATA.sessions,
    packets: sessionData?.total_packets || sessionData?.packet_count || MOCK_SESSION_DATA.packets,
    ips: sessionData?.unique_ip_addresses || sessionData?.unique_ips || MOCK_SESSION_DATA.ips,
    protocols: (sessionData?.protocols_detected || sessionData?.protocols || []).join(', ') || MOCK_SESSION_DATA.protocols,
    hasData: !!(sessionData?.total_sessions_captured || sessionData?.total_sessions)
  };

  return (
    <div className="evidence-summary-map">
      {/* Session Summary Panel */}
      <div className="session-summary-panel">
        <div className="summary-header">
          <h3>📊 Parsed Session Summary</h3>
        </div>
        <div className="summary-grid">
          <div className="summary-item">
            <label>Time Range Start:</label>
            <value>{sessionInfo.timeStart}</value>
          </div>
          <div className="summary-item">
            <label>Time Range End:</label>
            <value>{sessionInfo.timeEnd}</value>
          </div>
          <div className="summary-item">
            <label>Total Sessions Captured:</label>
            <value className="highlight">{sessionInfo.sessions}</value>
          </div>
          <div className="summary-item">
            <label>Total Packets:</label>
            <value className="highlight">{sessionInfo.packets}</value>
          </div>
          <div className="summary-item">
            <label>Unique IP Addresses:</label>
            <value className="highlight">{sessionInfo.ips}</value>
          </div>
          <div className="summary-item">
            <label>Protocols Detected:</label>
            <value>{sessionInfo.protocols}</value>
          </div>
        </div>
      </div>

      {/* World Map with Entry/Exit Nodes */}
      <div className="map-container">
        <div className="map-header">
          <h3>🌍 TOR Node Correlation Map</h3>
          <div className="map-legend">
            <div className="legend-item entry">
              <span className="dot entry"></span> Entry Nodes (Guard)
            </div>
            <div className="legend-item exit">
              <span className="dot exit"></span> Exit Nodes
            </div>
            <div className="legend-item confidence">
              <span className="note">Size indicates confidence score</span>
            </div>
          </div>
        </div>

        <svg className="world-map" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
          {/* Ocean background */}
          <defs>
            <radialGradient id="confidenceGradient" cx="30%" cy="30%">
              <stop offset="0%" stopColor="rgba(255, 255, 255, 0.8)" />
              <stop offset="100%" stopColor="rgba(0, 0, 0, 0.2)" />
            </radialGradient>
          </defs>

          <rect x="0" y="0" width="800" height="400" fill="#1e3a8a" />

          {/* World continents (simplified) */}
          <g className="continents" opacity="0.3">
            {/* North America */}
            <ellipse cx="150" cy="120" rx="60" ry="80" fill="#4ade80" />
            {/* South America */}
            <ellipse cx="180" cy="280" rx="40" ry="60" fill="#4ade80" />
            {/* Europe */}
            <ellipse cx="320" cy="100" rx="50" ry="40" fill="#4ade80" />
            {/* Africa */}
            <ellipse cx="380" cy="220" rx="50" ry="70" fill="#4ade80" />
            {/* Asia */}
            <ellipse cx="500" cy="140" rx="100" ry="80" fill="#4ade80" />
            {/* Australia */}
            <ellipse cx="650" cy="300" rx="40" ry="50" fill="#4ade80" />
          </g>

          {/* Grid lines */}
          <g className="grid" strokeWidth="0.5" stroke="#ffffff" opacity="0.15" strokeDasharray="2,2">
            {[100, 200, 300, 400, 500, 600, 700].map(x => (
              <line key={`vline-${x}`} x1={x} y1="0" x2={x} y2="400" />
            ))}
            {[100, 200, 300].map(y => (
              <line key={`hline-${y}`} x1="0" y1={y} x2="800" y2={y} />
            ))}
          </g>

          {/* Exit Nodes (Red) */}
          {exitNodes.map((node) => {
            const pos = latLonToSvg(node.latitude, node.longitude);
            const size = 4 + node.confidence * 6; // Size based on confidence
            return (
              <g
                key={node.id}
                className="node exit-node"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => setSelectedNode(node.id)}
              >
                {/* Glow effect */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={size + 3}
                  fill="#ff6b6b"
                  opacity="0.3"
                />
                {/* Main node */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={size}
                  fill="#ff0000"
                  stroke="#ffcccc"
                  strokeWidth="2"
                  className={hoveredNode === node.id ? 'highlighted' : ''}
                />
                {/* Label */}
                {hoveredNode === node.id && (
                  <text
                    x={pos.x}
                    y={pos.y - size - 15}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="11"
                    fontWeight="bold"
                    className="node-label"
                  >
                    {node.country} (Exit #{node.rank})
                  </text>
                )}
              </g>
            );
          })}

          {/* Entry Nodes (Green) */}
          {entryNodes.map((node) => {
            const pos = latLonToSvg(node.latitude, node.longitude);
            const size = 4 + node.confidence * 6; // Size based on confidence
            return (
              <g
                key={node.id}
                className="node entry-node"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => setSelectedNode(node.id)}
              >
                {/* Glow effect */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={size + 3}
                  fill="#51cf66"
                  opacity="0.3"
                />
                {/* Main node */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={size}
                  fill="#00c000"
                  stroke="#ccffcc"
                  strokeWidth="2"
                  className={hoveredNode === node.id ? 'highlighted' : ''}
                />
                {/* Label */}
                {hoveredNode === node.id && (
                  <text
                    x={pos.x}
                    y={pos.y - size - 15}
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="11"
                    fontWeight="bold"
                    className="node-label"
                  >
                    {node.country} (Guard #{node.rank})
                  </text>
                )}
              </g>
            );
          })}

          {/* Connection lines between entry and exit */}
          {entryNodes.length > 0 && exitNodes.length > 0 && (
            <g className="connections" strokeWidth="1" stroke="#ffff99" opacity="0.4">
              {entryNodes.slice(0, 3).map((entry) =>
                exitNodes.slice(0, 3).map((exit) => {
                  const entryPos = latLonToSvg(entry.latitude, entry.longitude);
                  const exitPos = latLonToSvg(exit.latitude, exit.longitude);
                  return (
                    <line
                      key={`conn-${entry.id}-${exit.id}`}
                      x1={entryPos.x}
                      y1={entryPos.y}
                      x2={exitPos.x}
                      y2={exitPos.y}
                      strokeDasharray="3,3"
                    />
                  );
                })
              )}
            </g>
          )}
        </svg>

        {/* Node details if selected */}
        {selectedNode && (
          <div className="node-details">
            <button className="close-btn" onClick={() => setSelectedNode(null)}>✕</button>
            {(() => {
              const node = [...entryNodes, ...exitNodes].find(n => n.id === selectedNode);
              return node ? (
                <div>
                  <h4>{node.country} {node.fullText.includes('Entry') ? '(Entry Node)' : '(Exit Node)'}</h4>
                  <p><strong>Confidence:</strong> {(node.confidence * 100).toFixed(1)}%</p>
                  <p><strong>Rank:</strong> #{node.rank}</p>
                  <p><strong>Details:</strong> {node.fullText}</p>
                </div>
              ) : null;
            })()}
          </div>
        )}
      </div>

      {/* Forensic Timeline Section */}
      {showTimeline && (
        <div className="forensic-timeline-container">
          <div className="timeline-header">
            <h3>🔍 Forensic Timeline {loadingTimeline ? '⏳ Loading...' : timelineEvents === MOCK_TIMELINE_EVENTS ? '(Mock Data)' : '(Real Data)'}</h3>
            <button className="toggle-btn" onClick={() => setShowTimeline(false)}>Collapse</button>
          </div>
          
          {loadingTimeline ? (
            <div className="timeline-loading">
              <div className="loading-spinner"></div>
              <p>Fetching timeline events from server...</p>
            </div>
          ) : (
            <div className="timeline-events">
              {timelineEvents && timelineEvents.length > 0 ? (
                timelineEvents.map((event, index) => (
                  <div key={index} className={`timeline-event event-type-${event.type.toLowerCase().replace(/\s+/g, '-')}`}>
                    <div className="timeline-marker">
                      <div className="timeline-dot"></div>
                      {index < timelineEvents.length - 1 && <div className="timeline-line"></div>}
                    </div>
                    <div className="event-content">
                      <div className="event-header">
                        <span className="event-timestamp">{event.timestamp}</span>
                        <span className={`event-type event-type-badge`}>{event.type}</span>
                      </div>
                      <p className="event-description">{event.description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="timeline-empty">
                  <p>No timeline events available</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceSummaryMap;
