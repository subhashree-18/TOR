# BACKEND ERROR ANALYSIS REPORT
**Date:** 2025-12-20  
**Status:** ⚠️ CRITICAL ISSUES IDENTIFIED  
**Severity:** HIGH (5 major problem areas)

---

## Executive Summary

The TOR-Unveil backend has **5 critical error categories** that could cause runtime failures, API 404 errors, database connection issues, and incorrect analysis results. This report documents each issue with:
- ❌ The specific problem
- 🔍 Root cause analysis
- 💥 Impact on system functionality
- ✅ Recommended fixes

---

## Issue 1: Application Boot & Routing Errors

### 1.1 FastAPI App Instance Consistency ✅ GOOD

**Status:** ✅ **SAFE** - No critical issues found

**Finding:**
```python
# backend/app/main.py (Line 40-43)
app = FastAPI(
    title="TOR Unveil API",
    version="2.0",
    description="Forensic correlation analysis for TOR network investigations..."
)
```

**Assessment:**
- ✅ FastAPI app is properly instantiated at module level
- ✅ App is correctly named `app` (standard for uvicorn)
- ✅ Auth router is properly included: `app.include_router(auth_router)`
- ✅ CORS middleware is properly configured
- ✅ No if `__name__ == "__main__"` block needed (designed for uvicorn)

**Conclusion:** Application initialization is **CORRECT**. Will work with:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

---

## Issue 2: MongoDB Connection Failures

### 2.1 Inconsistent MongoDB Connection Strings ❌ CRITICAL

**Problem Identified:**

The codebase has **THREE different MONGO_URL configurations**:

| File | MONGO_URL | Issue |
|------|-----------|-------|
| `main.py` (Line 71) | `mongodb://mongo:27017/torunveil` | Docker-only hostname |
| `correlator.py` (Line 45) | `mongodb://mongo:27017/torunveil` | Docker-only hostname |
| `auth.py` (Line 43) | Custom handling | Has timeout logic ✅ |
| `fetcher.py` (Line 21) | `mongodb://localhost:27017/torunveil` | Localhost only |
| `fetcher_enhanced.py` (Line 21) | `mongodb://localhost:27017/torunveil` | Localhost only |

**Code Examples:**

```python
# main.py (BREAKS when not in Docker)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/torunveil")
client = MongoClient(MONGO_URL)
db = client["torunveil"]
# ❌ "mongo" hostname only resolves inside Docker Compose
# ❌ No error handling - silent failure
```

```python
# fetcher.py (Different default)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/torunveil")
client = MongoClient(MONGO_URL)
# ❌ Uses localhost, but main.py uses "mongo"
# ❌ Inconsistent between modules
```

```python
# auth.py (HAS proper error handling)
_mongo_client = MongoClient(
    mongodb_url, 
    serverSelectionTimeoutMS=5000,  # ✅ Good
    connectTimeoutMS=5000              # ✅ Good
)
```

### 2.2 Impact

**When running locally (without Docker):**
```
ERROR: MongoClient tries to connect to "mongo:27017"
       → "mongo" hostname cannot be resolved
       → Silent connection failure
       → All API calls fail with no clear error message
```

**When running in Docker:**
```
✅ Works fine (mongo service is available)
❌ But still inconsistent with fetcher modules
```

