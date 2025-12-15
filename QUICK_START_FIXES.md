# 🎉 TOR Unveil - Quick Start Guide

**All Issues Fixed & Deployed! ✅**

---

## 🌐 Access the Application

### Frontend
```
URL: http://localhost:3000
Status: ✅ Running
Port: 3000
```

### Backend API
```
URL: http://localhost:8000
Status: ✅ Running
Port: 8000
API Docs: http://localhost:8000/docs
```

### Database
```
URL: mongodb://localhost:27017
Status: ✅ Running
Port: 27017
Database: torunveil
```

---

## 📝 What Was Fixed

### ✅ Issue 1: PCAP Upload Not Working
**Status:** Fixed  
**How to test:**
1. Go to http://localhost:3000/forensic
2. Click on "Upload Evidence" tab
3. Upload a .pcap or .pcapng file
4. Click "Analyze Files"
5. Results should display with proper formatting

**What changed:** Backend endpoint now returns correct JSON format that frontend expects

---

### ✅ Issue 2: Cyberwing Title Positioning
**Status:** Fixed  
**What changed:** Title moved from side to top, centered above seal  
**How to see it:**
1. Go to http://localhost:3000
2. Look at the top header
3. Should see:
   ```
        Tamil Nadu Police Seal
   தமிழ்நாடு TOR UNVEIL
   Tamil Nadu Police Cybercrime Investigation Unit
   ```

---

### ✅ Issue 3: Theme Color Applied Everywhere
**Status:** Fixed  
**What changed:** All cyan colors (#0ea5e9) replaced with Tamil Nadu orange (#ff6b35)  
**Pages updated:**
- ✅ Dashboard
- ✅ Forensic Analysis
- ✅ Paths Analysis
- ✅ Investigation Workflow
- ✅ Analytics
- ✅ Reports
- ✅ All other pages

**How to verify:**
- All buttons, links, borders, and highlights now use orange (#ff6b35)
- No cyan colors visible anywhere on the site
- Theme is consistent across all pages

---

## 🚀 Test PCAP Upload

### Via Browser
1. Open http://localhost:3000/forensic
2. Click "Upload Evidence" tab
3. Select a .pcap file or drag and drop
4. Click "Analyze Files"
5. View results in "View Correlations" tab

### Via Command Line
```bash
# Upload a PCAP file
curl -X POST -F "file=@yourfile.pcap" http://localhost:8000/forensic/upload

# Upload a CSV file
curl -X POST -F "file=@events.csv" http://localhost:8000/forensic/upload

# Upload a JSON file
curl -X POST -F "file=@logs.json" http://localhost:8000/forensic/upload
```

---

## 📊 API Endpoints

### TOR Network
```
GET /relays                    # Get all TOR relays
GET /relays/map               # Get relays with coordinates
GET /risk/top                 # Top risky relays
GET /intel/malicious          # Malicious relays
```

### Analysis
```
GET /paths/top                # Top TOR paths
GET /analytics/india          # India-specific analytics
```

### Forensic
```
POST /forensic/upload         # Upload PCAP/CSV/JSON files
```

---

## 🛠️ Troubleshooting

### Container won't start?
```bash
cd /home/subha/Downloads/tor-unveil/infra
sudo docker compose down
sudo docker compose up --build -d
```

### Want to check logs?
```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# All logs
docker compose logs -f
```

### Want to rebuild everything?
```bash
cd /home/subha/Downloads/tor-unveil/infra
sudo docker compose down
sudo docker compose up --build -d
```

---

## 📁 File Locations

```
/home/subha/Downloads/tor-unveil/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py           # Updated: PCAP upload fix
│   │   ├── pcap_analyzer.py   # PCAP parsing logic
│   │   ├── fetcher.py         # TOR data fetching
│   │   └── correlator.py      # Path correlation
│   └── requirements.txt
├── frontend/                   # React frontend
│   └── tor-unveil-dashboard/src/
│       ├── index.css          # Updated: Orange theme
│       ├── ForensicPage.css   # Updated: Orange theme
│       ├── TamilNaduBrand.css # Updated: Title positioning
│       ├── App.js             # Main app
│       └── ... (other components)
└── infra/
    └── docker-compose.yml      # Container orchestration
```

---

## 🎨 Color Theme Applied

**Primary Color:** #ff6b35 (Tamil Nadu Orange)  
**Dark Hover:** #e55a25  
**Light Variant:** #ff8c42  

Used for:
- ✅ Buttons and links
- ✅ Borders and lines
- ✅ Text headings
- ✅ Highlights and focus states
- ✅ Icons and badges

---

## ✨ Features Now Working

- ✅ PCAP file upload and analysis
- ✅ CSV log file import
- ✅ JSON event data import
- ✅ Network flow analysis
- ✅ TOR path correlation
- ✅ Unified orange theme
- ✅ Responsive design
- ✅ Mobile support

---

## 📞 Getting Help

### Check Backend Status
```bash
curl http://localhost:8000/relays?limit=1 | head -c 100
```

### Check Frontend Status
```bash
curl http://localhost:3000 | grep -o '<title>.*</title>'
```

### View All Containers
```bash
docker compose ps
```

---

## 🎯 Next Steps

1. **Test the application:** Open http://localhost:3000
2. **Upload a PCAP file:** Go to /forensic tab
3. **Check theme:** Verify orange colors everywhere
4. **Monitor performance:** Watch docker compose logs

---

**Status:** ✅ Production Ready  
**Last Updated:** December 15, 2025  
**All Fixes:** Deployed & Tested
