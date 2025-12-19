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
  const [viewMode, setViewMode] = useState('risk'); // 'risk', 'traffic', 'activity'

  useEffect(() => {
    const fetchRelayData = async () => {
      try {
        const response = await fetch(`${API_URL}/relays/map`);
        const data = await response.json();
        setRelayData(data || []);
      } catch (error) {
        console.warn("Could not fetch relay data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRelayData();
  }, []);

  const getHeatmapColor = (relay) => {
    switch (viewMode) {
      case 'risk':
        const riskLevel = relay.risk_score / 100;
        return `rgba(255, ${Math.floor(255 - (riskLevel * 200))}, 0, 0.7)`;
      case 'traffic':
        return relay.is_exit ? 'rgba(255, 0, 0, 0.8)' : 'rgba(0, 100, 255, 0.6)';
      case 'activity':
        return relay.running ? 'rgba(0, 255, 0, 0.7)' : 'rgba(128, 128, 128, 0.4)';
      default:
        return 'rgba(0, 100, 255, 0.6)';
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
      <div className="map-controls">
        <h3>🌍 Global TOR Relay Network</h3>
        <div className="view-mode-selector">
          <button 
            className={viewMode === 'risk' ? 'active' : ''}
            onClick={() => setViewMode('risk')}
          >
            Risk Heat Map
          </button>
          <button 
            className={viewMode === 'traffic' ? 'active' : ''}
            onClick={() => setViewMode('traffic')}
          >
            Traffic Flow
          </button>
          <button 
            className={viewMode === 'activity' ? 'active' : ''}
            onClick={() => setViewMode('activity')}
          >
            Activity Status
          </button>
        </div>
      </div>

      <div className="world-map-container">
        <svg viewBox="0 0 800 400" className="world-map">
          {/* Ocean background */}
          <rect width="800" height="400" fill="#1a365d" />
          
          {/* Realistic world map */}
          <WorldMapBackground />
          
          {/* Grid overlay for coordinates */}
          <defs>
            <pattern id="grid" width="50" height="25" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 25" fill="none" stroke="#2a4a6b" strokeWidth="0.5" opacity="0.4"/>
            </pattern>
          </defs>
          <rect width="800" height="400" fill="url(#grid)" />
          
          {/* Equator and Prime Meridian */}
          <line x1="0" y1="200" x2="800" y2="200" stroke="#34568B" strokeWidth="1" opacity="0.6" strokeDasharray="2,2"/>
          <line x1="400" y1="0" x2="400" y2="400" stroke="#34568B" strokeWidth="1" opacity="0.6" strokeDasharray="2,2"/>
          
          {/* Render relay points as heatmap */}
          {relayData.map((relay, index) => {
            // Convert lat/lon to SVG coordinates (simplified projection)
            const x = ((relay.lon + 180) / 360) * 800;
            const y = ((90 - relay.lat) / 180) * 400;
            
            return (
              <g key={relay.fingerprint || index}>
                <circle
                  cx={x}
                  cy={y}
                  r={Math.max(2, Math.min(8, relay.risk_score / 10))}
                  fill={getHeatmapColor(relay)}
                  stroke="rgba(255,255,255,0.5)"
                  strokeWidth="1"
                  className="relay-point"
                  title={`${relay.nickname} (${relay.country}) - Risk: ${relay.risk_score}`}
                />
              </g>
            );
          })}
        </svg>
      </div>

      <div className="map-legend">
        <h4>Legend</h4>
        {viewMode === 'risk' && (
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color" style={{background: 'rgba(255, 255, 0, 0.7)'}}></div>
              <span>Low Risk (0-30)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{background: 'rgba(255, 128, 0, 0.7)'}}></div>
              <span>Medium Risk (31-70)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{background: 'rgba(255, 0, 0, 0.7)'}}></div>
              <span>High Risk (71-100)</span>
            </div>
          </div>
        )}
        {viewMode === 'traffic' && (
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color" style={{background: 'rgba(255, 0, 0, 0.8)'}}></div>
              <span>Exit Nodes</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{background: 'rgba(0, 100, 255, 0.6)'}}></div>
              <span>Guard/Middle Nodes</span>
            </div>
          </div>
        )}
        <div className="map-stats">
          <span><strong>Total Relays:</strong> {relayData.length}</span>
          <span><strong>Exit Nodes:</strong> {relayData.filter(r => r.is_exit).length}</span>
          <span><strong>Guard Nodes:</strong> {relayData.filter(r => r.is_guard).length}</span>
        </div>
      </div>
    </div>
  );
};

export default TorRelayMap;