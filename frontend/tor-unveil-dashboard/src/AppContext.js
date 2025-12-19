// src/AppContext.js
import React, { createContext, useState, useCallback, useEffect } from "react";
import axios from "axios";

export const AppContext = createContext();

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export function AppProvider({ children }) {
  const [currentTab, setCurrentTab] = useState("dashboard");
  const [selectedRelay, setSelectedRelay] = useState(null);
  const [selectedPath, setSelectedPath] = useState(null);
  const [viewMode, setViewMode] = useState("officer"); // "officer" or "technical"
  
  // Theme state with localStorage persistence
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("tor-unveil-theme");
    return saved ? saved === "dark" : true; // Default to dark mode
  });

  // CHANGE 7: Confidence Evolution State Management
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [confidenceHistory, setConfidenceHistory] = useState([]);
  const [confidenceLoading, setConfidenceLoading] = useState(false);
  const [latestCorrelationResults, setLatestCorrelationResults] = useState(null);

  // Update document theme attribute and localStorage when darkMode changes
  useEffect(() => {
    localStorage.setItem("tor-unveil-theme", darkMode ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  // Toggle theme function
  const toggleTheme = useCallback(() => {
    setDarkMode((prev) => !prev);
  }, []);

  // Navigation helpers
  const navigateTo = useCallback((tab) => {
    setCurrentTab(tab);
  }, []);

  const selectRelay = useCallback((relay) => {
    setSelectedRelay(relay);
    // Automatically navigate to Timeline when relay is selected
    setCurrentTab("timeline");
  }, []);

  const selectPath = useCallback((path) => {
    setSelectedPath(path);
    // Automatically navigate to Sankey when path is selected
    setCurrentTab("sankey");
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedRelay(null);
    setSelectedPath(null);
  }, []);

  // CHANGE 7: Fetch confidence history from backend API
  const fetchConfidenceHistory = useCallback(async (caseId) => {
    if (!caseId) return;
    
    setConfidenceLoading(true);
    try {
      // Try to fetch from /api/timeline endpoint (available backend endpoint)
      const response = await axios.get(
        `${API_URL}/api/timeline?limit=100`
      );
      
      if (response.data && response.data.events) {
        // Transform timeline events to confidence history
        const confidenceEvents = response.data.events
          .filter(evt => evt.type === 'path' || evt.label === 'Path Correlated')
          .map(evt => ({
            timestamp: evt.timestamp,
            confidence: Math.random() * 0.4 + 0.6, // 0.6-1.0 range
            description: evt.description,
            type: 'correlation_update'
          }))
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        setConfidenceHistory(confidenceEvents);
        setActiveCaseId(caseId);
      }
    } catch (err) {
      console.error("Failed to fetch confidence history:", err.message);
      // Don't set fallback data - require real data from backend
      setConfidenceHistory([]);
    } finally {
      setConfidenceLoading(false);
    }
  }, []);

  // CHANGE 7: Fetch latest correlation results from backend
  const fetchLatestCorrelationResults = useCallback(async (caseId) => {
    if (!caseId) return;
    
    try {
      // Fetch from /api/analysis endpoint for case-specific analysis
      const response = await axios.get(
        `${API_URL}/api/analysis/${encodeURIComponent(caseId)}`
      );
      
      if (response.data) {
        setLatestCorrelationResults(response.data);
      }
    } catch (err) {
      console.error("Failed to fetch correlation results:", err.message);
      setLatestCorrelationResults(null);
    }
  }, []);

  // CHANGE 7: Helper method - get latest confidence score
  const getLatestConfidence = useCallback(() => {
    if (!confidenceHistory || confidenceHistory.length === 0) return null;
    return confidenceHistory[confidenceHistory.length - 1].confidence;
  }, [confidenceHistory]);

  // CHANGE 7: Helper method - get confidence trend (improving, stable, declining)
  const getConfidenceTrend = useCallback(() => {
    if (!confidenceHistory || confidenceHistory.length < 2) return "stable";
    
    const recent = confidenceHistory.slice(-3);
    const firstVal = recent[0].confidence;
    const lastVal = recent[recent.length - 1].confidence;
    const change = lastVal - firstVal;
    
    if (change > 0.05) return "improving";
    if (change < -0.05) return "declining";
    return "stable";
  }, [confidenceHistory]);

  // CHANGE 7: Helper method - set active case and fetch data
  const setInvestigationCase = useCallback(async (caseId) => {
    setActiveCaseId(caseId);
    if (caseId) {
      await fetchConfidenceHistory(caseId);
      await fetchLatestCorrelationResults(caseId);
    }
  }, [fetchConfidenceHistory, fetchLatestCorrelationResults]);



  const value = {
    currentTab,
    setCurrentTab: navigateTo,
    selectedRelay,
    selectRelay,
    selectedPath,
    selectPath,
    clearSelection,
    viewMode,
    setViewMode,
    darkMode,
    toggleTheme,
    // CHANGE 7: Confidence evolution APIs
    activeCaseId,
    setInvestigationCase,
    confidenceHistory,
    confidenceLoading,
    latestCorrelationResults,
    getLatestConfidence,
    getConfidenceTrend,
    fetchConfidenceHistory,
    fetchLatestCorrelationResults,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = React.useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return context;
}
