// frontend/src/PathsDashboard.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import SankeyChart from "./SankeyChart";
import Timeline from "./Timeline";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function PathsDashboard() {
  const [paths, setPaths] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPath, setSelectedPath] = useState(null);

  const loadTopPaths = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/paths/top?limit=100`);
      setPaths(res.data.paths || []);
    } catch (err) {
      console.error("Error loading top paths", err);
      alert("Failed to load paths");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTopPaths();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2>Top plausible TOR paths</h2>
      <button onClick={loadTopPaths}>Refresh</button>
      <p>Total paths: {paths.length}</p>

      <div style={{ display: "flex", gap: 20 }}>
        <div style={{ flex: 1 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th>Entry</th>
                <th>Middle</th>
                <th>Exit</th>
                <th>Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {paths.map((p) => (
                <tr key={p.id}>
                  <td title={p.entry.nickname}>{p.entry.fingerprint}</td>
                  <td title={p.middle.nickname}>{p.middle.fingerprint}</td>
                  <td title={p.exit.nickname}>{p.exit.fingerprint}</td>
                  <td>{p.score}</td>
                  <td>
                    <button onClick={() => setSelectedPath(p)}>Inspect</button>
                    <a style={{ marginLeft: 8 }} href={`${API_URL}/export/report?path_id=${p.id}`} target="_blank" rel="noreferrer">PDF</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ flex: 1 }}>
          <h3>Visualization (Sankey)</h3>
          <SankeyChart paths={paths.slice(0, 50)} />
          <h3>Selected Path</h3>
          {selectedPath ? (
            <>
              <pre style={{ fontSize: 12 }}>{JSON.stringify(selectedPath, null, 2)}</pre>
              <h4>Timeline (entry)</h4>
              <Timeline fingerprint={selectedPath.entry.fingerprint} />
              <h4>Timeline (exit)</h4>
              <Timeline fingerprint={selectedPath.exit.fingerprint} />
            </>
          ) : (
            <div>Select a path to inspect</div>
          )}
        </div>
      </div>
    </div>
  );
}
