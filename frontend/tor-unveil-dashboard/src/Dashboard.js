import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Dashboard.css";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function Dashboard() {
  const [relays, setRelays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [countryData, setCountryData] = useState([]);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(`${API_URL}/relays?limit=1000`);
      const data = response.data?.data || [];
      setRelays(data);

      if (!data.length) throw new Error("No relay data received");

      // build country count chart
      const counts = {};
      data.forEach((relay) => {
        const c = relay.country || "Unknown";
        counts[c] = (counts[c] || 0) + 1;
      });

      const formatted = Object.keys(counts)
        .map((c) => ({ country: c, count: counts[c] }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

      setCountryData(formatted);
    } catch (err) {
      console.error("Error loading data:", err);
      setError("Failed to load data from backend");
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    try {
      await axios.get(`${API_URL}/relays/fetch`);
      await loadData();
    } catch (err) {
      setError("Failed to refresh TOR data");
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="container">
      <header>
        <h1>🧅 TOR Unveil Visualization Dashboard</h1>
        <button className="refresh-btn" onClick={refresh}>🔄 Refresh</button>
      </header>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <h2>Total Relays: {relays.length}</h2>

          <section className="chart-section">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={countryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="country" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#1e90ff" />
              </BarChart>
            </ResponsiveContainer>
          </section>

          <section className="table-section">
            <h3>Relay List (Top 20)</h3>
            <table>
              <thead>
                <tr>
                  <th>Fingerprint</th>
                  <th>Country</th>
                  <th>Flags</th>
                </tr>
              </thead>
              <tbody>
                {relays.slice(0, 20).map((relay, i) => (
                  <tr key={i}>
                    <td>{relay.fingerprint}</td>
                    <td>{relay.country}</td>
                    <td>{relay.flags.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  );
}
