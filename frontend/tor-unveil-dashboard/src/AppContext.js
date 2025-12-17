// src/AppContext.js
import React, { createContext, useState, useCallback, useEffect } from "react";

export const AppContext = createContext();

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
