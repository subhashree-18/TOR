# TOR Unveil Frontend - Tamil Nadu Police Hackathon 2025

## 🎯 Project Overview

The frontend interface for **TOR Unveil: Peel the Onion** - a forensic decision-support system for the Tamil Nadu Police Cyber Crime Wing. This React-based web application provides a government-grade portal for police officers to conduct TOR network traffic correlation analysis.

### 🏛️ Government Portal Design
- **Target Users**: Police officers and cyber crime investigators (non-technical)
- **Design Philosophy**: Conservative, text-first, table-based layout
- **Color Scheme**: Tamil Nadu Police official colors (Navy, Maroon, Gold)
- **No Flashy Elements**: No animations, maps, or Sankey charts
- **Focus**: Clarity, professionalism, and investigative workflow

## 🚨 Important Disclaimers
- **Does NOT deanonymize TOR users**
- **Provides probabilistic correlation only**
- **For investigative assistance, not definitive attribution**
- **All findings require independent corroboration**

## 🏗️ Architecture

```
frontend/tor-unveil-dashboard/
├── public/
│   ├── index.html              # Main HTML template
│   ├── manifest.json           # PWA configuration
│   └── robots.txt             # Search engine directives
├── src/
│   ├── index.js               # Application entry point
│   ├── App.js                 # Main application component
│   ├── App.css                # Global application styles
│   ├── theme.css              # TN Police color theme
│   ├── AppContext.js          # Global state management
│   │
│   ├── PoliceLogin.js         # Disclaimer & access page
│   ├── PoliceLogin.css        # Login page styles
│   │
│   ├── Dashboard.js           # Case management dashboard
│   ├── Dashboard.css          # Dashboard styles
│   │
│   ├── InvestigationPage.js   # Central case workflow hub
│   ├── InvestigationPage.css  # Investigation page styles
│   │
│   ├── ForensicUpload.js      # Evidence upload interface
│   ├── ForensicUpload.css     # Upload page styles
│   │
│   ├── AnalysisPage.js        # Correlation results display
│   ├── AnalysisPage.css       # Analysis page styles
│   │
│   ├── ForensicAnalysis.js    # Detailed findings explanation
│   ├── ForensicAnalysis.css   # Detailed analysis styles
│   │
│   ├── ReportPage.js          # Final forensic report
│   ├── ReportPage.css         # Report page styles
│   │
│   ├── Breadcrumb.js          # Navigation breadcrumb
│   ├── Breadcrumb.css         # Breadcrumb styles
│   │
│   ├── MandatoryDisclaimer.js # Legal disclaimer component
│   ├── MandatoryDisclaimer.css
│   │
│   └── IndianContextBadge.js  # Indian jurisdiction indicator
├── package.json               # Dependencies and scripts
├── static.json               # Build configuration for deployment
├── Dockerfile                # Container configuration
└── README.md                 # This file
```

## 🔧 Technology Stack

- **Framework**: React 18.x with Hooks
- **Routing**: React Router DOM v6
- **HTTP Client**: Axios for API communication
- **Styling**: Pure CSS (no external UI libraries)
- **Icons**: Lucide React (minimal usage)
- **Build Tool**: Create React App
- **Deployment**: Docker containerization

## 📊 Core Features

### 1. **Investigation Workflow Management**
- **Dashboard**: Case selection and creation
- **Investigation Hub**: Single source of truth for case status
- **Evidence Upload**: Forensic file ingestion with chain of custody
- **Analysis Initiation**: Backend-driven correlation triggers
- **Results Display**: Probabilistic findings presentation
- **Report Generation**: Print-friendly forensic documentation

### 2. **Government Portal Standards**
- **Official Branding**: Tamil Nadu Police visual identity
- **Conservative Design**: Professional, non-flashy interface
- **Accessibility**: Government accessibility compliance
- **Mobile Responsive**: Works on tablets and mobile devices
- **Print Optimization**: Report pages optimized for printing

### 3. **Workflow Enforcement**
```
Dashboard → Investigation → Evidence → Analysis → Report
```
- **Route Guards**: Backend verification prevents workflow bypassing
- **Progressive Disclosure**: Information revealed based on case progress
- **State Management**: Real-time synchronization with backend
- **Error Handling**: Clear guidance for unauthorized access

### 4. **Security & Ethics**
- **Legal Disclaimers**: Prominent throughout the interface
- **Evidence Integrity**: Visual indicators for sealed evidence
- **Audit Trail**: Complete operation tracking
- **Access Control**: Officer identification and authorization

## 🚀 Quick Start

### Prerequisites
```bash
# System requirements
Node.js 16+ (LTS recommended)
npm 8+ or yarn 1.22+
Modern web browser (Chrome, Firefox, Edge, Safari)
```

