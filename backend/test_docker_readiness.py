#!/usr/bin/env python3
"""
Phase 1 Docker/Production Readiness Test
Validates that Phase 1 changes work in production environment setup
"""

import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))

def test_docker_environment_variable():
    """Test that MONGO_URL environment variable works in docker setup"""
    print("\n" + "="*70)
    print("TEST 1: Docker Environment Variable (Production Setup)")
    print("="*70)
    
    # Simulate docker-compose environment
    os.environ['MONGO_URL'] = 'mongodb://torunveil-mongo:27017/torunveil'
    
    try:
        from app.database import MongoDBManager
        
        # Create a fresh manager
        manager = MongoDBManager()
        urls = manager.get_mongo_urls()
        
        # Check that docker URL is first (from env var)
        if urls[0] == 'mongodb://torunveil-mongo:27017/torunveil':
            print("✓ Docker environment variable set correctly")
            print(f"  First URL: {urls[0]}")
            return True
        else:
            print(f"✗ Expected docker URL first, got: {urls[0]}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if 'MONGO_URL' in os.environ:
            del os.environ['MONGO_URL']


def test_main_py_imports():
    """Test that main.py can be imported with new modules"""
    print("\n" + "="*70)
    print("TEST 2: main.py Integration (FastAPI Server)")
    print("="*70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 2.1: Import main module
    tests_total += 1
    try:
        from app.main import app
        print("✓ main.py imports successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ main.py import failed: {e}")
        return False
    
    # Test 2.2: Check FastAPI app is created
    tests_total += 1
    try:
        if app is not None:
            print("✓ FastAPI app instance created")
            tests_passed += 1
        else:
            print("✗ FastAPI app is None")
    except Exception as e:
        print(f"✗ Error checking app: {e}")
    
    # Test 2.3: Check routes are registered
    tests_total += 1
    try:
        routes = [route.path for route in app.routes]
        if len(routes) > 5:
            print(f"✓ {len(routes)} routes registered")
            # Show sample routes
            for route in routes[:3]:
                print(f"  - {route}")
            tests_passed += 1
        else:
            print(f"✗ Too few routes ({len(routes)})")
    except Exception as e:
        print(f"✗ Error checking routes: {e}")
    
    print(f"\n✓ main.py Integration: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_scoring_in_context():
    """Test that scoring pipeline works in the context of main.py"""
    print("\n" + "="*70)
    print("TEST 3: Scoring Pipeline in Application Context")
    print("="*70)
    
    from app.scoring_pipeline import UnifiedScoringEngine, ScoringFactors
    
    tests_passed = 0
    tests_total = 0
    
    # Simulate realistic PCAP analysis scenario
    scenarios = [
        {
            "name": "Strong TOR correlation",
            "evidence": 85000,
            "timing": 0.88,
            "overlap": 0.75,
            "expected": "High"
        },
        {
            "name": "Moderate TOR correlation",
            "evidence": 12000,
            "timing": 0.65,
            "overlap": 0.55,
            "expected": "Medium"
        },
        {
            "name": "Weak correlation (noise)",
            "evidence": 300,
            "timing": 0.35,
            "overlap": 0.25,
            "expected": "Low"
        },
    ]
    
    for scenario in scenarios:
        tests_total += 1
        factors = ScoringFactors(
            evidence_count=scenario["evidence"],
            timing_similarity=scenario["timing"],
            session_overlap=scenario["overlap"],
            additional_evidence_count=0,
            prior_uploads=0
        )
        
        confidence = UnifiedScoringEngine.compute_confidence_level(factors)
        
        if confidence == scenario["expected"]:
            print(f"✓ {scenario['name']}: {confidence}")
            tests_passed += 1
        else:
            print(f"✗ {scenario['name']}: got {confidence}, expected {scenario['expected']}")
    
    print(f"\n✓ Scoring Pipeline Context: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_api_endpoint_mock():
    """Test that the upload endpoint can receive data correctly"""
    print("\n" + "="*70)
    print("TEST 4: API Endpoint Signature (Mock Test)")
    print("="*70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 4.1: Check endpoint exists and has correct signature
    tests_total += 1
    try:
        from app.main import upload_evidence
        import inspect
        
        sig = inspect.signature(upload_evidence)
        params = list(sig.parameters.keys())
        
        # Should have file and caseId parameters
        if 'file' in params and 'caseId' in params:
            print(f"✓ upload_evidence endpoint has correct parameters: {params}")
            tests_passed += 1
        else:
            print(f"✗ Missing parameters. Got: {params}")
    except Exception as e:
        print(f"✗ Error checking endpoint: {e}")
    
    # Test 4.2: Verify endpoint is async
    tests_total += 1
    try:
        import inspect
        from app.main import upload_evidence
        
        if inspect.iscoroutinefunction(upload_evidence):
            print("✓ upload_evidence is async (FastAPI compatible)")
            tests_passed += 1
        else:
            print("✗ upload_evidence is not async")
    except Exception as e:
        print(f"✗ Error checking async: {e}")
    
    print(f"\n✓ API Endpoint Signature: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def test_database_fallback_chain():
    """Test that database fallback chain matches docker-compose setup"""
    print("\n" + "="*70)
    print("TEST 5: Database Fallback Chain (Docker-Ready)")
    print("="*70)
    
    from app.database import MongoDBManager
    
    tests_passed = 0
    tests_total = 0
    
    manager = MongoDBManager()
    urls = manager.get_mongo_urls()
    
    # Test 5.1: Docker service name should be in fallback list
    tests_total += 1
    docker_urls = [u for u in urls if 'torunveil-mongo' in u or 'mongo:27017' in u or 'mongodb:27017' in u]
    if len(docker_urls) > 0:
        print(f"✓ Docker service URLs in fallback list: {docker_urls}")
        tests_passed += 1
    else:
        print(f"✗ No Docker service URLs found in: {urls}")
    
    # Test 5.2: Localhost fallback should exist
    tests_total += 1
    localhost_urls = [u for u in urls if 'localhost' in u or '127.0.0.1' in u]
    if len(localhost_urls) > 0:
        print(f"✓ Localhost fallback URLs exist: {len(localhost_urls)} variants")
        tests_passed += 1
    else:
        print(f"✗ No localhost URLs found")
    
    # Test 5.3: Kubernetes fallback should exist
    tests_total += 1
    k8s_urls = [u for u in urls if 'cluster.local' in u or 'svc' in u]
    if len(k8s_urls) > 0:
        print(f"✓ Kubernetes service URLs in fallback list: {k8s_urls}")
        tests_passed += 1
    else:
        print(f"✗ No Kubernetes URLs found (note: k8s support is optional)")
    
    print(f"\n✓ Database Fallback Chain: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total


def main():
    """Run all Docker/Production readiness tests"""
    print("\n" + "="*70)
    print("PHASE 1 DOCKER/PRODUCTION READINESS TESTS")
    print("="*70)
    
    results = []
    
    # Run all test suites
    results.append(("Docker Environment Variable", test_docker_environment_variable()))
    results.append(("main.py Integration", test_main_py_imports()))
    results.append(("Scoring Pipeline Context", test_scoring_in_context()))
    results.append(("API Endpoint Signature", test_api_endpoint_mock()))
    results.append(("Database Fallback Chain", test_database_fallback_chain()))
    
    # Summary
    print("\n" + "="*70)
    print("DOCKER READINESS TEST SUMMARY")
    print("="*70)
    
    total_suites = len(results)
    passed_suites = sum(1 for _, passed in results if passed)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    print(f"Result: {passed_suites}/{total_suites} test suites passed")
    print(f"{'='*70}")
    
    if passed_suites == total_suites:
        print("\n✅ Phase 1 is DOCKER-READY!")
        print("\nNext steps:")
        print("1. Start Docker containers: docker compose -f infra/docker-compose.yml up")
        print("2. Test API: curl http://localhost:8000/api/analysis")
        print("3. Backend should connect to: mongodb://torunveil-mongo:27017/torunveil")
    else:
        print("\n⚠️  Some tests failed. Review output above.")
    
    print()
    return passed_suites == total_suites


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
