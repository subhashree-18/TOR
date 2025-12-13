// src/SankeyPage.js
import React from "react";
import { BarChart2 } from "lucide-react";
import { useAppContext } from "./AppContext";
import SankeyChart from "./SankeyChart";

export default function SankeyPage() {
  const { selectedPath, setCurrentTab } = useAppContext();

  if (!selectedPath) {
    return (
      <div style={styles.container}>
        <div style={styles.explanationBanner}>
          <h2 style={{ margin: "0 0 8px 0" }}><BarChart2 size={24} style={{marginRight: "8px", display: "inline-block", verticalAlign: "middle"}} />TOR Flow Visualization</h2>
          <p style={{ margin: "0", fontSize: "14px", color: "#cbd5e1" }}>
            Visual flow of probable TOR connection paths through network nodes.
          </p>
        </div>

        <div style={styles.emptyState}>
          <h3>No Path Selected</h3>
          <p style={styles.emptyText}>
            Select a path to visualize its entry → middle → exit flow.
          </p>
          <button 
            style={styles.actionBtn}
            onClick={() => setCurrentTab("paths")}
          >
            ← Back to Paths
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.explanationBanner}>
        <h2 style={{ margin: "0 0 8px 0" }}><BarChart2 size={24} style={{marginRight: "8px", display: "inline-block", verticalAlign: "middle"}} />TOR Flow Visualization</h2>
        <p style={{ margin: "0", fontSize: "14px", color: "#cbd5e1" }}>
          Visual representation of the selected path: entry node → middle relay → exit node.
        </p>
      </div>

      <div style={styles.selectedInfo}>
        <strong>Entry:</strong> {selectedPath.entry.nickname || selectedPath.entry.fingerprint.slice(0, 8)}
        {" ("}{selectedPath.entry.country}{")"}
        <br />
        <strong>Middle:</strong> {selectedPath.middle.nickname || selectedPath.middle.fingerprint.slice(0, 8)}
        {" ("}{selectedPath.middle.country}{")"}
        <br />
        <strong>Exit:</strong> {selectedPath.exit.nickname || selectedPath.exit.fingerprint.slice(0, 8)}
        {" ("}{selectedPath.exit.country}{")"}
        <br />
        <strong>Plausibility Score:</strong> {selectedPath.score.toFixed(4)} / 1.0
      </div>

      <div style={styles.scoreBreakdown}>
        <h4 style={{ marginTop: 0 }}>Score Components</h4>
        {selectedPath.components && (
          <div style={styles.componentsList}>
            {Object.entries(selectedPath.components).map(([key, value]) => (
              <div key={key} style={styles.componentRow}>
                <span style={styles.componentLabel}>{key}:</span>
                <span style={styles.componentValue}>{typeof value === 'number' ? value.toFixed(3) : value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={styles.chartContainer}>
        <SankeyChart paths={[selectedPath]} />
      </div>

      <div style={styles.explanation}>
        <h4>How to read this flow:</h4>
        <ul style={styles.explanationList}>
          <li><strong>Entry Node:</strong> Where your connection originates into the TOR network</li>
          <li><strong>Middle Relay:</strong> An intermediate node that routes traffic</li>
          <li><strong>Exit Node:</strong> Where the connection emerges from TOR to the destination</li>
          <li><strong>Score:</strong> Plausibility metric based on uptime overlap, bandwidth, and network diversity</li>
        </ul>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "1000px",
  },
  explanationBanner: {
    background: "#1e293b",
    border: "1px solid #38bdf8",
    padding: "16px",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  selectedInfo: {
    background: "#1e293b",
    border: "1px solid #38bdf8",
    padding: "16px",
    borderRadius: "8px",
    marginBottom: "20px",
    fontSize: "14px",
    lineHeight: "1.8",
    fontFamily: "monospace",
  },
  scoreBreakdown: {
    background: "#1e293b",
    border: "1px solid #38bdf8",
    padding: "16px",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  componentsList: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  componentRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "8px",
    background: "#0f172a",
    borderRadius: "4px",
    fontSize: "13px",
  },
  componentLabel: {
    color: "#94a3b8",
    fontWeight: "bold",
  },
  componentValue: {
    color: "#38bdf8",
  },
  chartContainer: {
    marginBottom: "24px",
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
  explanation: {
    background: "#1e293b",
    border: "1px solid #38bdf8",
    padding: "16px",
    borderRadius: "8px",
    marginTop: "24px",
  },
  explanationList: {
    margin: "8px 0",
    paddingLeft: "20px",
  },
};
