# TOR UNVEIL - QUICK START GUIDE FOR POLICE

**For:** Tamil Nadu Police Cyber Crime Wing  
**Date:** December 13, 2025  
**System Status:** ✅ Production Ready

---

## QUICK START - 5 MINUTES

### 1. Open Your Browser
```
http://localhost:3000
```

### 2. Mandatory Legal Disclaimer
- ⚠️ READ CAREFULLY - "NO TOR DEANONYMIZATION" section
- ✓ Check: "I have read and understood..."
- Click: "I Acknowledge and Understand These Limitations"

### 3. You'll See: Investigation Workflow Page

**Your Case Information:**
- Case ID: CASE-2025-001
- Officer: [Your name - click Edit to change]
- Started: [Current timestamp]

**Workflow Progress:**
```
1️⃣ Case Created ✓
2️⃣ TOR Data Collected ✓
3️⃣ Correlation Performed ✓
4️⃣ High-Confidence Paths Identified ✓
5️⃣ Evidence Exported (click button)
```

### 4. Add Investigation Notes
Type in the notes field:
```
"Starting investigation into suspicious exits"
```
Press: `Ctrl+Enter`

✓ Your note is saved with timestamp in audit trail

---

## NAVIGATE TO KEY PAGES

**Top Left Sidebar:**
- 📊 **Dashboard** - TOR relay overview + country legend
- 🔗 **Paths** - List of plausible routes + score explainer
- 📈 **Analysis** - Timeline and network visualization
- 📋 **Reports** - Generate forensic reports

---

## UNDERSTANDING THE DASHBOARD

### Country Reference Legend
- Expand: Click "📍 Country Reference"
- Shows: Full country names for abbreviations
- Search: Type country name to find relays
- Example: "US" = "United States"

### Relay Selection
- Click any relay in the table to investigate
- Shows: Fingerprint, country, role (Exit/Entry), bandwidth

---

## UNDERSTANDING PATHS

### Select a Path
1. Go to **Paths** page
2. Click a path from the list
3. See: **Score Explainer** panel

### Read the Score Explainer
```
ENTRY Node: India
↓
MIDDLE Node: Netherlands
↓
EXIT Node: Bulgaria
```

**Confidence: 87%** (HIGH)

**Why This Score?**
- Primary Factor: High Bandwidth (45% weight)
  "Node has strong relay capacity"
- Secondary Factor: Uptime Overlap (30% weight)
  "Relays were online simultaneously"
- Penalties Applied: -30% (same AS)
  "Reduces score due to AS diversity"
- **Important Limitation:** "This indicates a plausible path, not a confirmed path used by a specific user"

### India-Specific Context
Look for badges like:
- 🇮🇳 "Indian Entry: BSNL"
- 🚨 "India→Bulgaria High-Risk Pattern"

Explanation: "Common in financial fraud targeting India"

---

## GENERATING A FORENSIC REPORT

### Click: Quick Actions → "📋 Generate Report"

**Report Includes:**
- Executive Summary (non-technical)
- Technical Findings (scores & formulas)
- Timeline Narrative (investigation log)
- Confidence & Limitations (CRITICAL SECTION)
- Legal Disclaimer (MUST SHOW IN COURT)

### Download Formats:
- **TXT** - Print-friendly for briefing
- **JSON** - Data for spreadsheet analysis
- **CSV** - Import to Excel

### Important:
✓ All fingerprints preserved (not truncated)  
✓ All timestamps included  
✓ Legal disclaimer visible  
✓ Score limitations explained  

---

## CRITICAL: WHAT THIS SYSTEM DOES (AND DOESN'T)

### ✅ WHAT IT DOES:
- Correlates TOR relay metadata (public information)
- Scores path plausibility (30-95% range)
- Explains scoring factors
- Helps contextualize investigations
- Supports forensic analysis with timestamp correlation

### ❌ WHAT IT DOES NOT DO:
- ❌ **CANNOT** identify TOR users
- ❌ **CANNOT** break TOR encryption
- ❌ **CANNOT** read packet content
- ❌ **CANNOT** track traffic
- ❌ NOT a "TOR deanonymization tool"

---

## FOR COURT PRESENTATION

