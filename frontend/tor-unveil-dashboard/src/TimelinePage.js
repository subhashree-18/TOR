// src/TimelinePage.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAppContext } from "./AppContext";
import { Clock } from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function TimelinePage() {
  const { selectedRelay, selectedPath, setCurrentTab } = useAppContext();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedRelay && !selectedPath) return;

    async function loadTimeline() {
      try {
        setLoading(true);
        setError(null);

        // Fetch timeline events from backend
        const res = await axios.get(`${API_URL}/api/timeline?limit=100`);
        const allEvents = res.data.events || [];

        // Filter events by selected relay if available
        if (selectedRelay) {
          const filtered = allEvents.filter(
            (e) =>
              e.fingerprint === selectedRelay.fingerprint.slice(0, 6) ||
              e.type === "relay"
          );
          setEvents(filtered.slice(0, 50));
        } else if (selectedPath) {
          // Filter events related to the path
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

  if (!selectedRelay && !selectedPath) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          <h2><Clock size={28} style={{marginRight: "10px", display: "inline", verticalAlign: "middle"}} />Timeline Reconstruction</h2>
          <p style={styles.emptyText}>
            No relay or path selected. Please select a relay from the Dashboard to view its timeline.
          </p>
          <button 
            style={styles.actionBtn}
            onClick={() => setCurrentTab("dashboard")}
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.explanationBanner}>
        <h2 style={{ margin: "0 0 8px 0" }}><Clock size={24} style={{marginRight: "10px", display: "inline", verticalAlign: "middle"}} />Timeline Reconstruction</h2>
        <p style={{ margin: "0", fontSize: "14px", color: "#cbd5e1" }}>
          Sequence of TOR network events and observations. Times are based on relay metadata from the TOR directory.
        </p>
      </div>

      {selectedRelay && (
        <div style={styles.selectedInfo}>
          <strong>Relay:</strong> {selectedRelay.nickname || selectedRelay.fingerprint.slice(0, 8)}
          {" | "}
          <strong>Country:</strong> {selectedRelay.country}
          {" | "}
          <strong>IP:</strong> {selectedRelay.ip}
        </div>
      )}

      {selectedPath && (
        <div style={styles.selectedInfo}>
          <strong>Path:</strong> {selectedPath.entry.nickname || selectedPath.entry.fingerprint.slice(0, 6)}
          {" → "}
          {selectedPath.middle.nickname || selectedPath.middle.fingerprint.slice(0, 6)}
          {" → "}
          {selectedPath.exit.nickname || selectedPath.exit.fingerprint.slice(0, 6)}
          {" | Score: "}
          {selectedPath.score.toFixed(4)}
        </div>
      )}

      {loading ? (
        <div style={styles.loading}>Loading timeline events...</div>
      ) : error ? (
        <div style={styles.error}>{error}</div>
      ) : events.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No timeline events found.</p>
        </div>
      ) : (
        <div style={styles.timelineList}>
          {events.map((event, idx) => (
            <div key={idx} style={styles.timelineItem}>
              <div style={styles.timelineDot} />
              <div style={styles.timelineContent}>
                <div style={styles.timelineHeader}>
                  <span style={styles.label}>{event.label}</span>
                  <span style={styles.timestamp}>{new Date(event.timestamp).toLocaleString()}</span>
                </div>
                <p style={styles.description}>{event.description}</p>
                {event.path_id && (
                  <div style={styles.pathInfo}>
                    <small>Path ID: {event.path_id.slice(0, 12)}...</small>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "900px",
  },
  explanationBanner: {
    background: "#1e293b",
    border: "1px solid #38bdf8",
    padding: "16px",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  selectedInfo: {
    background: "#0ea5e9",
    color: "#0f172a",
    padding: "12px 16px",
    borderRadius: "6px",
    marginBottom: "20px",
    fontWeight: "500",
    fontSize: "14px",
  },
  loading: {
    textAlign: "center",
    padding: "40px",
    color: "#94a3b8",
  },
  error: {
    background: "#7f1d1d",
    color: "#fecaca",
    padding: "16px",
    borderRadius: "6px",
    marginBottom: "20px",
  },
  emptyState: {
    background: "#1e293b",
    border: "1px solid #334155",
    padding: "40px",
    borderRadius: "8px",
    textAlign: "center",
    color: "#94a3b8",
  },
  emptyText: {
    margin: "12px 0",
    fontSize: "14px",
  },
  actionBtn: {
    background: "#0ea5e9",
    color: "#0f172a",
    border: "none",
    padding: "8px 16px",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "bold",
    marginTop: "16px",
  },
  timelineList: {
    position: "relative",
  },
  timelineItem: {
    display: "flex",
    gap: "20px",
    marginBottom: "24px",
    paddingLeft: "20px",
    borderLeft: "2px solid #38bdf8",
  },
  timelineDot: {
    width: "12px",
    height: "12px",
    background: "#38bdf8",
    borderRadius: "50%",
    marginTop: "6px",
    marginLeft: "-26px",
  },
  timelineContent: {
    flex: 1,
  },
  timelineHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  label: {
    background: "#0ea5e9",
    color: "#0f172a",
    padding: "4px 12px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "bold",
  },
  timestamp: {
    fontSize: "12px",
    color: "#94a3b8",
  },
  description: {
    margin: "8px 0",
    fontSize: "14px",
    color: "#e2e8f0",
    lineHeight: "1.5",
  },
  pathInfo: {
    marginTop: "8px",
    paddingTop: "8px",
    borderTop: "1px solid #334155",
    color: "#94a3b8",
  },
};
