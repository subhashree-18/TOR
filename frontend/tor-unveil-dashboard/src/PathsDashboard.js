// src/PathsDashboard.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import SankeyChart from "./SankeyChart";
import Timeline from "./Timeline";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function PathsDashboard() {
  const [paths, setPaths] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadPaths() {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/paths/top?limit=50`);
      setPaths(res.data.paths || []);
    } catch (err) {
      console.error(err);
      alert("Failed to load paths");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPaths();
  }, []);

  return (
    <div style={{ padding: 15 }}>
      <h2>🔀 TOR Path Analysis</h2>
      <button onClick={loadPaths}>Refresh</button>
      <p>Total: {paths.length}</p>

      {loading && <p>Loading...</p>}

      <div style={{ display: "flex", gap: 20 }}>
        {/* TABLE */}
        <table style={styles.table}>
          <thead>
            <tr>
              <th>Entry</th>
              <th>Middle</th>
              <th>Exit</th>
              <th>Score</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {paths.map((p) => (
              <tr key={p.id}>
                <td>{p.entry.fingerprint.slice(0, 8)}</td>
                <td>{p.middle.fingerprint.slice(0, 8)}</td>
                <td>{p.exit.fingerprint.slice(0, 8)}</td>
                <td>{p.score.toFixed(3)}</td>
                <td>
                  <button onClick={() => setSelected(p)}>Inspect</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* RIGHT PANE */}
        <div style={{ flex: 1 }}>
          <h3>Sankey</h3>
          <SankeyChart paths={paths.slice(0, 20)} />

          <h3>Selected Path</h3>

          {selected ? (
            <>
              <pre style={styles.json}>
                {JSON.stringify(selected, null, 2)}
              </pre>

              <h4>Entry Timeline</h4>
              <Timeline fingerprint={selected.entry.fingerprint} />

              <h4>Exit Timeline</h4>
              <Timeline fingerprint={selected.exit.fingerprint} />
            </>
          ) : (
            <div>Select a row to inspect</div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  table: {
    borderCollapse: "collapse",
    width: "50%",
    fontSize: 12,
    color: "#fff",
    background: "#0b1622",
  },
  json: {
  fontSize: 12,
  background: "#0f172a",
  color: "#f0f9ff",
  border: "1px solid #334155",
  padding: 10,
  borderRadius: 6,
  overflowX: "auto",
},

};