#!/usr/bin/env python3
"""
Phase 1 Backend Implementation Tests
Tests unified database module, scoring pipeline, and module integration
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test all new and modified module imports"""
    print("\n" + "="*70)
    print("TEST 1: Module Imports")
    print("="*70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1.1: Database module
    tests_total += 1
    try:
        from app.database import get_db, MongoDBManager
        print("✓ database module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ database module failed: {e}")
    
    # Test 1.2: Scoring pipeline
    tests_total += 1
    try:
        from app.scoring_pipeline import UnifiedScoringEngine, ScoringFactors
        print("✓ scoring_pipeline module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ scoring_pipeline module failed: {e}")
    
    # Test 1.3: Main module
    tests_total += 1
    try:
        from app.main import app
        print("✓ main module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ main module failed: {e}")
    
    # Test 1.4: Correlator module
    tests_total += 1
    try:
        from app.correlator import get_database as corr_get_db
        print("✓ correlator module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ correlator module failed: {e}")
    
    # Test 1.5: Fetcher module
    tests_total += 1
    try:
        from app.fetcher import db as fetcher_db
        print("✓ fetcher module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ fetcher module failed: {e}")
    
    # Test 1.6: Auth module
    tests_total += 1
    try:
        from app.auth import router as auth_router
        print("✓ auth module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ auth module failed: {e}")
    
    print(f"\n✓ Imports: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_deprecated_modules():
    """Test that deprecated modules raise ImportError"""
    print("\n" + "="*70)
    print("TEST 2: Deprecated Module Guards")
    print("="*70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 2.1: fetcher_enhanced should fail
    tests_total += 1
    try:
        from app.fetcher_enhanced import fetch_and_store_relays
        print("✗ fetcher_enhanced should have raised ImportError")
    except ImportError as e:
        print(f"✓ fetcher_enhanced correctly raises ImportError")
        tests_passed += 1
    except Exception as e:
        print(f"✗ fetcher_enhanced raised wrong error: {e}")
    
    # Test 2.2: confidence_calculator should fail
    tests_total += 1
    try:
        from app.scoring.confidence_calculator import calculate_confidence
        print("✗ confidence_calculator should have raised ImportError")
    except ImportError as e:
        print(f"✓ confidence_calculator correctly raises ImportError")
        tests_passed += 1
    except Exception as e:
        print(f"✗ confidence_calculator raised wrong error: {e}")
    
    # Test 2.3: confidence_evolution should fail
    tests_total += 1
    try:
        from app.scoring.confidence_evolution import ConfidenceEvolutionTracker
        print("✗ confidence_evolution should have raised ImportError")
    except ImportError as e:
        print(f"✓ confidence_evolution correctly raises ImportError")
        tests_passed += 1
    except Exception as e:
        print(f"✗ confidence_evolution raised wrong error: {e}")
    
    print(f"\n✓ Deprecated Guards: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_scoring_pipeline():
    """Test scoring pipeline with various evidence counts"""
    print("\n" + "="*70)
    print("TEST 3: Scoring Pipeline Logic")
    print("="*70)
    
    from app.scoring_pipeline import UnifiedScoringEngine, ScoringFactors
    
    tests_passed = 0
    tests_total = 0
    
    # Test cases: (evidence_count, timing, overlap, expected_confidence)
    test_cases = [
        (100000, 0.9, 0.8, "High", "Very high evidence with strong timing"),
        (50000, 0.8, 0.7, "High", "High evidence threshold"),
        (20000, 0.5, 0.4, "Medium", "Medium-high evidence, lower timing/overlap"),
        (5000, 0.6, 0.5, "Medium", "Moderate evidence"),
        (1000, 0.4, 0.3, "Low", "Weak evidence"),
        (100, 0.2, 0.1, "Low", "Very weak evidence"),
    ]
    
    for evidence, timing, overlap, expected, description in test_cases:
        tests_total += 1
        factors = ScoringFactors(
            evidence_count=evidence,
            timing_similarity=timing,
            session_overlap=overlap,
            additional_evidence_count=0,
            prior_uploads=0
        )
        confidence = UnifiedScoringEngine.compute_confidence_level(factors)
        
        if confidence == expected:
            print(f"✓ {description}: {confidence} (evidence={evidence})")
            tests_passed += 1
        else:
            print(f"✗ {description}: got {confidence}, expected {expected}")
    
    print(f"\n✓ Scoring Pipeline: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_scoring_methods():
    """Test individual scoring methods"""
    print("\n" + "="*70)
    print("TEST 4: Scoring Pipeline Methods")
    print("="*70)
    
    from app.scoring_pipeline import UnifiedScoringEngine, ScoringFactors
    
    tests_passed = 0
    tests_total = 0
    
    # Test 4.1: Evidence scoring
    tests_total += 1
    try:
        score = UnifiedScoringEngine._score_evidence_volume(100000)
        if 0.9 <= score <= 1.0:
            print(f"✓ Evidence scoring for 100k: {score:.2f}")
            tests_passed += 1
        else:
            print(f"✗ Evidence scoring for 100k out of range: {score}")
    except Exception as e:
        print(f"✗ Evidence scoring failed: {e}")
    
    # Test 4.2: Confidence bar width
    tests_total += 1
    try:
        width_high = UnifiedScoringEngine.get_confidence_bar_width("High")
        width_medium = UnifiedScoringEngine.get_confidence_bar_width("Medium")
        width_low = UnifiedScoringEngine.get_confidence_bar_width("Low")
        
        if width_high == 85 and width_medium == 55 and width_low == 25:
            print(f"✓ Confidence bar widths: High={width_high}, Medium={width_medium}, Low={width_low}")
            tests_passed += 1
        else:
            print(f"✗ Bar widths incorrect: High={width_high}, Medium={width_medium}, Low={width_low}")
    except Exception as e:
        print(f"✗ Bar width calculation failed: {e}")
    
    # Test 4.3: False positive rate
    tests_total += 1
    try:
        fpr_high = UnifiedScoringEngine.estimate_false_positive_rate("High", 100000)
        fpr_medium = UnifiedScoringEngine.estimate_false_positive_rate("Medium", 100000)
        fpr_low = UnifiedScoringEngine.estimate_false_positive_rate("Low", 100000)
        
        if 0 < fpr_high < fpr_medium < fpr_low < 1:
            print(f"✓ False positive rates: High={fpr_high:.1%}, Medium={fpr_medium:.1%}, Low={fpr_low:.1%}")
            tests_passed += 1
        else:
            print(f"✗ FPR ordering incorrect")
    except Exception as e:
        print(f"✗ FPR calculation failed: {e}")
    
    # Test 4.4: Uncertainty margins
    tests_total += 1
    try:
        margins = UnifiedScoringEngine.compute_uncertainty_margins("High", 100000)
        if "lower_margin" in margins and "upper_margin" in margins:
            print(f"✓ Uncertainty margins for High: {margins}")
            tests_passed += 1
        else:
            print(f"✗ Uncertainty margins missing keys")
    except Exception as e:
        print(f"✗ Uncertainty margins failed: {e}")
    
    print(f"\n✓ Scoring Methods: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_database_fallback():
    """Test database fallback URLs"""
    print("\n" + "="*70)
    print("TEST 5: Database Fallback URLs")
    print("="*70)
    
    from app.database import MongoDBManager
    
    tests_passed = 0
    tests_total = 0
    
    manager = MongoDBManager()
    
    # Test 5.1: Get all fallback URLs
    tests_total += 1
    try:
        urls = manager.get_mongo_urls()
        if isinstance(urls, list) and len(urls) >= 5:
            print(f"✓ Got {len(urls)} fallback URLs:")
            for i, url in enumerate(urls[:3], 1):
                print(f"  {i}. {url}")
            if len(urls) > 3:
                print(f"  ... and {len(urls)-3} more")
            tests_passed += 1
        else:
            print(f"✗ Expected at least 5 URLs, got {len(urls)}")
    except Exception as e:
        print(f"✗ Failed to get URLs: {e}")
    
    # Test 5.2: Check environment variable priority
    tests_total += 1
    try:
        os.environ['MONGO_URL'] = 'mongodb://custom:27017/testdb'
        manager2 = MongoDBManager()
        urls = manager2.get_mongo_urls()
        if urls[0] == 'mongodb://custom:27017/testdb':
            print(f"✓ Environment variable has priority: {urls[0]}")
            tests_passed += 1
        else:
            print(f"✗ Env var not prioritized: {urls[0]}")
        del os.environ['MONGO_URL']
    except Exception as e:
        print(f"✗ Env var test failed: {e}")
    
    print(f"\n✓ Database Fallback: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def main():
    """Run all Phase 1 tests"""
    print("\n" + "="*70)
    print("PHASE 1 BACKEND IMPLEMENTATION TESTS")
    print("="*70)
    
    results = []
    
    # Run all test suites
    results.append(("Module Imports", test_imports()))
    results.append(("Deprecated Guards", test_deprecated_modules()))
    results.append(("Scoring Pipeline Logic", test_scoring_pipeline()))
    results.append(("Scoring Methods", test_scoring_methods()))
    results.append(("Database Fallback", test_database_fallback()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_suites = len(results)
    passed_suites = sum(1 for _, passed in results if passed)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    print(f"Result: {passed_suites}/{total_suites} test suites passed")
    print(f"{'='*70}\n")
    
    return passed_suites == total_suites


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
