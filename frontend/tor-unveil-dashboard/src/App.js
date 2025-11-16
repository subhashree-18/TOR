// src/App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

import Dashboard from "./Dashboard";
import PathsDashboard from "./PathsDashboard";
import Timeline from "./Timeline";
import SankeyChart from "./SankeyChart";

export default function App() {
  return (
    <Router>
      <nav style={{ padding: 15, background: "#f0f0f0" }}>
        <Link to="/" style={{ marginRight: 20 }}>Dashboard</Link>
        <Link to="/paths" style={{ marginRight: 20 }}>Paths Dashboard</Link>
        <Link to="/timeline" style={{ marginRight: 20 }}>Timeline</Link>
        <Link to="/sankey" style={{ marginRight: 20 }}>Sankey Chart</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/paths" element={<PathsDashboard />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/sankey" element={<SankeyChart />} />
      </Routes>
    </Router>
  );
}