### Installation
```bash
# Clone the repository
git clone https://github.com/subhashree-18/TOR.git
cd TOR/frontend/tor-unveil-dashboard

# Install dependencies
npm install
# or
yarn install
```

### Development Server
```bash
# Start development server
npm start
# or
yarn start

# Application will be available at:
# http://localhost:3000
```

### Production Build
```bash
# Create optimized production build
npm run build
# or
yarn build

# Build output will be in ./build/
```

### Docker Deployment
```bash
# Build image
docker build -t tor-unveil-frontend .

# Run container
docker run -p 3000:3000 \
  -e REACT_APP_API_URL=http://localhost:8000 \
  tor-unveil-frontend
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Backend API configuration
REACT_APP_API_URL=http://localhost:8000

# Application settings
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development

# Optional: Enable debug mode
REACT_APP_DEBUG=false

# Optional: Custom branding
REACT_APP_ORGANIZATION_NAME="Tamil Nadu Police"
REACT_APP_DEPARTMENT="Cyber Crime Wing"
```

### API Integration
The frontend communicates with the backend through these endpoints:

```javascript
// Investigation management
GET  /api/investigations/:caseId
POST /api/investigations
PUT  /api/investigations/:caseId

// Evidence handling
POST /api/evidence/upload
GET  /api/evidence/:caseId
POST /api/evidence/:caseId/seal

// Analysis operations
POST /api/analysis/initiate
GET  /api/analysis/:caseId/status
GET  /api/analysis/:caseId/results
GET  /api/analysis/:caseId/details

// Report generation
GET  /api/report/:caseId
```

## 🎨 Design System

### Color Palette (Tamil Nadu Police)
```css
/* Primary Colors */
--tn-navy: #0b3c5d;      /* Primary navigation, headers */
--tn-maroon: #7a1f1f;    /* Accents, warnings */
--tn-gold: #d9a441;      /* Highlights, success states */

/* Secondary Colors */
--bg-main: #f5f7fa;      /* Page backgrounds */
--bg-white: #ffffff;     /* Content areas */
--text-dark: #1a1a1a;    /* Primary text */
--text-grey: #4a4a4a;    /* Secondary text */
--border-light: #d1d5db; /* Borders, dividers */
```

### Typography
```css
/* Font Stack */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 
             'Helvetica Neue', Arial, sans-serif;

/* Hierarchy */
h1: 24px, 700 weight      /* Page titles */
h2: 20px, 700 weight      /* Section headers */
h3: 16px, 600 weight      /* Subsections */
body: 14px, 400 weight    /* Body text */
small: 12px, 400 weight   /* Meta information */
```

### Layout Principles
- **Grid System**: CSS Grid and Flexbox
- **Spacing**: 8px base unit (8, 16, 24, 32px)
- **Borders**: 1-2px solid borders, no rounded corners
- **Shadows**: Minimal use, subtle elevation only
- **Animations**: None (government portal requirement)

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
Mobile:  320px - 768px
Tablet:  768px - 1024px
Desktop: 1024px+
```

### Key Features
- **Mobile Navigation**: Collapsible menu for small screens
- **Touch Targets**: Minimum 44px for touch interfaces
- **Readable Text**: Scalable font sizes
- **Optimized Images**: Responsive image sizing
- **Print Friendly**: Special print stylesheets for reports

## 🔐 Security Features

### Route Protection
```javascript
// Route guards check backend state
const RouteGuard = ({ children, requiredState }) => {
  const [hasAccess, setHasAccess] = useState(false);
  
  useEffect(() => {
    checkCaseStatus(caseId).then(status => {
      setHasAccess(status[requiredState]);
    });
  }, [caseId, requiredState]);
  
  return hasAccess ? children : <AccessDenied />;
};
```

### Data Validation
- **Input Sanitization**: All user inputs validated
- **File Type Validation**: Only PCAP files accepted
- **Size Limits**: 100MB maximum file size
- **Format Checking**: File header validation

### Audit Trail
- **User Actions**: All navigation and interactions logged
- **API Calls**: Complete request/response logging
- **Error Tracking**: Comprehensive error reporting
- **Session Management**: Secure session handling

## 🧪 Testing

### Unit Testing
```bash
# Run unit tests
npm test
# or
yarn test

