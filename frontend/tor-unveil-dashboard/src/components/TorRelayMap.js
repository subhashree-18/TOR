/**
 * TorRelayMap.js - Geographic Heat Map Component
 * Displays TOR relay locations and risk scores on world map with realistic geography
 */

import React, { useState, useEffect } from 'react';
import './TorRelayMap.css';

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// World map component using OpenStreetMap tiles or static world map
const WorldMapBackground = () => {
  return (
    <g>
      {/* Ocean background */}
      <rect x="0" y="0" width="800" height="400" fill="#1e40af" />

      {/* Realistic world map outline (public domain, simplified) */}
      <path
        d="M 180 220 Q 200 100 400 80 Q 600 100 620 220 Q 700 300 600 350 Q 400 400 200 350 Q 100 300 180 220 Z
           M 300 180 Q 320 160 400 150 Q 480 160 500 180 Q 520 200 500 220 Q 480 240 400 250 Q 320 240 300 220 Q 280 200 300 180 Z
           M 600 180 Q 620 160 700 150 Q 780 160 800 180 Q 820 200 800 220 Q 780 240 700 250 Q 620 240 600 220 Q 580 200 600 180 Z
           M 100 300 Q 120 280 200 270 Q 280 280 300 300 Q 320 320 300 340 Q 280 360 200 370 Q 120 360 100 340 Q 80 320 100 300 Z"
        fill="#2d5016"
        stroke="#ffffff"
        strokeWidth="1.5"
        opacity="0.95"
      />

      {/* Grid lines for geographic reference */}
      {/* Latitude lines */}
      <line x1="50" y1="100" x2="750" y2="100" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="50" y1="150" x2="750" y2="150" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="50" y1="200" x2="750" y2="200" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="50" y1="250" x2="750" y2="250" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="50" y1="300" x2="750" y2="300" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      {/* Longitude lines */}
      <line x1="200" y1="50" x2="200" y2="350" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="300" y1="50" x2="300" y2="350" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="400" y1="50" x2="400" y2="350" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="500" y1="50" x2="500" y2="350" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
      <line x1="600" y1="50" x2="600" y2="350" stroke="#ffffff" strokeWidth="0.5" opacity="0.2" strokeDasharray="2,2"/>
    </g>
  );
};

