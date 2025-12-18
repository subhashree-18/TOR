# TOR Unveil Backend - Tamil Nadu Police Hackathon 2025

## 🎯 Project Overview

**TOR Unveil: Peel the Onion** is a forensic decision-support system developed for the Tamil Nadu Police Cyber Crime Wing. This backend provides probabilistic correlation analysis of TOR network traffic for investigative assistance.

### 🚨 Important Disclaimers
- **Does NOT deanonymize TOR users**
- **Does NOT break TOR encryption**
- **Provides probabilistic correlation only**
- **For investigative assistance, not proof of attribution**
- **Requires independent corroboration for legal proceedings**

## 🏗️ Architecture

```
backend/
├── app/
│   ├── __init__.py              # FastAPI application initialization
│   ├── main.py                  # API endpoints and server setup
│   ├── auth.py                  # Authentication middleware (placeholder)
│   ├── correlator.py            # TOR traffic correlation engine
│   ├── disclaimer.py            # Legal disclaimer management
│   ├── fetcher.py              # TOR relay data fetching
│   ├── fetcher_enhanced.py     # Enhanced relay data processing
│   ├── forensic_pcap.py        # PCAP file analysis
│   ├── geoip_resolver.py       # Geographic IP resolution
│   ├── integrity.py            # Evidence integrity verification
│   ├── pcap_analyzer.py        # Network packet analysis
│   ├── probabilistic_paths.py  # Path probability calculation
│   ├── risk_engine.py          # Risk assessment engine
│   ├── models/
│   │   ├── __init__.py
│   │   └── investigation.py    # Investigation data models
│   └── scoring/
│       ├── __init__.py
│       ├── bayes_inference.py  # Bayesian statistical analysis
│       ├── confidence_calculator.py
│       ├── confidence_evolution.py
│       └── evidence.py         # Evidence handling models
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                  # This file
```

## 🔧 Technology Stack

- **Framework**: FastAPI (Python 3.9+)
- **Data Processing**: pandas, numpy, scipy
- **Network Analysis**: scapy, dpkt
- **Statistical Analysis**: Bayesian inference models
- **Geographic Data**: GeoIP2, MaxMind databases
- **API Documentation**: OpenAPI/Swagger (auto-generated)
- **Containerization**: Docker

## 📊 Core Features

### 1. **TOR Relay Data Management**
- Fetches live TOR consensus data
- Maintains relay database with geographic metadata
- Tracks relay uptime and bandwidth statistics
- Supports 190+ countries and 7000+ relays

### 2. **Traffic Correlation Engine**
- Time-based correlation analysis
- Entry/middle/exit node path reconstruction
- Confidence scoring with Bayesian inference
- Statistical significance testing

### 3. **Evidence Processing**
- PCAP file ingestion and validation
- SHA-256 integrity verification
- Chain of custody maintenance
- Immutable evidence sealing

### 4. **Forensic Analysis**
- Probabilistic path hypothesis generation
- Confidence evolution tracking
- Geographic correlation analysis
- Temporal pattern recognition

### 5. **Investigation Management**
- Case creation and tracking
- FIR reference linking
- Status workflow management
- Audit trail maintenance

## 🚀 Quick Start

### Prerequisites
```bash
# System requirements
Python 3.9+
Docker (optional)
8GB RAM minimum
50GB storage for TOR data
```

### Installation
```bash
# Clone the repository
git clone https://github.com/subhashree-18/TOR.git
cd TOR/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TOR_DATA_URL="https://collector.torproject.org"
export GEOIP_LICENSE_KEY="your_maxmind_key"
export API_DEBUG=false
```

### Run Development Server
```bash
# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Docker Deployment
```bash
# Build image
docker build -t tor-unveil-backend .

# Run container
docker run -p 8000:8000 \
  -e TOR_DATA_URL="https://collector.torproject.org" \
  -e GEOIP_LICENSE_KEY="your_key" \
  tor-unveil-backend
