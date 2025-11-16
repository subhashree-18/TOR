import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function Timeline({ fingerprint }) {
  const [relay, setRelay] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/relay/${fingerprint}/timeline`);
      setRelay(res.data.relay);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [fingerprint]);

  if (loading) return <p>Loading timeline...</p>;
  if (!relay) return <p>No timeline data found.</p>;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h3>{relay.nickname}</h3>
        <p><b>IP:</b> {relay.ip}</p>
        <p><b>Country:</b> {relay.country}</p>
        <p><b>First Seen:</b> {relay.first_seen}</p>
        <p><b>Last Seen:</b> {relay.last_seen}</p>

        <div style={styles.bar}>
          <div
            style={{ ...styles.innerBar, width: `${relay.advertised_bandwidth / 20000}%` }}
          ></div>
        </div>
      </div>

      <div style={styles.card}>
        <h3>Middle Node</h3>
        <p>Coming soon</p>
      </div>

      <div style={styles.card}>
        <h3>Exit Node</h3>
        <p>Coming soon</p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    gap: 20,
  },
  card: {
    background: "#e2e8f0",
    color: "#0f172a",
    padding: 20,
    width: "30%",
    borderRadius: 10,
  },
  bar: {
    height: 8,
    background: "#cbd5e1",
    marginTop: 10,
    borderRadius: 5,
  },
  innerBar: {
    height: "100%",
    background: "#38bdf8",
    borderRadius: 5,
  },
};