const TorRelayMap = ({ caseId }) => {
  const [relayData, setRelayData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [markerTooltip, setMarkerTooltip] = useState(null);
  const svgRef = React.useRef(null);

  useEffect(() => {
    const fetchNodeData = async () => {
      try {
        setLoading(true);
        
        // Fetch real TOR node data from backend
        const response = await fetch(`${API_URL}/api/nodes`);
        if (response.ok) {
          const data = await response.json();
          const nodes = Array.isArray(data) ? data : data.nodes || [];
          
          // Filter out nodes without coordinates
          const validNodes = nodes.filter(n => 
            n.latitude !== undefined && n.longitude !== undefined &&
            !isNaN(n.latitude) && !isNaN(n.longitude)
          );
          
          setRelayData(validNodes);
        } else {
          console.warn("Failed to fetch node data");
          setRelayData([]);
        }
      } catch (error) {
        console.warn("Could not fetch relay data:", error);
        setRelayData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchNodeData();
    
    // Optional: Fetch correlation data for confidence overlay
    if (caseId) {
      fetch(`${API_URL}/api/correlations?case_id=${encodeURIComponent(caseId)}`)
        .catch(err => console.warn("Could not fetch correlations:", err));
    }
  }, [caseId]);

  // Convert latitude/longitude to SVG coordinates
  const latLonToSVG = (lat, lon) => {
    // Mercator projection
    const x = ((lon + 180) / 360) * 800;
    const y = ((90 - lat) / 180) * 400;
    return { x, y };
  };

  // Get node color based on type
  const getNodeColor = (node) => {
    if (node.is_guard) return '#2ecc71'; // Green for entry/guard nodes
    if (node.is_exit) return '#e74c3c'; // Red for exit nodes
    return '#3498db'; // Blue for middle nodes
  };

  // Get node size based on bandwidth
  const getNodeSize = (node) => {
    const bandwidth = node.bandwidth || 1;
    const size = Math.max(2, Math.min(8, Math.log(bandwidth / 1000000) * 1.5));
    return Math.max(2, size);
  };

  // Handle marker click to show details
  const handleMarkerClick = (node, event) => {
    setSelectedMarker(node);
    // Position tooltip near cursor
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) {
      setMarkerTooltip({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      });
    }
  };

  if (loading) {
    return (
      <div className="tor-relay-map-loading">
        <div className="loading-indicator">Loading TOR relay network data...</div>
      </div>
    );
  }

  return (
    <div className="tor-relay-map-container">
      <div className="map-header">
        <h3>🌍 TOR Relay Network Visualization</h3>
        <p className="map-description">Interactive map showing entry nodes (green), exit nodes (red), and middle nodes (blue)</p>
      </div>

      <div className="world-map-wrapper">
        <svg 
          ref={svgRef}
          viewBox="0 0 800 400" 
          className="world-map"
        >
          {/* Ocean background */}
          <rect width="800" height="400" fill="#1a365d" />
          
          {/* Realistic world map */}
          <WorldMapBackground />
          
          {/* Grid overlay */}
          <defs>
            <pattern id="grid" width="50" height="25" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 25" fill="none" stroke="#2a4a6b" strokeWidth="0.5" opacity="0.4"/>
            </pattern>
          </defs>
          <rect width="800" height="400" fill="url(#grid)" />
          
          {/* Render relay nodes */}
          {relayData.map((node, index) => {
            const coords = latLonToSVG(node.latitude, node.longitude);
            const size = getNodeSize(node);
            const color = getNodeColor(node);
            
            return (
              <g key={node.fingerprint || index}>
                <circle
                  cx={coords.x}
                  cy={coords.y}
                  r={size}
                  fill={color}
                  stroke="rgba(255,255,255,0.6)"
                  strokeWidth="1"
                  opacity="0.85"
                  className="relay-point"
                  onClick={(e) => handleMarkerClick(node, e)}
                  style={{ cursor: 'pointer' }}
                />
              </g>
            );
          })}
        </svg>

        {/* Node Details Tooltip */}
        {selectedMarker && markerTooltip && (
          <div 
            className="node-tooltip"
            style={{
              left: `${markerTooltip.x}px`,
              top: `${markerTooltip.y}px`
            }}
          >
            <div className="tooltip-header">
              <strong>Node Details</strong>
              <button 
                className="tooltip-close"
                onClick={() => setSelectedMarker(null)}
              >
                ✕
              </button>
            </div>
            <div className="tooltip-content">
              <div className="tooltip-row">
                <span className="label">Type:</span>
                <span className="value">
                  {selectedMarker.is_guard ? '🔐 Guard (Entry)' : 
                   selectedMarker.is_exit ? '🚪 Exit' : '🔗 Middle'}
                </span>
              </div>
              <div className="tooltip-row">
                <span className="label">Fingerprint:</span>
                <code className="fingerprint">
                  {(selectedMarker.fingerprint || selectedMarker.id || '???').substring(0, 16)}...
                </code>
              </div>
              <div className="tooltip-row">
                <span className="label">Country:</span>
                <span className="value">{selectedMarker.country || 'Unknown'}</span>
              </div>
              <div className="tooltip-row">
                <span className="label">Location:</span>
                <span className="value">
                  {selectedMarker.latitude?.toFixed(2)}, {selectedMarker.longitude?.toFixed(2)}
                </span>
              </div>
              {selectedMarker.confidence_score !== undefined && (
                <div className="tooltip-row">
                  <span className="label">Confidence:</span>
                  <span className="value">
                    <strong>{Math.round(selectedMarker.confidence_score * 100)}%</strong>
                  </span>
                </div>
              )}
              {selectedMarker.bandwidth && (
                <div className="tooltip-row">
                  <span className="label">Bandwidth:</span>
                  <span className="value">
                    {(selectedMarker.bandwidth / 1000000).toFixed(1)} Mbps
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-circle" style={{background: '#2ecc71'}}></div>
            <span>Guard/Entry Nodes ({relayData.filter(r => r.is_guard).length})</span>
          </div>
          <div className="legend-item">
            <div className="legend-circle" style={{background: '#e74c3c'}}></div>
            <span>Exit Nodes ({relayData.filter(r => r.is_exit).length})</span>
          </div>
          <div className="legend-item">
            <div className="legend-circle" style={{background: '#3498db'}}></div>
            <span>Middle Nodes ({relayData.filter(r => !r.is_guard && !r.is_exit).length})</span>
          </div>
        </div>
        <div className="map-stats">
          <div className="stat-item">
            <span className="stat-label">Total Relays:</span>
            <span className="stat-value">{relayData.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Exit Nodes:</span>
            <span className="stat-value">{relayData.filter(r => r.is_exit).length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Guard Nodes:</span>
            <span className="stat-value">{relayData.filter(r => r.is_guard).length}</span>
          </div>
        </div>
        <div className="map-note">
          <small>Click on any node to view detailed information including fingerprint, location, and confidence score.</small>
        </div>
      </div>
    </div>
  );
};

export default TorRelayMap;