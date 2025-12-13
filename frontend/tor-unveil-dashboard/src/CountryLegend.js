/**
 * CountryLegend.js - Full Country Name Display with Tooltips
 * 
 * Shows full country names for abbreviations used in charts
 * Provides hover tooltips and searchable legend
 */

import React, { useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import "./CountryLegend.css";

// Complete country mapping for tooltips
const COUNTRY_MAP = {
  US: "United States",
  GB: "United Kingdom",
  DE: "Germany",
  FR: "France",
  NL: "Netherlands",
  CA: "Canada",
  AU: "Australia",
  JP: "Japan",
  CH: "Switzerland",
  SE: "Sweden",
  NO: "Norway",
  DK: "Denmark",
  FI: "Finland",
  AT: "Austria",
  BE: "Belgium",
  IT: "Italy",
  ES: "Spain",
  PT: "Portugal",
  GR: "Greece",
  RO: "Romania",
  PL: "Poland",
  CZ: "Czechia",
  HU: "Hungary",
  IE: "Ireland",
  IN: "India",
  BR: "Brazil",
  RU: "Russia",
  CN: "China",
  SG: "Singapore",
  HK: "Hong Kong",
  KR: "South Korea",
  MX: "Mexico",
  ZA: "South Africa",
  NZ: "New Zealand",
  MY: "Malaysia",
  TH: "Thailand",
  ID: "Indonesia",
  VN: "Vietnam",
  PH: "Philippines",
  TR: "Turkey",
  IL: "Israel",
  AE: "United Arab Emirates",
  SA: "Saudi Arabia",
  ZZ: "Unknown",
};

export default function CountryLegend({ countryData = [], isExpanded = false }) {
  const [expanded, setExpanded] = useState(isExpanded);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredCountries = countryData.filter((item) => {
    const fullName = COUNTRY_MAP[item.country] || item.country;
    return (
      fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.country.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="country-legend-container">
      <button
        className="country-legend-header"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="legend-title">
          📍 Country Reference ({countryData.length} countries)
        </span>
        <ChevronDown
          size={18}
          className={`legend-chevron ${expanded ? "expanded" : ""}`}
        />
      </button>

      {expanded && (
        <div className="country-legend-content">
          <div className="legend-search">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search country..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="legend-grid">
            {filteredCountries.map((item) => {
              const fullName = COUNTRY_MAP[item.country] || item.country;
              return (
                <div key={item.country} className="legend-item">
                  <div className="legend-item-code">{item.country}</div>
                  <div className="legend-item-info">
                    <div className="legend-item-name">{fullName}</div>
                    <div className="legend-item-count">{item.count} relays</div>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredCountries.length === 0 && (
            <div className="legend-empty">No countries match "{searchTerm}"</div>
          )}
        </div>
      )}
    </div>
  );
}