```

## 🔌 API Endpoints

### Investigation Management
```
GET  /api/investigations                    # List all investigations
POST /api/investigations                    # Create new investigation
GET  /api/investigations/{case_id}          # Get investigation details
PUT  /api/investigations/{case_id}          # Update investigation
```

### Evidence Handling
```
POST /api/evidence/upload                   # Upload PCAP evidence
GET  /api/evidence/{case_id}               # Get evidence status
POST /api/evidence/{case_id}/seal          # Seal evidence (immutable)
```

### Analysis Operations
```
POST /api/analysis/initiate                 # Start correlation analysis
GET  /api/analysis/{case_id}/status        # Get analysis progress
GET  /api/analysis/{case_id}/results       # Get correlation results
GET  /api/analysis/{case_id}/details       # Get detailed findings
```

### TOR Network Data
```
GET  /api/tor/relays                       # Get TOR relay information
GET  /api/tor/status                       # Get network status
GET  /api/tor/update                       # Trigger data refresh
```

### Reports
```
GET  /api/report/{case_id}                 # Generate forensic report
GET  /api/report/{case_id}/export         # Export report (PDF/text)
```

### System Information
```
GET  /api/health                          # System health check
GET  /api/version                         # API version info
GET  /api/disclaimer                      # Legal disclaimer text
```

## 📈 Analysis Methodology

### Correlation Algorithm
1. **Temporal Alignment**: Match traffic timestamps with TOR relay activity
2. **Geographic Correlation**: Analyze entry/exit node geographic distribution
3. **Bandwidth Analysis**: Consider relay capacity and selection probability
4. **Path Reconstruction**: Generate probable 3-hop TOR circuits
5. **Confidence Scoring**: Apply Bayesian inference with penalty factors

### Confidence Levels
- **High (≥75%)**: Strong correlation evidence, multiple confirmatory factors
- **Medium (50-74%)**: Moderate correlation, some uncertainty factors
- **Low (<50%)**: Weak correlation, significant limitations

### Statistical Penalties
- **Same AS Penalty**: 30% reduction if entry/exit in same autonomous system
- **Same Country Penalty**: 20% reduction if entry/exit in same country
- **Timing Uncertainty**: Variable reduction based on clock synchronization

## 🛡️ Security & Ethics

### Data Protection
- All traffic analysis is metadata-only
- No packet payload inspection
- No personal data collection
- Secure evidence handling with integrity verification

### Privacy Preservation
- Geographic regions only (no specific addresses)
- Aggregate relay statistics
- No user identification attempts
- Compliance with Indian IT Act 2000

### Audit Trail
- Complete operation logging
- Evidence chain of custody
- API access tracking
- Investigation timeline preservation

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Test coverage
python -m pytest --cov=app tests/

# Load testing
python -m locust -f tests/load_test.py
```

## 📝 Configuration

### Environment Variables
```bash
# Required
TOR_DATA_URL=https://collector.torproject.org
GEOIP_LICENSE_KEY=your_maxmind_license

# Optional
API_DEBUG=false
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=100MB
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=sqlite:///./investigations.db
CACHE_TTL=3600
```

### Performance Tuning
```bash
# Worker processes (production)
WORKERS=4
MAX_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=5

# Memory limits
MAX_MEMORY_MB=4096
ANALYSIS_TIMEOUT=300

# TOR data refresh
RELAY_UPDATE_INTERVAL=3600
CONSENSUS_CACHE_SIZE=10000
```

## 🚨 Production Deployment

### Hardware Requirements
- **CPU**: 8+ cores recommended
- **RAM**: 16GB minimum, 32GB preferred
- **Storage**: 100GB SSD for optimal performance
- **Network**: Stable internet for TOR data updates

### Security Checklist
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up API authentication
- [ ] Enable request rate limiting
- [ ] Configure CORS properly
- [ ] Set up log monitoring
- [ ] Enable data backup
- [ ] Configure firewall rules

### Monitoring
```bash
# Health check endpoint
curl http://localhost:8000/api/health

# System metrics
curl http://localhost:8000/api/metrics

# Log monitoring
tail -f logs/tor-unveil.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-analysis`)
3. Commit changes (`git commit -m 'Add new analysis method'`)
4. Push to branch (`git push origin feature/new-analysis`)
5. Create Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints for all functions
- Include docstrings for public APIs
- Write unit tests for new features
- Update API documentation

## 📞 Support

### Technical Issues
- **Email**: cyber.tn@gov.in
- **Documentation**: https://github.com/subhashree-18/TOR/wiki
- **Issues**: https://github.com/subhashree-18/TOR/issues

### Legal/Ethical Concerns
- **Tamil Nadu Police**: https://tnpolice.gov.in
- **Cyber Crime Helpline**: 1930

## ⚖️ Legal Notice

This system is developed for the Tamil Nadu Police Cyber Crime Wing under the TN Police Hackathon 2025. It provides investigative assistance only and does not constitute evidence in legal proceedings without independent corroboration.

**Key Limitations:**
- Probabilistic analysis only
- Requires corroboration with additional evidence
- Not suitable as sole evidence in court
- Subject to TOR network database accuracy
- Does not guarantee attribution certainty

---

**© 2025 Tamil Nadu Police Cyber Crime Wing. All Rights Reserved.**