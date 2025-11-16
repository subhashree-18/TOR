// src/App.js
import React, { useState } from "react";
import Dashboard from "./Dashboard";
import PathsDashboard from "./PathsDashboard";
import Timeline from "./Timeline";
import SankeyChart from "./SankeyChart";

export default function App() {
  const [tab, setTab] = useState("dashboard");

  return (
    <div>
      <nav style={styles.nav}>
        <button style={styles.btn} onClick={() => setTab("dashboard")}>
          🧅 Dashboard
        </button>
        <button style={styles.btn} onClick={() => setTab("paths")}>
          🔀 Paths
        </button>
        <button style={styles.btn} onClick={() => setTab("timeline")}>
          ⏳ Timeline
        </button>
        <button style={styles.btn} onClick={() => setTab("sankey")}>
          📊 Sankey
        </button>
      </nav>

      <div style={{ padding: 20 }}>
        {tab === "dashboard" && <Dashboard />}
        {tab === "paths" && <PathsDashboard />}
        {tab === "timeline" && <Timeline fingerprint="000A10D43011EA4928A35F610405F92B4433B4DC" />}
        {tab === "sankey" && <SankeyChart paths={[]} />}
      </div>
    </div>
  );
}

const styles = {
  nav: {
    display: "flex",
    gap: "12px",
    padding: "12px",
    background: "#222",
  },
  btn: {
    background: "#00bfff",
    color: "white",
    border: "none",
    padding: "8px 12px",
    borderRadius: "5px",
    cursor: "pointer",
  },
};
