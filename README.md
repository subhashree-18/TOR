# TOR Unveil: Forensic TOR Network Analysis for Law Enforcement

## 🎯 Overview

**TOR Unveil** is a forensic investigation tool designed to help law enforcement identify probable TOR network routing paths through temporal and network-topology correlation analysis. This tool assists cybercrime investigators in understanding potential communication patterns without breaking TOR's anonymity protections.

### Purpose
- **Investigative Support**: Correlate TOR relay metadata to identify probable network paths
- **Plausibility Analysis**: Score path likelihood based on timing, geography, and network topology
- **Forensic Transparency**: Provide explainable, reproducible scoring with full methodology documentation
- **Legal Compliance**: Operate strictly within legal and ethical boundaries

### Critical Disclaimer
⚠️ **Results express PLAUSIBILITY only, NOT proof.** All findings must be validated through independent investigative methods. This tool does NOT break TOR anonymity or compromise TOR users.

---

## ❌ What This System Does NOT Do

| Claim | Status |
|-------|--------|
| Break TOR encryption or anonymity | ❌ NOT PERFORMED |
| Identify actual TOR users | ❌ NOT PERFORMED |
| Perform packet inspection or traffic analysis | ❌ NOT PERFORMED |
| Deanonymize TOR network participants | ❌ NOT PERFORMED |
| Provide definitive proof of user identity | ❌ NOT PERFORMED |
| Bypass legal authorization requirements | ❌ NOT PERFORMED |