**Specific API Failures:**
- ❌ GET `/api/hypotheses` → 404 (correlator.py can't connect)
- ❌ GET `/api/analysis/{caseId}` → 500 (database query fails)
- ❌ POST `/api/evidence/upload` → 500 (can't persist analysis)
- ❌ GET `/relays` → 500 (fetcher.py uses different URL)

### 2.3 Root Cause

1. **No environment validation** - Code doesn't check if MongoDB is reachable
2. **No fallback logic** - Code doesn't try alternative URLs
3. **Multiple hardcoded values** - Each file has its own default
4. **No error handling** - MongoClient errors are not caught

### 2.4 Recommended Fix

**Create a unified database module** to handle connections:

```python
# backend/app/database.py (NEW FILE)
import os
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

def get_mongo_client():
    """Get MongoDB client with fallback and error handling."""
    
    # Try environment variable first, then fallbacks
    mongo_urls = [
        os.getenv("MONGO_URL"),
        "mongodb://localhost:27017/torunveil",      # Local development
        "mongodb://127.0.0.1:27017/torunveil",      # Local alias
        "mongodb://mongo:27017/torunveil",          # Docker Compose
        "mongodb://mongo-service:27017/torunveil",  # Kubernetes
    ]
    
    for url in mongo_urls:
        if url is None:
            continue
        try:
            client = MongoClient(
                url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test connection
            client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {url}")
            return client
        except Exception as e:
            logger.warning(f"❌ Failed to connect to {url}: {e}")
            continue
    
    # If all attempts fail, raise explicit error
    raise RuntimeError(
        "Cannot connect to MongoDB. Tried: " + 
        ", ".join([u for u in mongo_urls if u])
    )

# Global client
_client = None
_db = None

def get_db():
    """Get MongoDB database instance."""
    global _client, _db
    if _db is None:
        _client = get_mongo_client()
        _db = _client["torunveil"]
    return _db
```

**Then update all modules** to use this:

```python
# In main.py, correlator.py, fetcher.py, etc.
from .database import get_db

# Instead of: db = client["torunveil"]
db = get_db()
```

---

## Issue 3: Correlation & Scoring Logic Errors

### 3.1 Mixed and Potentially Conflicting Logic ❌ MODERATE

**Problem Identified:**

The correlation scoring system mixes multiple frameworks without clear integration:

| Module | Purpose | Scoring Method | Issue |
|--------|---------|-----------------|-------|
| `correlator.py` | Entry-exit correlation | Timing + behavior | ⚠️ Complex, unclear normalization |
| `risk_engine.py` | Risk assessment | TBD | ❓ Unknown implementation |
| `confidence_calculator.py` | Confidence scoring | TBD | ❓ Separate from correlator |
| `confidence_evolution.py` | Confidence evolution | TBD | ❓ Another scoring system |
| `probabilistic_paths.py` | Probabilistic inference | Bayesian | ⚠️ Not integrated with correlator |

**Example from correlator.py:**

```python
class CorrelationResult(NamedTuple):
    """Result of correlation between exit and guard"""
    guard_nickname: str
    exit_nickname: str
    timing_similarity_score: float        # Normalized 0-1 ✅
    session_overlap_score: float          # Normalized 0-1 ✅
    # But how are these combined???
    # No final_score or confidence field!
```

**Example of normalization:**

```python
# In correlator.py Line 428-432
mean_diff = abs(tv1.mean_ipt_ms - tv2.mean_ipt_ms) / max(tv1.mean_ipt_ms, tv2.mean_ipt_ms, 1.0)
std_diff = abs(tv1.std_ipt_ms - tv2.std_ipt_ms) / max(tv1.std_ipt_ms, tv2.std_ipt_ms, 1.0)
median_diff = abs(tv1.median_ipt_ms - tv2.median_ipt_ms) / max(tv1.median_ipt_ms, tv2.median_ipt_ms, 1.0)
# These are differences (0-∞) but then...
return min(1.0, distance)  # Clamped to 1.0
# ❌ What is "distance"? It's the sum above, so could be 3.0+
# ❌ min(1.0, 3.0+) always returns 1.0 for large differences!
# ❌ This causes score clamp to same range (always ~1.0 for dissimilar pairs)
```

### 3.2 Confidence Score Does Not Vary ❌ CRITICAL

**Observation from previous testing:**

All hypotheses received "Medium" confidence level regardless of actual evidence:

```
Rank 1: 100,000 evidence → Medium confidence
Rank 2: 85,000 evidence  → Medium confidence
Rank 3: 70,000 evidence  → Medium confidence
Rank 4: 55,000 evidence  → Medium confidence
Rank 5: 40,000 evidence  → Medium confidence
```

**Why this happens:**

The evidence formula (`packets × 100 × decay_factor`) only affects `evidence_count`, NOT `confidence_level`. The confidence is hardcoded separately:

```python
# From main.py (Line ~2290, approximate)
hypotheses.append({
    "rank": pair_idx + 1,
    "entry_region": f"{g.get('country')}",
    "exit_region": f"{e.get('country')}",
    "evidence_count": evidence_count,  # ← Varies based on formula
    "confidence_level": "Medium",      # ← Hardcoded!!!
    "explanation": {...}
})
```

### 3.3 Hackathon Requirement "Accuracy Improves Over Time" NOT MET ❌

**Requirement (from problem statement):**
> "Confidence or accuracy improves when additional evidence is processed"

**Current system:**
- ✅ Evidence count increases (good)
- ❌ Confidence level stays fixed at "Medium" (bad)
- ❌ No mechanism to improve confidence with additional uploads

**Why it's broken:**
- Multiple scoring modules exist but aren't coordinated
- `confidence_evolution.py` exists but isn't called
- No state tracking across uploads for the same case

### 3.4 Root Cause

1. **No integrated scoring pipeline** - Multiple modules do scoring independently
2. **No evidence aggregation** - Each upload doesn't improve previous confidence
3. **Hardcoded values** - Confidence is literal string, not computed
4. **No Bayesian update** - New evidence doesn't update prior beliefs

### 3.5 Recommended Fix

**Implement unified scoring pipeline:**

```python
# backend/app/scoring_pipeline.py (NEW)

from typing import Dict, List
import statistics

class UnifiedScoringEngine:
    """Single source of truth for all scoring."""
    
    @staticmethod
    def compute_confidence_level(
        evidence_count: int,
        timing_similarity: float,
        session_overlap: float,
        additional_evidence: List[Dict] = None
    ) -> str:
        """
        Compute confidence level from multiple evidence sources.
        Returns: "High", "Medium", or "Low"
        """
        
        # Combine multiple sources
        scores = []
        
        # Evidence volume factor
        if evidence_count > 50000:
            scores.append(0.85)  # Strong evidence volume
        elif evidence_count > 20000:
            scores.append(0.65)  # Moderate evidence
        else:
            scores.append(0.35)  # Weak evidence
        
        # Timing factor (0-1)
        scores.append(timing_similarity)
        
        # Session overlap factor (0-1)
        scores.append(session_overlap)
        
        # Additional evidence (Bayesian prior)
        if additional_evidence:
            prior = len(additional_evidence) / max(1, len(additional_evidence) + 5)
            scores.append(prior)
        
        # Average all factors
        avg_score = statistics.mean(scores)
        
        # Map to confidence level
        if avg_score >= 0.75:
            return "High"
        elif avg_score >= 0.50:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def combine_correlations(
        timing_score: float,
        overlap_score: float,
        weight_timing: float = 0.6,
        weight_overlap: float = 0.4
    ) -> float:
        """Properly combine correlation scores."""
        return (timing_score * weight_timing) + (overlap_score * weight_overlap)
```

---

## Issue 4: PCAP & Forensics Module Issues

### 4.1 PCAP Features Exist But May Have Integration Issues ✅/⚠️ MODERATE

**Status:** PCAP processing exists, but integration unclear

**What exists:**
- ✅ `pcap_analyzer.py` (518 lines) - Full PCAP parser
- ✅ `forensic_pcap.py` - Forensic flow analysis
- ✅ `POST /forensic/upload` endpoint (main.py Line 564)
- ✅ `POST /api/evidence/upload` endpoint with PCAP support

**What was verified working:**
- ✅ PCAP files are parsed correctly
- ✅ Packets are extracted and counted
- ✅ IPs are identified and deduplicated
- ✅ Hypotheses are generated from PCAP data

**Potential issues:**

1. **Multiple upload endpoints**
   ```python
   POST /forensic/upload          # Line 564 in main.py
   POST /api/evidence/upload      # Line 2184 in main.py
   ```
   - ❓ Which one should frontend use?
   - ❓ Do they do the same thing?

2. **File type validation**
   ```python
   # From main.py ~2190
   if file_ext in {'.pcap', '.pcapng', '.cap'}:
       # Process PCAP
   else:
       # Process other file types
   ```
   - ✅ File extension checks exist
   - ⚠️ No magic number validation (could accept fake PCAP)

3. **Error handling during PCAP processing**
   ```python
   try:
       pcap_parsed = analyze_pcap_file(content)
   except Exception as e:
       logger.error(f"PCAP analysis failed: {e}")
       # Still returns upload_result without analysis
       # User doesn't know analysis failed
   ```

### 4.2 Recommended Fix

**Consolidate to single upload endpoint:**

```python
# backend/app/main.py - Remove duplicate /forensic/upload

# Keep only /api/evidence/upload and make it clear what it does
@app.post("/api/evidence/upload", tags=["Evidence"])
async def upload_evidence(
    file: UploadFile = File(...),
    caseId: str = Form(...),
    evidence_type: str = Form(default="pcap")  # pcap, log, metadata
):
    """
    Upload forensic evidence: PCAP files, logs, or metadata.
    
    Supported formats:
    - PCAP: .pcap, .pcapng, .cap
    - Logs: .txt, .log
    - Metadata: .json
    """
    # ... single implementation for all types
```

**Add magic number validation:**

```python
def validate_pcap_magic(data: bytes) -> bool:
    """Validate PCAP file using magic number."""
    VALID_MAGICS = {
        b'\xa1\xb2\xc3\xd4',  # Little-endian
        b'\xd4\xc3\xb2\xa1',  # Big-endian
        b'\xa1\xb2\x3c\x4d',  # Nanoseconds LE
        b'\x4d\x3c\xb2\xa1',  # Nanoseconds BE
    }
    return data[:4] in VALID_MAGICS
```

---

## Issue 5: Duplicate & Conflicting Logic

### 5.1 Duplicate Fetcher Modules ❌ CRITICAL TECHNICAL DEBT

**Problem:**

Two nearly identical fetcher modules exist:

| File | Lines | Function | Status |
|------|-------|----------|--------|
| `fetcher.py` | 325 | Relay fetching | Unknown if used |
| `fetcher_enhanced.py` | ~325 | Relay fetching (enhanced?) | Unknown if used |

**Key question:** Which one is actually imported and used?

```python
# In main.py - which one is imported?
from .fetcher import fetch_and_store_relays  # Line 21
# OR
from .fetcher_enhanced import fetch_and_store_relays  # Not found
```

**Finding:** Only `fetcher.py` is imported, so `fetcher_enhanced.py` is **dead code**.

### 5.2 Multiple Scoring Modules (5 total!) ❌ CRITICAL CONFUSION

**Modules found:**

```
1. correlator.py          - Entry-exit correlation scoring
2. risk_engine.py         - Risk scoring
3. confidence_calculator.py  - Confidence scoring
4. confidence_evolution.py   - Confidence tracking over time
5. probabilistic_paths.py    - Probabilistic path inference
```

**Assessment:** It's unclear which module is the "source of truth"

**Code snippet:**
```python
# From main.py imports (Line 21-27)
from .correlator import generate_candidate_paths, top_candidate_paths
from .pcap_analyzer import analyze_pcap_file
from .forensic_pcap import analyze_pcap_forensic, flow_evidence_to_scoring_metrics
from .probabilistic_paths import (
    generate_probabilistic_paths,
    ProbabilisticPathInference,
)
```

**Questions:**
- ❓ Is `generate_candidate_paths` used?
- ❓ Is `generate_probabilistic_paths` used?
- ❓ Which one produces the final hypotheses?
- ❓ Why does `confidence_calculator.py` exist if confidence is hardcoded?
- ❓ Why does `confidence_evolution.py` exist if confidence never changes?

### 5.3 Impact

**Dead code increases:**
- Maintenance burden
- Confusion during debugging
- Memory usage at runtime
- Risk of bugs in unused code spreading

**Example:** If someone fixes a bug in `fetcher_enhanced.py`, it will never be used.

### 5.4 Recommended Fix

**Audit all modules:**

```bash
# Check which modules are actually imported/used
grep -r "from .fetcher_enhanced" backend/app/
grep -r "from .confidence_calculator" backend/app/
grep -r "from .risk_engine" backend/app/
grep -r "generate_candidate_paths" backend/app/
grep -r "generate_probabilistic_paths" backend/app/
```

**Then delete dead code:**

```bash
# If fetcher_enhanced is unused
rm backend/app/fetcher_enhanced.py

# If confidence_calculator is unused
rm backend/app/confidence_calculator.py

# If confidence_evolution is unused
rm backend/app/confidence_evolution.py
```

**Or consolidate into single modules:**

```
backend/app/
  fetcher.py (consolidated relay fetching)
  scoring.py (all scoring logic)
  analyzer.py (all analysis logic)
```

---

## Summary Table: All Issues

| Issue | Severity | Status | Fix Effort |
|-------|----------|--------|-----------|
| 1. App routing | 🟢 LOW | ✅ WORKING | - |
| 2. MongoDB connection | 🔴 HIGH | ❌ INCONSISTENT | HIGH |
| 3. Scoring logic | 🔴 HIGH | ❌ MIXED/HARDCODED | HIGH |
| 4. PCAP module | 🟡 MEDIUM | ⚠️ PARTIAL | MEDIUM |
| 5. Duplicate code | 🟡 MEDIUM | ❌ DEAD CODE | MEDIUM |

---

## Recommended Fix Priority

**Phase 1 (CRITICAL) - Do First:**
1. Fix MongoDB connection inconsistency (Issue 2)
2. Implement unified scoring pipeline (Issue 3)

**Phase 2 (IMPORTANT) - Do Next:**
3. Consolidate PCAP upload endpoints (Issue 4)
4. Audit and remove dead code (Issue 5)

**Phase 3 (NICE TO HAVE) - Do Later:**
5. Add comprehensive error handling
6. Add API logging for debugging

---

## Test Recommendations

**To verify fixes work:**

```bash
# Test MongoDB connection with fallback
curl -X GET http://localhost:8000/api/relays
# Should work even if MongoDB is on localhost:27017

# Test confidence variation
curl -X POST http://localhost:8000/api/evidence/upload \
  -F "file=@large.pcap" -F "caseId=test1"
curl -X POST http://localhost:8000/api/evidence/upload \
  -F "file=@large.pcap" -F "caseId=test1"  # Same case again
# Should show improved confidence on 2nd upload

# Test PCAP upload endpoint consistency
curl -X POST http://localhost:8000/api/evidence/upload \
  -F "file=@test.pcap"
# Should have clear error message if PCAP invalid
```

---

**Report Status:** ✅ ANALYSIS COMPLETE

**Date Generated:** 2025-12-20  
**Next Step:** Review findings and implement Phase 1 fixes
