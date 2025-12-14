// src/GeoTemporalLayer.js
// Time slider for geographic relay views with activity window filtering
import React, { useState, useCallback, useMemo } from "react";
import { Clock, MapPin } from "lucide-react";

export default function GeoTemporalLayer({ relays }) {
  const [selectedTime, setSelectedTime] = useState(50); // 0-100 scale

  // Generate time window (assume relays have timestamps)
  const timeWindowData = useMemo(() => {
    if (!relays || relays.length === 0) {
      return { min: new Date(), max: new Date(), current: new Date() };
    }

    // Assume each relay has an activity timestamp
    const now = new Date();
    const hoursBack = 6; // Show 6-hour window
    const minTime = new Date(now - hoursBack * 60 * 60 * 1000);

    // Calculate time based on slider
    const progress = selectedTime / 100;
    const currentTime = new Date(minTime.getTime() + progress * hoursBack * 60 * 60 * 1000);

    return {
      min: minTime,
      max: now,
      current: currentTime,
      hoursBack,
    };
  }, [selectedTime, relays]);

  // Filter relays by activity window (metadata-only, timestamps only)
  const filteredRelays = useMemo(() => {
    if (!relays) return [];

    const windowStart = timeWindowData.current;
    const windowEnd = new Date(timeWindowData.current.getTime() + 5 * 60 * 1000); // 5-min window

    return relays.filter(relay => {
      if (!relay.timestamp) return true; // Include undated relays
      const relayTime = new Date(relay.timestamp);
      return relayTime >= windowStart && relayTime <= windowEnd;
    });
  }, [relays, timeWindowData]);

  const handleSliderChange = (e) => {
    setSelectedTime(Number(e.target.value));
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Clock size={20} stroke="currentColor" style={{ color: "#0ea5e9" }} />
        <h3 style={styles.title}>Geo-Temporal Correlation</h3>
      </div>

      <div style={styles.timeDisplay}>
        <div style={styles.timeLabel}>Analysis Window</div>
        <div style={styles.timeValue}>
          {formatTime(timeWindowData.current)}
        </div>
        <div style={styles.timeRange}>
          {formatTime(timeWindowData.min)} → {formatTime(timeWindowData.max)}
        </div>
      </div>

      {/* Time Slider */}
      <div style={styles.sliderSection}>
        <input
          type="range"
          min="0"
          max="100"
          value={selectedTime}
          onChange={handleSliderChange}
          style={styles.slider}
        />
        <div style={styles.sliderLabels}>
          <span>Earlier</span>
          <span>Later</span>
        </div>
      </div>

      {/* Relay Activity Visualization */}
      <div style={styles.relayVisualization}>
        <div style={styles.vizHeader}>
          <MapPin size={16} stroke="currentColor" />
          Relays in Window ({filteredRelays.length})
        </div>

        <div style={styles.relayGrid}>
          {filteredRelays.length === 0 ? (
            <div style={styles.emptyViz}>No relays in this time window</div>
          ) : (
            filteredRelays.map((relay, idx) => (
              <div key={idx} style={styles.relayCard}>
                <div style={styles.relayCountry}>{relay.country || "??"}</div>
                <div style={styles.relayCity}>{relay.city || "Unknown"}</div>
                <div style={styles.relayTime}>
                  {relay.timestamp ? formatTime(new Date(relay.timestamp)) : "No timestamp"}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Statistics */}
      <div style={styles.stats}>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>Total Relays</div>
          <div style={styles.statValue}>{relays?.length || 0}</div>
        </div>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>In Window</div>
          <div style={styles.statValue}>{filteredRelays.length}</div>
        </div>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>Coverage</div>
          <div style={styles.statValue}>
            {relays?.length ? ((filteredRelays.length / relays.length) * 100).toFixed(0) + "%" : "0%"}
          </div>
        </div>
      </div>

      <div style={styles.disclaimer}>
        <strong>Metadata-Only Analysis:</strong> This layer shows relay geographic and temporal
        metadata only. No traffic content or user behavior is analyzed. Time windows are for
        correlation filtering only.
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: "#0f172a",
    border: "1px solid #2d3e4f",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "16px",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
    color: "#0ea5e9",
    letterSpacing: "0.5px",
  },
  timeDisplay: {
    marginBottom: "20px",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
  },
  timeLabel: {
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "600",
    textTransform: "uppercase",
  },
  timeValue: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#0ea5e9",
    margin: "6px 0",
  },
  timeRange: {
    fontSize: "12px",
    color: "#94a3b8",
  },
  sliderSection: {
    marginBottom: "20px",
  },
  slider: {
    width: "100%",
    height: "6px",
    borderRadius: "3px",
    background: "linear-gradient(to right, #ef4444, #f59e0b, #10b981)",
    outline: "none",
    WebkitAppearance: "none",
    appearance: "none",
    cursor: "pointer",
  },
  sliderLabels: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "11px",
    color: "#64748b",
    marginTop: "4px",
  },
  relayVisualization: {
    marginBottom: "20px",
  },
  vizHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "12px",
    fontWeight: "600",
    color: "#cbd5e1",
    marginBottom: "12px",
    paddingBottom: "8px",
    borderBottom: "1px solid #2d3e4f",
  },
  relayGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
    gap: "12px",
  },
  relayCard: {
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    border: "1px solid #2d3e4f",
    textAlign: "center",
  },
  relayCountry: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#0ea5e9",
    marginBottom: "4px",
  },
  relayCity: {
    fontSize: "11px",
    color: "#cbd5e1",
    marginBottom: "4px",
  },
  relayTime: {
    fontSize: "10px",
    color: "#64748b",
  },
  emptyViz: {
    textAlign: "center",
    color: "#64748b",
    padding: "20px",
  },
  stats: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "12px",
    marginBottom: "16px",
  },
  statBox: {
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    textAlign: "center",
  },
  statLabel: {
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "600",
    textTransform: "uppercase",
  },
  statValue: {
    fontSize: "18px",
    fontWeight: "700",
    color: "#0ea5e9",
    marginTop: "4px",
  },
  disclaimer: {
    fontSize: "12px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
};