### Always Say:
✓ "This indicates a **plausible path** based on metadata"  
✓ "The score of 87% means **strong technical evidence**"  
✓ "We corroborated this with **network logs**"  
✓ "This is one piece of **investigative support**, not sole proof"  

### Never Say:
✗ "We deanonymized the TOR user"  
✗ "We identified the user with 100% certainty"  
✗ "This is definitive proof"  
✗ "Our system broke TOR"  

### Always Include:
✓ Original network evidence (logs, PCAP, behavioral)  
✓ Score breakdown explaining methodology  
✓ Confidence limitations from report  
✓ Legal disclaimer from report  

---

## EXAMPLE INVESTIGATION FLOW

### Scenario: TOR-based financial fraud investigation

1. **Receive complaint:** User received phishing email, clicked link, compromised account
2. **Collect evidence:** Network logs show IP connected at specific time
3. **Enter TOR UNVEIL:**
   - Go to Paths → Find high-confidence entry/exit nodes at that timestamp
   - See: "India→Bulgaria 87% confidence"
   - Badge shows: "India→Foreign High-Risk Pattern (common in financial fraud)"
4. **Generate Report:**
   - Multi-format forensic report
   - Explains metadata correlation methodology
   - Score breakdown showing what factors contributed
5. **Corroborate:**
   - Cross-check with ISP logs for that IP
   - Cross-check with timeline of fraud activity
   - Combine all evidence for investigation package
6. **Court Presentation:**
   - Show report with limitations clearly stated
   - Explain: "Metadata analysis indicated these relays were plausibly used"
   - Present corroborating evidence (ISP logs, behavioral pattern, etc.)
   - Secure conviction based on preponderance of evidence

---

## TROUBLESHOOTING

### System not loading
- Check: http://localhost:3000 in browser address bar
- If error, restart: `sudo docker compose -f infra/docker-compose.yml restart`

### No relays showing
- Click: "Refresh Data" button on Dashboard
- Wait 10-15 seconds for TOR data collection
- Refresh browser page

### Score Explainer not appearing
- Select a path from Paths page
- Look in right panel under visualization
- Should show "Why This Path?" section (click to expand)

### Legal Disclaimer appearing again
- This is correct behavior - shows on every fresh Investigation page load
- Must acknowledge to proceed
- Protects both officer and police department

---

## KEYBOARD SHORTCUTS

- `Ctrl+Enter` - Submit investigation note
- Click fingerprint - Copy to clipboard (shows ✓ confirmation)
- Click "🔗" icon - Navigate between pages

---

## DATA YOU CAN TRUST

- **TOR Data:** From official Onionoo directory (public)
- **Timestamps:** Recorded in UTC, verified from multiple sources
- **Fingerprints:** 40-character SHA1 hashes (official TOR identifiers)
- **Audit Trail:** Immutable, append-only investigation log
- **Scores:** Reproducible, formula-based, capped at realistic 95% max

---

## IMPORTANT REMINDERS

### BEFORE USING:
✓ Read and accept Mandatory Legal Disclaimer  
✓ Understand: NO TOR deanonymization claimed  
✓ Understand: Metadata analysis only  
✓ Consult legal counsel for court procedures  

### DURING INVESTIGATION:
✓ Keep notes in Investigation Log (audit trail)  
✓ Cross-reference with network evidence  
✓ Document case ID and officer name  
✓ Take screenshots of Score Explainer for reports  

### FOR COURT:
✓ Present Score Explainer showing methodology  
✓ Include Legal Disclaimer from report  
✓ Explain: "Plausible path, not proven path"  
✓ Bring corroborating evidence (logs, PCAP, behavior)  

---

## NEED HELP?

**Technical Issues:**
- Check Docker containers are running
- View logs: `sudo docker compose logs torunveil-frontend`

**Investigation Questions:**
- See MANDATORY_EXECUTION_REPORT.md for detailed documentation
- Review ScoreExplainer component for methodology

**Legal Questions:**
- Consult police department legal counsel
- Reference MandatoryDisclaimer.js for official disclaimers

---

**System Ready for Investigation  
Status: ✅ Production Ready**

Questions? See MANDATORY_EXECUTION_REPORT.md for complete documentation.

