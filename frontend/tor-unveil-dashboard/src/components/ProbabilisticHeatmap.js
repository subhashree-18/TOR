/**
 * ProbabilisticHeatmap.js
 * 
 * Interactive world map with confidence-weighted heatmap regions.
 * Shows probabilistic origin zones instead of exact IP pinpoints.
 * 
 * Uses Leaflet.js with custom GeoJSON heatmap overlay.
 */

import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import './ProbabilisticHeatmap.css';

const ProbabilisticHeatmap = ({ caseId }) => {
  const mapRef = useRef();
  const [map, setMap] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);

  // Fetch probability map data
  useEffect(() => {
    const fetchProbabilityMap = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/origin/probability-map?case_id=${caseId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch probability map');
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.map) {
          setData(result.map);
        } else {
          setError('No probability map data available');
        }
      } catch (err) {
        setError(err.message);
        console.error('Error fetching probability map:', err);
      } finally {
        setLoading(false);
      }
    };

    if (caseId) {
      fetchProbabilityMap();
    }
  }, [caseId]);

  // Initialize map and draw zones
  useEffect(() => {
    if (!mapRef.current || map) return;

    // Initialize Leaflet map
    const newMap = L.map(mapRef.current).setView([20, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(newMap);

    setMap(newMap);

    return () => {
      newMap.remove();
    };
  }, [mapRef]);

  // Draw probability zones on map
  useEffect(() => {
    if (!map || !data || !data.zones) return;

    // Clear existing layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Circle || layer instanceof L.Popup) {
        map.removeLayer(layer);
      }
    });

    // Draw zones
    data.zones.forEach((zone) => {
      // Create circle marker for zone
      const circle = L.circle([zone.lat, zone.lon], {
        color: zone.color,
        fill: true,
        fillColor: zone.color,
        fillOpacity: zone.opacity,
        weight: 2,
        radius: (zone.radius_km || 100) * 1000, // Convert to meters
        className: 'probability-zone'
      }).addTo(map);

      // Create popup with zone details
      const popupContent = `
        <div class="zone-popup">
          <h4>${zone.zone_name}</h4>
          <p><strong>Type:</strong> ${zone.type}</p>
          <p><strong>Confidence:</strong> ${(zone.confidence * 100).toFixed(1)}%</p>
          <p><strong>Probability:</strong> ${(zone.probability * 100).toFixed(1)}%</p>
          <p><strong>Guards:</strong> ${zone.guard_count}</p>
          ${zone.sources.length > 0 ? `
            <p><strong>Guard Sources (top 3):</strong></p>
            <ul class="source-list">
              ${zone.sources.slice(0, 3).map(fp => `<li>${fp.substring(0, 12)}...</li>`).join('')}
            </ul>
          ` : ''}
        </div>
      `;

      circle.bindPopup(popupContent);

      // Add click listener
      circle.on('click', () => {
        setSelectedZone(zone);
      });

      // Add hover effects
      circle.on('mouseover', function() {
        this.setStyle({
          weight: 3,
          fillOpacity: zone.opacity + 0.1
        });
      });

      circle.on('mouseout', function() {
        this.setStyle({
          weight: 2,
          fillOpacity: zone.opacity
        });
      });
    });

    // Fit bounds to all zones if available
    if (data.zones.length > 0) {
      const bounds = data.zones.map(z => [z.lat, z.lon]);
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [map, data]);

  if (loading) {
    return <div className="heatmap-container loading">Loading probability map...</div>;
  }

  if (error) {
    return <div className="heatmap-container error">{error}</div>;
  }

  if (!data || !data.zones || data.zones.length === 0) {
    return <div className="heatmap-container">No probability map data available</div>;
  }

  return (
    <div className="heatmap-wrapper">
      <div className="heatmap-header">
        <h3>🗺️ Probabilistic Origin Zone Mapping</h3>
        <p>Case: {caseId} | Confidence Level: <span className={`confidence-badge ${data.confidence_level?.toLowerCase()}`}>{data.confidence_level}</span></p>
      </div>

      <div className="heatmap-stats">
        <div className="stat-box">
          <span className="stat-label">Zones</span>
          <span className="stat-value">{data.zones.length}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Total Probability</span>
          <span className="stat-value">{(data.total_probability * 100).toFixed(1)}%</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Most Likely</span>
          <span className="stat-value">{data.most_likely_country || 'Unknown'}</span>
        </div>
        {data.asn_clusters?.length > 0 && (
          <div className="stat-box">
            <span className="stat-label">ASN Clusters</span>
            <span className="stat-value">{data.asn_clusters.length}</span>
          </div>
        )}
      </div>

      <div className="heatmap-container" ref={mapRef}></div>

      <div className="heatmap-legend">
        <h4>Legend</h4>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#FF0000', opacity: 0.7 }}></div>
          <span>High Confidence (&gt;70%)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#FFFF00', opacity: 0.7 }}></div>
          <span>Medium Confidence (40-70%)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#00FF00', opacity: 0.7 }}></div>
          <span>Low Confidence (&lt;40%)</span>
        </div>
      </div>

      {selectedZone && (
        <div className="zone-details-panel">
          <button className="close-btn" onClick={() => setSelectedZone(null)}>✕</button>
          <h4>{selectedZone.zone_name}</h4>
          <div className="details-content">
            <div className="detail-item">
              <span className="detail-label">Zone Type:</span>
              <span className="detail-value">{selectedZone.type}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Confidence Score:</span>
              <span className="detail-value">{(selectedZone.confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Probability Weight:</span>
              <span className="detail-value">{(selectedZone.probability * 100).toFixed(2)}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Associated Guards:</span>
              <span className="detail-value">{selectedZone.guard_count}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Coordinates:</span>
              <span className="detail-value">{selectedZone.lat.toFixed(4)}, {selectedZone.lon.toFixed(4)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Coverage Radius:</span>
              <span className="detail-value">{selectedZone.radius_km.toFixed(1)} km</span>
            </div>
            {selectedZone.sources.length > 0 && (
              <div className="detail-section">
                <h5>Guard Sources</h5>
                <ul className="sources-list">
                  {selectedZone.sources.map((source, idx) => (
                    <li key={idx} title={source}>
                      {source.substring(0, 20)}...
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="zones-list-panel">
        <h4>📍 All Zones ({data.zones.length})</h4>
        <div className="zones-list">
          {data.zones.map((zone, idx) => (
            <div
              key={idx}
              className={`zone-item ${selectedZone?.zone_id === zone.zone_id ? 'active' : ''}`}
              onClick={() => setSelectedZone(zone)}
            >
              <div className="zone-item-color" style={{ backgroundColor: zone.color, opacity: zone.opacity }}></div>
              <div className="zone-item-info">
                <div className="zone-item-name">{zone.zone_name}</div>
                <div className="zone-item-meta">
                  {(zone.probability * 100).toFixed(1)}% • {zone.guard_count} guards
                </div>
              </div>
              <div className="zone-item-badge">{(zone.confidence * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProbabilisticHeatmap;
