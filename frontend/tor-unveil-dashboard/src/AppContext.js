// src/AppContext.js
import React, { createContext, useState, useCallback } from "react";

export const AppContext = createContext();

export function AppProvider({ children }) {
  const [currentTab, setCurrentTab] = useState("dashboard");
  const [selectedRelay, setSelectedRelay] = useState(null);
  const [selectedPath, setSelectedPath] = useState(null);

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
