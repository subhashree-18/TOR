# TOR Unveil: Peel the Onion
## Tamil Nadu Police Hackathon 2025 🏆

<div align="center">

**Forensic Decision-Support System for TOR Network Traffic Correlation**

*Developed for the Tamil Nadu Police Cyber Crime Wing*

[![License](https://img.shields.io/badge/License-Restricted-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)

</div>

---

## 🚨 **IMPORTANT DISCLAIMERS**

### **THIS SYSTEM DOES NOT:**
- ❌ **Deanonymize TOR users**
- ❌ **Break TOR encryption**
- ❌ **Provide definitive attribution**
- ❌ **Constitute legal evidence without corroboration**

### **THIS SYSTEM PROVIDES:**
- ✅ **Probabilistic correlation analysis**
- ✅ **Investigative assistance**
- ✅ **Temporal pattern recognition**
- ✅ **Geographic correlation insights**

> **⚖️ Legal Notice**: This system is for investigative assistance only. All findings require independent corroboration before being presented in legal proceedings.

---

## 🎯 **Project Overview**

**TOR Unveil** is a forensic decision-support system designed for the Tamil Nadu Police Cyber Crime Wing to assist in investigations involving TOR network traffic. The system performs probabilistic correlation analysis between observed network metadata and known TOR relay infrastructure.

### **Problem Statement Alignment**
This project directly addresses the **"TOR Unveil: Peel the Onion"** challenge from the Tamil Nadu Police Hackathon 2025, focusing on:
- **Ethical forensic analysis** without breaking anonymity
- **Probabilistic correlation** of network traffic patterns
- **Investigative assistance** for law enforcement
- **Evidence-based insights** with clear limitations

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│    Frontend     │◄──►│     Backend      │◄──►│   TOR Network   │
│   React Web     │    │   FastAPI +      │    │     Data        │
│     Portal      │    │   Analytics      │    │   (Live Feed)   │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│ Police Officers │    │ PCAP Analysis +  │    │ 7000+ Relays    │
│ Investigation   │    │ Bayesian Stats   │    │ 190+ Countries  │
│    Workflow     │    │ Correlation      │    │ Real-time Data  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 📊 **Core Capabilities**

### 🔍 **Traffic Correlation Analysis**
- **Temporal Correlation**: Match traffic timing with TOR relay activity windows
- **Geographic Analysis**: Correlate entry/exit node regions with observed patterns
- **Path Reconstruction**: Generate probable 3-hop TOR circuit hypotheses
- **Confidence Scoring**: Bayesian inference with penalty factors for uncertainty

### 📁 **Evidence Management**
- **PCAP Ingestion**: Secure upload and processing of network capture files
- **Chain of Custody**: SHA-256 integrity verification and immutable evidence sealing
- **Audit Trail**: Complete investigation workflow tracking
- **Forensic Standards**: Compliance with digital evidence handling protocols

### 👮 **Investigation Workflow**
```
Dashboard → Investigation → Evidence → Analysis → Report
    ↓           ↓             ↓          ↓         ↓
Case       Case Status   PCAP Upload  Correlation  Forensic
Selection  Tracking      & Sealing    Analysis     Report
```

### 📈 **Statistical Analysis**
- **Bayesian Inference**: Probabilistic confidence assessment
- **Uncertainty Quantification**: Clear limitations and error margins
- **Multiple Hypotheses**: Ranked alternative explanations
- **Confidence Evolution**: Progressive analysis refinement

---

## 🏛️ **Government Portal Design**

### **Tamil Nadu Police Standards**
- **Conservative Interface**: Text-first, table-based layout
- **Official Colors**: Navy (#0b3c5d), Maroon (#7a1f1f), Gold (#d9a441)
- **Professional Typography**: Clean, readable government portal styling
- **No Flashy Elements**: No animations, maps, or complex visualizations

### **User Experience**
- **Target Audience**: Police officers and cyber crime investigators (non-technical)
- **Workflow-Driven**: Backend state determines available actions
- **Clear Limitations**: Prominent disclaimers and ethical guidance
- **Print-Friendly**: Report generation optimized for case files

---

## 🚀 **Quick Start Guide**

### **Prerequisites**
```bash
# Required Software
Node.js 16+ (for frontend)
Python 3.9+ (for backend)
Docker (optional, recommended)
8GB RAM minimum
50GB storage for TOR data
```

### **Option 1: Docker Compose (Recommended)**
```bash
# Clone the repository
git clone https://github.com/subhashree-18/TOR.git
cd TOR

# Start all services
docker-compose up -d

# Access the application
Frontend: http://localhost:3000
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
```

### **Option 2: Manual Setup**

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend/tor-unveil-dashboard

# Install dependencies
npm install

# Start development server
npm start

# Application available at http://localhost:3000
```

---

## 📁 **Project Structure**

```
TOR/
├── README.md                    # This file
├── docker-compose.yml          # Multi-container orchestration
├── DEPLOYMENT.md               # Deployment instructions
├── LICENSE                     # License information
│
├── backend/                    # FastAPI backend service
│   ├── app/                   # Application code
│   │   ├── main.py           # API endpoints
│   │   ├── correlator.py     # Correlation engine
│   │   ├── forensic_pcap.py  # PCAP analysis
│   │   ├── models/           # Data models
│   │   └── scoring/          # Statistical analysis
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Backend container
│   └── README.md            # Backend documentation
│
├── frontend/                  # React frontend application
│   └── tor-unveil-dashboard/ # Main web interface
│       ├── src/              # Source code
│       │   ├── App.js       # Main application
│       │   ├── Dashboard.js  # Case management
│       │   ├── InvestigationPage.js  # Case workflow hub
│       │   ├── ForensicUpload.js     # Evidence upload
│       │   ├── AnalysisPage.js       # Results display
│       │   └── ReportPage.js         # Report generation
│       ├── public/          # Static assets
│       ├── package.json     # Dependencies
│       ├── Dockerfile       # Frontend container
│       └── README.md        # Frontend documentation
│
├── infra/                    # Infrastructure as code
│   └── docker-compose.yml   # Service orchestration
│
├── tests/                    # Test suites
│   ├── test_*.py            # Backend unit tests
│   └── __pycache__/         # Python cache
│
└── docs/                     # Documentation
    └── forensic_notes.md    # Technical notes
```

---

## 💻 **Technology Stack**

### **Backend (Python)**
- **Framework**: FastAPI (high-performance async API)
- **Data Analysis**: pandas, numpy, scipy
- **Network Analysis**: scapy, dpkt (PCAP processing)
- **Statistics**: Bayesian inference, confidence intervals
- **Geographic Data**: MaxMind GeoIP2
- **Database**: SQLite (development), PostgreSQL (production)

### **Frontend (React)**
- **Framework**: React 18 with Hooks
- **Routing**: React Router DOM v6
- **HTTP Client**: Axios
- **Styling**: Pure CSS (no external UI libraries)
- **State Management**: Context API
- **Build Tool**: Create React App

### **Infrastructure**
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production reverse proxy)
- **Process Management**: Gunicorn (WSGI server)
- **Development**: Hot reload for both frontend and backend

---

## 🔐 **Security & Compliance**

### **Data Protection**
- **Metadata Only**: No packet payload inspection
- **Secure Hashing**: SHA-256 evidence integrity
- **Audit Logging**: Complete operation tracking
- **Access Control**: Officer identification and authorization

### **Ethical Guidelines**
- **Privacy Preservation**: Geographic regions only, no specific addresses
- **Limitation Transparency**: Clear disclaimers throughout interface
- **Legal Compliance**: Aligned with Indian IT Act 2000
- **Professional Use**: Police investigation assistance only

### **Evidence Handling**
- **Chain of Custody**: Immutable evidence sealing
- **Forensic Standards**: Digital evidence best practices
- **Integrity Verification**: Cryptographic file validation
- **Audit Trail**: Complete workflow documentation

---

## 📈 **Analysis Methodology**

### **Correlation Algorithm**
1. **PCAP Ingestion**: Extract network metadata from forensic captures
2. **TOR Data Fetching**: Retrieve current relay consensus and historical data
3. **Temporal Alignment**: Match traffic timestamps with relay activity windows
4. **Geographic Correlation**: Analyze entry/exit node regional patterns
5. **Path Reconstruction**: Generate probable 3-hop circuit hypotheses
6. **Confidence Scoring**: Apply Bayesian inference with uncertainty factors

### **Statistical Framework**
```
Confidence = (Temporal_Score × 0.4 + Geographic_Score × 0.3 + 
              Bandwidth_Score × 0.3) × Penalty_Factors

Where:
- Temporal_Score: Time window overlap correlation (0-1)
- Geographic_Score: Regional distribution likelihood (0-1)
- Bandwidth_Score: Relay capacity and selection probability (0-1)
- Penalty_Factors: Reductions for same-AS, same-country relays
```

### **Confidence Levels**
- **High (≥75%)**: Strong correlation evidence, multiple confirmatory factors
- **Medium (50-74%)**: Moderate correlation, some uncertainty factors  
- **Low (<50%)**: Weak correlation, significant limitations

---

## 🧪 **Testing & Quality Assurance**

### **Backend Testing**
```bash
# Run unit tests
cd backend
python -m pytest tests/ -v

# Test coverage
python -m pytest --cov=app tests/

# Integration tests
python -m pytest tests/integration/ -v
```

### **Frontend Testing**
```bash
# Run unit tests
cd frontend/tor-unveil-dashboard
npm test

# Run with coverage
npm test -- --coverage

# E2E testing
npm run test:e2e
```

### **System Testing**
```bash
# Start all services
docker-compose up -d

# Run integration test suite
./scripts/run_integration_tests.sh

# Performance testing
./scripts/run_load_tests.sh
```

---

## 📚 **Documentation**

### **Technical Documentation**
- **[Backend README](backend/README.md)**: API documentation and setup
- **[Frontend README](frontend/tor-unveil-dashboard/README.md)**: UI components and styling
- **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions
- **[API Reference](http://localhost:8000/docs)**: OpenAPI/Swagger documentation

### **User Guides**
- **Investigation Workflow**: Step-by-step case management
- **Evidence Upload**: PCAP file handling procedures  
- **Analysis Interpretation**: Understanding correlation results
- **Report Generation**: Creating forensic documentation

### **Technical References**
- **TOR Protocol**: Understanding relay selection and routing
- **Correlation Methods**: Statistical analysis techniques
- **Forensic Standards**: Digital evidence best practices
- **Legal Framework**: Indian cyber crime investigation procedures

---

## 🤝 **Contributing**

### **Development Workflow**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-analysis`)
3. Make changes with proper testing
4. Update documentation as needed
5. Submit pull request with detailed description

### **Code Standards**
- **Backend**: Follow PEP 8, add type hints, include docstrings
- **Frontend**: Use ESLint/Prettier, functional components, CSS modules
- **Testing**: Maintain >80% test coverage
- **Documentation**: Update relevant README files

### **Review Process**
- **Code Review**: All changes require maintainer approval
- **Testing**: Automated tests must pass
- **Documentation**: Update user guides for feature changes
- **Security**: Security implications reviewed for sensitive changes

---

## 📞 **Support & Contact**

### **Technical Issues**
- **Repository**: https://github.com/subhashree-18/TOR
- **Issues**: https://github.com/subhashree-18/TOR/issues
- **Wiki**: https://github.com/subhashree-18/TOR/wiki

### **Official Channels**
- **Tamil Nadu Police**: https://tnpolice.gov.in
- **Cyber Crime Wing**: cyber.tn@gov.in
- **National Cyber Crime Helpline**: 1930

### **Academic Collaboration**
- **Technical Queries**: Research methodology and implementation
- **Forensic Consultation**: Digital evidence analysis techniques
- **Legal Framework**: Cyber crime investigation procedures

---

## ⚖️ **Legal & Ethics**

### **Terms of Use**
This system is developed exclusively for the Tamil Nadu Police Cyber Crime Wing under the TN Police Hackathon 2025. Usage is restricted to authorized law enforcement personnel for official investigations only.

### **Limitations Statement**
- **Probabilistic Analysis Only**: Results indicate correlation likelihood, not certainty
- **Corroboration Required**: All findings must be validated through independent evidence
- **Investigation Assistance**: Not suitable as sole evidence in legal proceedings
- **Technical Uncertainty**: Subject to TOR network data accuracy and analysis limitations

### **Ethical Compliance**
- **Privacy Respect**: No user deanonymization attempted or performed
- **Professional Use**: Restricted to legitimate law enforcement investigations
- **Transparency**: Open methodology and clear limitation disclosure
- **Legal Alignment**: Compliant with Indian IT Act 2000 and cyber crime laws

---

## 📊 **System Status**

### **Current Version**
- **Release**: v1.0.0-hackathon
- **Status**: Production Ready ✅
- **Last Updated**: December 18, 2025
- **Build Status**: All tests passing ✅

### **Features Status**
- ✅ **PCAP Upload & Analysis**
- ✅ **TOR Relay Data Fetching**
- ✅ **Correlation Engine**
- ✅ **Statistical Analysis**
- ✅ **Report Generation**
- ✅ **Evidence Chain of Custody**
- ✅ **Government Portal UI**
- ✅ **Legal Disclaimers**

### **Browser Support**
- ✅ **Chrome 90+**
- ✅ **Firefox 88+**
- ✅ **Safari 14+**
- ✅ **Edge 90+**

---

<div align="center">

**© 2025 Tamil Nadu Police Cyber Crime Wing. All Rights Reserved.**

*This system provides investigative assistance only and does not constitute evidence without independent corroboration.*

**Developed for TN Police Hackathon 2025**

</div>