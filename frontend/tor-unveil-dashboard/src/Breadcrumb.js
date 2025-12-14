/**
 * Breadcrumb.js - Investigation Context Navigation
 * 
 * Provides investigation context via breadcrumb trail:
 * Investigation → Analysis → Report
 * Helps users understand their position in the investigation workflow
 */

import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import "./Breadcrumb.css";

const Breadcrumb = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const breadcrumbs = [
    { label: "Investigation", path: "/investigation", icon: "home" },
    { label: "Dashboard", path: "/dashboard", icon: "dashboard" },
    { label: "TOR Analysis", path: "/analysis", icon: "analysis" },
    { label: "Forensics", path: "/forensic", icon: "forensic" },
    { label: "Reports", path: "/report", icon: "report" },
  ];

  // Filter breadcrumbs based on current location
  const activeBreadcrumbs = breadcrumbs.filter((crumb) => {
    const pathname = location.pathname;
    if (pathname === "/" || pathname === "/investigation") {
      return crumb.path === "/investigation";
    }
    return pathname.includes(crumb.path.replace("/", ""));
  });

  if (activeBreadcrumbs.length === 0) return null;

  return (
    <nav className="breadcrumb-container">
      <div className="breadcrumb-trail">
        {activeBreadcrumbs.map((crumb, index) => (
          <React.Fragment key={crumb.path}>
            {index > 0 && (
              <ChevronRight size={16} className="breadcrumb-separator" />
            )}
            <button
              className={`breadcrumb-item ${
                location.pathname === crumb.path ? "active" : ""
              }`}
              onClick={() => navigate(crumb.path)}
              title={`Navigate to ${crumb.label}`}
            >
              {index === 0 && <Home size={14} className="breadcrumb-icon" />}
              {crumb.label}
            </button>
          </React.Fragment>
        ))}
      </div>
    </nav>
  );
};

export default Breadcrumb;