# Run with coverage
npm test -- --coverage
# or
yarn test --coverage
```

### Integration Testing
```bash
# Run integration tests
npm run test:integration
# or
yarn test:integration
```

### End-to-End Testing
```bash
# Run E2E tests (requires backend running)
npm run test:e2e
# or
yarn test:e2e
```

### Accessibility Testing
```bash
# Run accessibility tests
npm run test:a11y
# or
yarn test:a11y
```

## 📦 Build and Deployment

### Development Build
```bash
npm run build:dev
# Creates development build with source maps
```

### Production Build
```bash
npm run build
# Creates optimized production build
# Output: ./build/
```

### Build Analysis
```bash
npm run analyze
# Analyze bundle size and dependencies
```

### Deployment Options

#### Static Hosting (Recommended)
```bash
# Serve build folder with any static file server
npm install -g serve
serve -s build -l 3000
```

#### Docker Deployment
```bash
# Multi-stage build for optimized container
docker build -t tor-unveil-frontend:latest .
docker run -p 3000:80 tor-unveil-frontend:latest
```

#### Cloud Deployment
```bash
# Deploy to cloud platforms
# Vercel, Netlify, AWS S3, etc.
npm run deploy
```

## 🎯 User Workflow

### 1. Access & Disclaimer
1. Officer enters system credentials
2. Acknowledges legal disclaimer
3. Understands system limitations

### 2. Case Management
1. View existing investigations
2. Create new case if needed
3. Select case to work on

### 3. Investigation Hub
1. Review case details and status
2. Check TOR network data currency
3. View evidence and analysis state
4. Follow next recommended action

### 4. Evidence Handling
1. Upload PCAP/network log files
2. Verify file integrity (SHA-256)
3. Seal evidence (makes immutable)
4. Maintain chain of custody

### 5. Analysis Operations
1. Initiate correlation analysis
2. Monitor analysis progress
3. Review probabilistic findings
4. Understand confidence levels

### 6. Report Generation
1. Generate comprehensive report
2. Export as PDF or text
3. Include legal disclaimers
4. Print for case files

## 🔧 Development Guidelines

### Code Style
```bash
# Use Prettier for formatting
npm run format

# Use ESLint for linting
npm run lint
```

### Component Structure
```javascript
// Functional components with hooks
const ComponentName = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  return (
    <div className="component-name">
      {/* JSX content */}
    </div>
  );
};

export default ComponentName;
```

### CSS Organization
```css
/* Component-specific CSS files */
.component-name {
  /* Layout */
  display: flex;
  flex-direction: column;
  
  /* Spacing */
  padding: 16px;
  margin: 8px 0;
  
  /* Colors */
  background: var(--bg-white);
  color: var(--text-dark);
  
  /* Typography */
  font-size: 14px;
  font-weight: 400;
}
```

### State Management
```javascript
// Context API for global state
const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [cases, setCases] = useState([]);
  
  const value = {
    user,
    setUser,
    cases,
    setCases
  };
  
  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};
```

## 📈 Performance Optimization

### Code Splitting
```javascript
// Lazy load components
const AnalysisPage = lazy(() => import('./AnalysisPage'));
const ReportPage = lazy(() => import('./ReportPage'));

// Wrap with Suspense
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/analysis" element={<AnalysisPage />} />
    <Route path="/report" element={<ReportPage />} />
  </Routes>
</Suspense>
```

### Caching Strategy
- **API Responses**: Cache case data for 5 minutes
- **Static Assets**: Browser caching with service worker
- **Images**: Optimize and compress images
- **Fonts**: Subset fonts for faster loading

### Bundle Optimization
```javascript
// webpack-bundle-analyzer output
File sizes after gzip:
  76.23 KB  static/js/main.[hash].js
  15.64 KB  static/css/main.[hash].css
  2.45 KB   static/js/runtime.[hash].js
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Clone your fork
3. Create feature branch
4. Make changes
5. Run tests
6. Submit pull request

### Commit Convention
```bash
# Use conventional commits
feat: add new analysis visualization
fix: resolve evidence upload issue
docs: update API documentation
style: improve component styling
refactor: optimize state management
test: add unit tests for Dashboard
```

### Pull Request Process
1. Ensure all tests pass
2. Update documentation
3. Add screenshot if UI changes
4. Request review from maintainers

## 📞 Support

### Technical Issues
- **Repository**: https://github.com/subhashree-18/TOR
- **Issues**: https://github.com/subhashree-18/TOR/issues
- **Documentation**: https://github.com/subhashree-18/TOR/wiki

### Application Support
- **Tamil Nadu Police**: https://tnpolice.gov.in
- **Cyber Crime Wing**: cyber.tn@gov.in
- **Helpline**: 1930

## ⚖️ Legal & Compliance

### Accessibility Standards
- **WCAG 2.1 Level AA** compliance
- **Keyboard Navigation** support
- **Screen Reader** compatibility
- **High Contrast** mode support

### Data Privacy
- **No Personal Data Collection**
- **Metadata Analysis Only**
- **Secure Evidence Handling**
- **Audit Trail Maintenance**

### Legal Disclaimers
- Prominent disclaimers throughout interface
- Clear limitation statements
- Ethical use guidance
- Investigation assistance only

---

**© 2025 Tamil Nadu Police Cyber Crime Wing. All Rights Reserved.**

*This system provides investigative assistance only and does not constitute evidence without independent corroboration.*