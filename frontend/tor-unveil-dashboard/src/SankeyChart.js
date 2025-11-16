import React, { useEffect, useState } from "react";
import axios from "axios";
import SankeyChart from "./SankeyChart";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function SankeyPage() {
  const [paths, setPaths] = useState([]);

  useEffect(() => {
    async function load() {
      const res = await axios.get(`${API_URL}/paths/top?limit=50`);
      setPaths(res.data.paths || []);
    }
    load();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2>Sankey Path Visualization</h2>
      <SankeyChart paths={paths} />
    </div>
  );
}
