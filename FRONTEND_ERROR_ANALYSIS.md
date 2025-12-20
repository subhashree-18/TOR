# Frontend Error Analysis - Phase 2

## Executive Summary
Frontend has 5 critical issues preventing data display and user interaction. All can be fixed with backend route normalization and frontend API client refactoring.

## Issue 1: API Route Inconsistency

### Current Problem
Frontend calls:
```
GET /api/investigations           ✓ Has /api prefix
GET /api/investigations/{id}      ✓ Has /api prefix  
GET /relays                       ✗ NO /api prefix
GET /relays/map                   ✗ NO /api prefix
GET /risk/top                     ✗ NO /api prefix
GET /api/timeline                 ✓ Has /api prefix
```

Backend routes are split:
- **WITH /api prefix**: investigations, timeline, metadata, scoring-methodology
- **WITHOUT /api prefix**: relays, risk, paths, intel, analytics, forensic

### Why This Breaks
Frontend fetches fail with 404 for endpoints like `/api/relays` (backend has `/relays`)

### Solution
**Standardize ALL backend routes to use `/api/` prefix**

Routes to add `/api/` prefix:
1. `/relays` → `/api/relays`
2. `/relays/map` → `/api/relays/map`
3. `/relays/fetch` → `/api/relays/fetch`
4. `/risk/top` → `/api/risk/top`
5. `/intel/malicious` → `/api/intel/malicious`
6. `/analytics/india` → `/api/analytics/india`
7. `/paths/generate` → `/api/paths/generate`
8. `/paths/inference` → `/api/paths/inference`
9. `/paths/top` → `/api/paths/top`
10. `/relay/{fp}/timeline` → `/api/relay/{fp}/timeline`
11. `/forensic/upload` → `/api/forensic/upload`
12. `/export/report` → `/api/export/report`

Exempted (keep as-is, non-API):
- `/` (root)
- `/disclaimer` (legal)
- `/methodology` (legal)

---

## Issue 2: Missing Map Visualization

### Current Problem
**TorRelayMap.js** and **GeographicContextMap.js** components:
- Missing map provider (Leaflet, Mapbox, or Google Maps)
- No coordinates returned from backend
- No event handlers for interactivity

### Required Backend Data
```json
{
  "relays": [
    {
      "ip": "1.2.3.4",
      "country": "DE",
      "lat": 51.29,
      "lon": 9.49,
      "is_guard": true,
      "is_exit": false,
      "risk_score": 0.15
    }
  ]
}
```

### Solution
1. Add Leaflet.js to frontend (lightweight map library)
2. Verify `/api/relays/map` returns lat/lon coordinates
3. Wire up map click handlers to show relay details
4. Add country-level geo-visualization

---

## Issue 3: Investigation Page Non-Functional

### Current Problem
InvestigationPage.js expects:
```javascript
{
  "case_id": "TN/CYB/2024/001234",
  "hypotheses": [...],
  "tor_relays": [...],
  "analysis_metadata": {...}
}
```

Backend `/api/investigations/{case_id}` returns this, but:
- No UI components display the data
- Investigation object not properly structured
- No hypothesis comparison UI

### Solution
1. Create **HypothesisList** component to display rankings
2. Add **CorrelationVisualization** component for timing/overlap  
3. Wire backend data to UI components
4. Add confidence breakdown explanation

---

## Issue 4: State Management Issues

### Current Problem
- **No global state**: Data fetched in each component independently
- **No caching**: Same API calls repeated
- **No persistence**: Page refresh loses data
- **No context**: Components don't share investigation state

### Solution
Use React Context (already partially implemented in AppContext.js):
```javascript
<AppProvider>
  <InvestigationContext>
    <component />
  </InvestigationContext>
</AppProvider>
```

Store at AppContext:
- `currentCaseId`
- `currentInvestigation`
- `currentAnalysis`
- `selectedHypothesis`
- `mapData`

---

## Issue 5: Missing UI/UX Components

### Currently Missing
1. **Loading States**: No spinners, no "Loading..." text
2. **Error Handling**: No error messages to users
3. **Empty States**: No "No data" placeholders
4. **Breadcrumbs**: No navigation path shown (partially implemented)
5. **Data Tables**: Investigation list shows no table
6. **Charts**: Risk charts commented out

### Solution
Add components:
- `<LoadingSpinner />`
- `<ErrorAlert />`
- `<EmptyState />`
- `<HypothesisTable />`
- `<RiskChart />`

---

## Implementation Priority

### P0 (Critical - Blocks everything)
1. Fix backend `/api/` prefix inconsistency
2. Create unified API client (apiService.js)
3. Fix InvestigationPage data binding

### P1 (High - Core features)
4. Add map visualization
5. Implement proper state management
6. Add loading/error states

### P2 (Medium - Polish)
7. Add empty states
8. Add data tables
9. Add charts

---

## Affected Files

### Backend (main.py)
- Lines where routes defined: 224, 280, 375, 406, 439, 469, 563, 1009, 1082, 1243, 1294, 1322, 1613, 1763, 1831, 1873

### Frontend (src/)
- Dashboard.js: API calls at lines 48, 97, 131, 169
- AnalysisPage.js: API calls at lines 59
- InvestigationPage.js: API calls at lines 68, 123, 145
- App.js: API setup at line 35
- Components/TorRelayMap.js: Map code needs Leaflet

### New Components Needed
- apiService.js (unified API client)
- LoadingSpinner.js
- ErrorAlert.js
- HypothesisList.js
- HypothesisTable.js

---

## Testing Strategy

### API Tests
```bash
curl http://localhost:8000/api/relays
curl http://localhost:8000/api/relays/map
curl http://localhost:8000/api/investigations
```

### Frontend Tests
1. Dashboard loads and displays relay data
2. Investigation page shows hypotheses
3. Maps render with pins
4. Loading states appear during fetch
5. Error states appear on 500/404

---

## Success Criteria

✅ All `/api/` routes consistent
✅ Dasboard loads investigation list
✅ AnalysisPage displays hypotheses (not zeros)
✅ InvestigationPage shows relay correlations
✅ Maps display with geographic markers
✅ Loading states visible during data fetch
✅ Error messages show on API failures

