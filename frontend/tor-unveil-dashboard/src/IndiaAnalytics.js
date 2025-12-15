// src/IndiaAnalytics.js
import React, { useEffect, useState } from "react";
import axios from "axios";
import { AlertCircle, TrendingUp, Globe } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import "./IndiaAnalytics.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function IndiaAnalytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indianData, setIndianData] = useState(null);
  const [overallStats, setOverallStats] = useState(null);

  useEffect(() => {
    const loadIndiaData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch India-specific analytics
        const indiaRes = await axios.get(`${API_URL}/analytics/india`);
        const data = indiaRes.data;

        setIndianData({
          total_indian_relays: data.indian_relays?.count || 0,
          asn_distribution: extractAsnDistribution(data.indian_asn_involvement?.relays || []),
          paths_with_india: data.paths_involving_india?.count || 0,
          high_confidence_paths: data.paths_involving_india?.high_confidence || 0,
        });

        setOverallStats({
          total: data.total_relays_indexed || 0,
          india: data.indian_relays?.count || 0,
          foreign: data.infrastructure_split?.foreign?.count || 0,
          indianPercent: data.indian_relays?.percentage || 0,
        });
      } catch (err) {
        console.error("Error loading India data:", err);
        setError("Failed to load India analytics");
      } finally {
        setLoading(false);
      }
    };

    const extractAsnDistribution = (relays) => {
      const asnMap = {};
      relays.forEach((relay) => {
        const asn = relay.as || "Unknown ASN";
        asnMap[asn] = (asnMap[asn] || 0) + 1;
      });
      return asnMap;
    };

    loadIndiaData();
  }, []);

  if (loading) {
    return (
      <div className="india-analytics-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading India-specific analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="india-analytics-container">
        <div className="error-banner">
          <AlertCircle size={20} style={{ marginRight: "8px" }} />
          {error}
        </div>
      </div>
    );
  }

  const splitData = overallStats ? [
    { name: "India (IN)", value: overallStats.india, fill: "#ef4444" },
    { name: "Rest of World", value: overallStats.foreign, fill: "#0ea5e9" },
  ] : [];

  return (
    <div className="india-analytics-container">
      <div className="explanation-banner">
        <h2>India-Focused TOR Analysis</h2>
        <p>
          <strong>Purpose:</strong> Specialized analysis of TOR relay infrastructure 
          within India, including ASN distribution, domestic vs. foreign infrastructure, 
          and regional risk assessment.
        </p>
      </div>

      <header className="analytics-header">
        <h1>India-Specific TOR Investigation</h1>
        <p>Detailed breakdown of Indian relay participation in TOR network</p>
      </header>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: "#ef4444" }}>
            <Globe size={24} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-label">Indian Relays</div>
            <div className="stat-value">{overallStats?.india || 0}</div>
            <div className="stat-detail">
              {overallStats?.indianPercent}% of total network
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: "#0ea5e9" }}>
            <Globe size={24} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-label">Foreign Relays</div>
            <div className="stat-value">{overallStats?.foreign || 0}</div>
            <div className="stat-detail">
              {((overallStats?.foreign || 0) / (overallStats?.total || 1) * 100).toFixed(1)}% of total network
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: "#f59e0b" }}>
            <TrendingUp size={24} color="white" />
          </div>
          <div className="stat-content">
            <div className="stat-label">Total Relays</div>
            <div className="stat-value">{overallStats?.total || 0}</div>
            <div className="stat-detail">Indexed TOR network relays</div>
          </div>
        </div>
      </div>

      {/* Split Visualization */}
      {splitData.length > 0 && (
        <div className="section">
          <div className="section-header">
            <h3 className="section-title">Domestic vs. Foreign Infrastructure Split</h3>
            <p className="section-description">
              Proportion of TOR relays hosted within India versus international infrastructure.
            </p>
          </div>
          <div className="chart-container-split">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={splitData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {splitData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Indian Analytics Detail Section */}
      {indianData && (
        <div className="section">
          <div className="section-header">
            <h3 className="section-title">Indian ASN & Infrastructure Analysis</h3>
            <p className="section-description">
              Autonomous System Numbers (ASNs) hosting TOR relays within India.
            </p>
          </div>
          <div className="indian-data-content">
            {indianData.asn_distribution && Object.keys(indianData.asn_distribution).length > 0 ? (
              <div className="asn-list">
                <table className="asn-table">
                  <thead>
                    <tr>
                      <th>ASN/Provider</th>
                      <th>Relay Count</th>
                      <th>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(indianData.asn_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .map(([asn, count], idx) => {
                        const percent = indianData.total_indian_relays > 0 
                          ? ((count / indianData.total_indian_relays) * 100).toFixed(1)
                          : 0;
                        return (
                          <tr key={`asn-${idx}`}>
                            <td className="asn-name">{asn || "Unknown"}</td>
                            <td className="asn-count">{count}</td>
                            <td className="asn-percent">{percent}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-section">
                <p>No ASN distribution data available</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Investigation Recommendations */}
      <div className="section">
        <div className="section-header">
          <h3 className="section-title">Investigation Recommendations</h3>
        </div>
        <div className="recommendations">
          <div className="recommendation-item">
            <div className="recommendation-icon">🔍</div>
            <div className="recommendation-content">
              <h4>Domestic Infrastructure Focus</h4>
              <p>
                When investigating Indian connections, prioritize relays hosted within India's 
                ASN space for more direct forensic correlation.
              </p>
            </div>
          </div>
          <div className="recommendation-item">
            <div className="recommendation-icon">⚠️</div>
            <div className="recommendation-content">
              <h4>Cross-Border Routing</h4>
              <p>
                Many Indian TOR users may route through foreign exit nodes for anonymity. 
                Monitor both entry and exit patterns.
              </p>
            </div>
          </div>
          <div className="recommendation-item">
            <div className="recommendation-icon">📊</div>
            <div className="recommendation-content">
              <h4>ASN-Based Tracking</h4>
              <p>
                Use ASN distribution data to identify major hosting providers and potential 
                policy enforcement points.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-description">
          <AlertCircle size={16} style={{ marginRight: "8px", display: "inline" }} />
          <strong>Disclaimer:</strong> This analysis is for authorized law enforcement and 
          investigative purposes only. All data collection and usage must comply with applicable 
          privacy laws and regulations.
        </div>
      </div>
    </div>
  );
}