This tool is **metadata-only analysis**. It uses publicly-available TOR network topology data (Onionoo directory, relay uptime windows, geolocation data) to correlate path plausibility. No user traffic, encryption keys, or private data is processed.

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- **Docker & Docker Compose**: [Install](https://docs.docker.com/get-docker/)
- **Git**: For cloning the repository
- **Linux/macOS/Windows with WSL2**: Recommended

### Installation & Launch

```bash
# Clone repository
git clone <repository-url>
cd tor-unveil

# Start all services
docker compose -f infra/docker-compose.yml up -d --build

# Wait for services to start (10-15 seconds)
sleep 15

# Open in browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Stop Services
```bash
docker compose -f infra/docker-compose.yml down
```

### Remove All Data
```bash
docker compose -f infra/docker-compose.yml down -v
```

---

## 📊 Investigation Flow (5 Steps)

TOR Unveil guides investigators through a structured workflow:

```
1. CREATE CASE
   ↓
   Enter case ID, officer name, and timestamps
   for the TOR activity you're investigating

2. FETCH TOR DATA
   ↓
   System fetches live TOR network metadata
   from Onionoo directory (public data)

3. CORRELATE PATHS
   ↓
   Analyzes which relay combinations were
   online during your timestamp window

4. SCORE PATHS
   ↓
   Rates path plausibility (30-95% range)
   based on network topology and geography

5. GENERATE REPORT
   ↓
   Export professional PDF report with
   scores, methodology, and legal disclaimers
```

**Each step includes audit trail logging for legal transparency.**

---

## 🎬 Demo Walkthrough (5 Steps)

After launching the system, here's a quick walkthrough:

### Step 1: Enter Investigation Details
```
URL: http://localhost:3000/investigation
- Enter a Case ID (e.g., "CASE-2025-001234")
- Enter your Officer Name
- System auto-records timestamp
```

### Step 2: View TOR Network Overview
```
URL: http://localhost:3000/dashboard
- See geographic distribution of TOR relays
- View top countries hosting relays
- Identify Indian network infrastructure (if applicable)
```

### Step 3: Explore Probable Paths
```
URL: http://localhost:3000/paths
- View candidate TOR paths with plausibility scores
- Click path row to expand details (entry/middle/exit relays)
- See scoring breakdown (uptime, bandwidth, geography)
```

### Step 4: Analyze with Sankey Visualization
```
URL: http://localhost:3000/analysis
- See merged timeline + flow chart
- Understand path structure visually
- Review confidence badges and country context
```

### Step 5: Generate Professional Report
```
URL: http://localhost:3000/report
- Export as PDF (professionally formatted)
- Export as JSON (machine-readable)
- Export as CSV (spreadsheet-compatible)
- All reports include legal disclaimers & IPC compliance
```

---

## 📋 System Architecture

### Technology Stack
```
Frontend:  React 19 + React Router 7 + Recharts + lucide-react
Backend:   FastAPI + MongoDB 7
Database:  MongoDB 7.0 (TOR relay metadata + correlation results)
Deployment: Docker Compose (3 containers)
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | React UI for investigators |
| **Backend API** | 8000 | FastAPI endpoints for data & analysis |
| **MongoDB** | 27017 | Relay metadata & correlation storage |

### Data Flow
```
1. Dashboard → Load 10K+ TOR relays from MongoDB
2. Paths → Fetch pre-calculated path scores (max 85%)
3. Analysis → Display timeline events + Sankey visualization
4. Report → Export findings as Text/JSON/CSV
```

---

## 🎮 User Interface Guide

### 1. Dashboard (`/dashboard`)
**What**: Overview of TOR network relays and geographic distribution
- **Relay Table**: List of 1000+ relays with fingerprints, countries, bandwidth
- **Copy Function**: Click fingerprint to copy full ID to clipboard
- **Country Chart**: Top 10 countries by relay count
- **Selection**: Click relay row to select for analysis

### 2. Paths (`/paths`)
**What**: Probable TOR routing paths identified through correlation
- **Path List**: Entry → Middle → Exit nodes with plausibility scores
- **Confidence Levels**: 
  - 🟢 **HIGH**: ≥80% (trusted, strong evidence)
  - 🟡 **MEDIUM**: 50-79% (possible, investigate further)
  - 🔴 **LOW**: <50% (unlikely but noted)
- **Expandable Rows**: Click to see full path details + scoring breakdown
- **Scoring Show**: Click "Scoring Methodology" to see how scores calculated
- **Full Fingerprints**: All node IDs shown with copy buttons

### 3. Analysis (`/analysis`)
**What**: Deep analysis of selected relay or path
- **Timeline Tab**: Chronological events for investigation
- **Flow Visualization Tab**: Sankey diagram showing path flow
  - 🔵 Blue = Entry node (connection enters TOR)
  - 🟠 Amber = Middle node (intermediate relay)
  - 🔴 Red = Exit node (connection leaves TOR)
- **Score Breakdown**: Component analysis with methodology explanation

### 4. Report (`/report`)
**What**: Export investigation findings
- **Export Formats**:
  - 📄 **Text**: Human-readable forensic report
  - 📄 **JSON**: Machine-readable structured data
  - 📊 **CSV**: Spreadsheet-compatible format
- **Includes**: Timestamp, full metadata, scoring methodology, disclaimers
- **Download**: Right-click → Save as for local storage

---

## 📊 Scoring Methodology

### Score Calculation

```
Final Score = (0.50 × Uptime + 0.25 × Bandwidth + 0.25 × Role)
            × AS_Penalty × Country_Penalty
            
Capped at: 85% maximum
Range: 0% - 85%
```

### Components

| Component | Value | Meaning |
|-----------|-------|---------|
| **Uptime Score** | 0-100% | Overlap of relay uptime in 7-day window |
| **Bandwidth Score** | 0-100% | Normalized relay bandwidth capacity |
| **Role Score** | 0-100% | Quality of relay flags (Guard, Exit, etc.) |
| **AS Penalty** | 0.70x | If entry & exit same Autonomous System |
| **Country Penalty** | 0.60x | If entry & exit same country |
| **Score Cap** | 85% max | Prevents unrealistic confidence claims |

### Confidence Mapping

- **HIGH (≥80%)**: Strong temporal alignment + geographic diversity + good flags
- **MEDIUM (≥50%)**: Moderate alignment with some penalizing factors
- **LOW (<50%)**: Weak correlation or multiple penalizing factors

### Why 7-Day Window?
TOR relays operate continuously, but the 7-day uptime window reflects realistic timing windows for correlation analysis. Longer windows (e.g., 30 days) create false positives by including relays that are always online.

### Why Penalties?
- **AS Penalty (0.70x)**: Same Autonomous System = potential shared infrastructure = lower path diversity
- **Country Penalty (0.60x)**: Same country = reduced geographic anonymity protection
- **Score Cap (85%)**: Acknowledges inherent uncertainty in metadata-only analysis

---

## 🔌 API Endpoints

### GET `/relays`
Fetch TOR relay data
```bash
curl http://localhost:8000/relays?limit=100
```
**Response**: Array of relay objects with fingerprint, nickname, country, bandwidth, AS info

### GET `/paths/top`
Fetch highest-scoring correlated paths
```bash
curl http://localhost:8000/paths/top?limit=50
```
**Response**: Array of path objects with entry/middle/exit nodes + score components

### GET `/paths/generate`
Regenerate all path correlations (long-running)
```bash
curl http://localhost:8000/paths/generate
```
**Response**: Generation status + count of paths created

### GET `/api/timeline`
Fetch timeline events for visualization
```bash
curl http://localhost:8000/api/timeline?limit=100
```
**Response**: Array of chronological events

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in root directory (optional):

```env
# Backend
MONGO_URI=mongodb://localhost:27017
API_PORT=8000
BATCH_SIZE=1000
LOG_LEVEL=INFO

# Frontend
REACT_APP_API_URL=http://127.0.0.1:8000
```

### Docker Compose Override

Edit `infra/docker-compose.yml` to customize:
- Port mappings
- Memory limits
- MongoDB persistence
- Environment variables

---

## 📦 Deployment Guide

### For Tamil Nadu Police Servers

#### Step 1: Prerequisites
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
sudo usermod -aG docker $USER
```

#### Step 2: Clone & Configure
```bash
cd /opt
sudo git clone <repo-url> tor-unveil
cd tor-unveil
sudo cp .env.example .env.prod
sudo nano .env.prod  # Edit for production
```

#### Step 3: Launch Services
```bash
sudo docker compose -f infra/docker-compose.yml -p tor-unveil-prod up -d
```

#### Step 4: Verify Deployment
```bash
sudo docker ps --filter name=torunveil
curl http://localhost:3000  # Check frontend
curl http://localhost:8000/relays?limit=1  # Check backend
```

#### Step 5: Data Persistence
```bash
# Backup MongoDB data
sudo docker compose -f infra/docker-compose.yml exec mongo mongodump --out /backups

# Restore from backup
sudo docker compose -f infra/docker-compose.yml exec mongo mongorestore /backups
```

### Security Recommendations

1. **Network Isolation**: Run on isolated network segment
2. **Firewall Rules**: Restrict access to ports 3000, 8000, 27017
3. **HTTPS**: Use reverse proxy (nginx) for HTTPS
4. **Authentication**: Implement password protection at reverse proxy
5. **Audit Logging**: Enable MongoDB audit logs for compliance
6. **Data Retention**: Define policy for old investigation data

---

## 🧪 Testing & Validation

### Manual Testing Workflow

```bash
# 1. Access Frontend
open http://localhost:3000

# 2. Navigate Dashboard
# - Should load 1000+ relays
# - Select any relay
# - Verify fingerprint visible and copyable

# 3. Navigate Paths
# - Should show 100+ paths
# - Each path shows entry→middle→exit
# - Scores should be 0-85% range
# - Expand a row to see full details

# 4. Navigate Analysis
# - Select a path first (from Paths page)
# - Timeline tab should show events
# - Flow tab should show Sankey with colored nodes

# 5. Navigate Report
# - Select relay or path
# - Export Text/JSON/CSV
# - Verify downloads contain correct data

# 6. Test APIs
curl http://localhost:8000/relays?limit=1 | jq
curl http://localhost:8000/paths/top?limit=1 | jq '.paths[0].score'
curl http://localhost:8000/api/timeline?limit=10 | jq '.events | length'
```

### Scoring Validation

```bash
# Verify scores are 0-85% max
curl http://localhost:8000/paths/top?limit=100 | \
  jq '.paths | map(.score) | [min, max, unique | length]'

# Expected output: [0, 0.85, <count of unique scores>]
```

---

## 📚 Documentation

### User Training (Non-Technical Officers)

1. **Dashboard**: "Select a relay to investigate"
2. **Paths**: "View probable connection routes"
3. **Analysis**: "See events and network flow"
4. **Report**: "Download findings for case file"

### For Investigators

**Key Point**: These scores represent correlation probability, NOT identification.

- **HIGH (80%+)**: "Strong temporal alignment + geographic diversity suggests this path is plausible"
- **MEDIUM (50-80%)**: "Moderate evidence; investigate further with other methods"
- **LOW (<50%)**: "Weak correlation; unlikely but documented"

### For Technical Staff

**Maintenance Tasks**:
- Monitor container health: `docker ps`
- Check logs: `docker logs container_name`
- Backup data: Automated MongoDB backups recommended
- Update: `docker compose pull && docker compose up -d`

---

## 🔒 Legal & Ethical Considerations

### Authorized Use Only
This tool is designed exclusively for authorized law enforcement investigations. Unauthorized use may violate laws protecting TOR users' privacy rights.

### Investigative Support
Results must be used as **one data point among many**. Never present as conclusive proof without independent validation.

### TOR Protection
This tool does NOT:
- Break TOR anonymity protections
- Intercept user traffic
- Compromise TOR network security
- Violate user privacy rights

### Chain of Custody
- Maintain records of all analysis
- Document dates/times of investigations
- Include full methodology in court presentations
- Preserve audit logs for compliance

### Disclaimers for Reports
Always include in forensic reports:

> **Disclaimer**: TOR Unveil provides probabilistic analysis for investigative support only. Results are not conclusive proof and must be validated through independent means. The tool does not break TOR anonymity protections and operates within legal and ethical boundaries. All findings should be presented with full scoring methodology transparency.

---

## 🆘 Troubleshooting

### Frontend Not Loading
```bash
# Check if container is running
docker ps | grep frontend

# Check logs
docker logs torunveil-frontend

# Rebuild
docker compose -f infra/docker-compose.yml up -d --build
```

### Backend API Not Responding
```bash
# Check backend logs
docker logs torunveil-backend

# Verify MongoDB connection
docker exec torunveil-backend curl http://localhost:8000/relays?limit=1

# Restart services
docker compose -f infra/docker-compose.yml restart
```

### MongoDB Not Connecting
```bash
# Check MongoDB status
docker exec torunveil-mongo mongosh --eval "db.adminCommand('ping')"

# View MongoDB logs
docker logs torunveil-mongo

# Restore from backup if corrupted
docker compose -f infra/docker-compose.yml down
docker volume rm tor-unveil_mongo-data  # WARNING: Deletes data!
docker compose -f infra/docker-compose.yml up -d
```

### Slow Performance
```bash
# Check container resource usage
docker stats torunveil-frontend torunveil-backend torunveil-mongo

# Increase MongoDB performance
docker exec torunveil-mongo mongo --eval "db.paths.createIndex({score: -1})"
docker exec torunveil-mongo mongo --eval "db.relays.createIndex({country: 1})"
```

---

## 📞 Support & Contact

For issues or questions:
1. Check logs: `docker compose logs -f`
2. Review troubleshooting section above
3. Contact development team with:
   - Container logs (sanitized)
   - Steps to reproduce
   - Expected vs actual behavior

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 2025 | Initial release for Tamil Nadu Police Hackathon 2025 |

---

## 📄 License & Attribution

Developed for Tamil Nadu Police Hackathon 2025 as forensic investigative support tool.

**Contributors**: Cybercrime Investigation Team

---

## 🙏 Acknowledgments

- TOR Project: For network metadata API
- React Community: For frontend framework
- FastAPI: For backend framework
- MongoDB: For data persistence

---

**Last Updated**: December 13, 2025
**Status**: Production Ready ✓
