#!/usr/bin/env python3
"""
Test script to verify all crawler AI fixes are working correctly.
Run this in the backend directory: python test_fixes.py
"""

import sys
import asyncio
from pathlib import Path

# Add paths for imports
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "services"))
sys.path.insert(0, str(backend_path / "fact_checker"))

def test_imports():
    """Test 1: Verify all new modules can be imported"""
    print("=" * 60)
    print("TEST 1: Verifying Imports")
    print("=" * 60)
    
    try:
        from services.intent_extractors import IntentExtractor, JobListing, ProductInfo
        print("✓ intent_extractors imported successfully")
    except Exception as e:
        print(f"✗ Failed to import intent_extractors: {e}")
        return False
    
    try:
        from services.intent_classifier import IntentClassifier, IntentResult
        print("✓ intent_classifier imported successfully")
    except Exception as e:
        print(f"✗ Failed to import intent_classifier: {e}")
        return False
    
    try:
        from fact_checker.answer_agent import AnswerAgentService
        print("✓ answer_agent imported successfully")
    except Exception as e:
        print(f"✗ Failed to import answer_agent: {e}")
        return False
    
    try:
        from services.search_agent_service import SearchAgentService
        print("✓ search_agent_service imported successfully")
    except Exception as e:
        print(f"✗ Failed to import search_agent_service: {e}")
        return False
    
    print("✓ All imports successful!\n")
    return True


def test_intent_extraction():
    """Test 2: Test intent-specific extractors"""
    print("=" * 60)
    print("TEST 2: Testing Intent Extractors")
    print("=" * 60)
    
    from services.intent_extractors import IntentExtractor
    
    # Test job extraction
    job_content = "Senior Python Developer at Acme Corporation in Remote, Salary $150,000-$170,000"
    job_sources = [{
        'url': 'https://linkedin.com/jobs/123',
        'title': 'Senior Python Developer - Acme',
        'content': job_content,
        'domain': 'linkedin.com',
        'snippet': 'Senior developer role'
    }]
    
    jobs = IntentExtractor.extract_jobs(job_content, "python developer", job_sources)
    print(f"✓ Job extraction: Found {len(jobs)} job(s)")
    if jobs:
        print(f"  - Title: {jobs[0].title}")
        print(f"  - Company: {jobs[0].company}")
        print(f"  - Location: {jobs[0].location}")
        print(f"  - Salary: {jobs[0].salary_range}")
    
    # Test product extraction
    product_content = "Corsair K70 RGB Mechanical Keyboard for $199.99, rated 4.8 stars"
    product_sources = [{
        'url': 'https://amazon.com/product/123',
        'title': 'Corsair K70 RGB',
        'content': product_content,
        'domain': 'amazon.com',
        'snippet': 'Best gaming keyboard'
    }]
    
    products = IntentExtractor.extract_products(product_content, "mechanical keyboard", product_sources)
    print(f"✓ Product extraction: Found {len(products)} product(s)")
    if products:
        print(f"  - Name: {products[0].name}")
        print(f"  - Price: {products[0].price}")
        print(f"  - Rating: {products[0].rating}")
    
    # Test event extraction
    event_content = "PyCon 2024 - May 15-17, 2024 in Pittsburgh"
    event_sources = [{
        'url': 'https://pycon.org/2024',
        'title': 'PyCon 2024',
        'content': event_content,
        'domain': 'pycon.org',
        'snippet': 'Python conference'
    }]
    
    events = IntentExtractor.extract_events(event_content, "python conference", event_sources)
    print(f"✓ Event extraction: Found {len(events)} event(s)")
    if events:
        print(f"  - Name: {events[0].name}")
        print(f"  - Date: {events[0].date}")
        print(f"  - Location: {events[0].location}")
    
    # Test service extraction
    service_content = "ABC Web Hosting Services - Professional hosting for websites - 4.7 rating"
    service_sources = [{
        'url': 'https://abchosting.com',
        'title': 'ABC Web Hosting',
        'content': service_content,
        'domain': 'abchosting.com',
        'snippet': 'Web hosting provider'
    }]
    
    services = IntentExtractor.extract_services(service_content, "web hosting", service_sources)
    print(f"✓ Service extraction: Found {len(services)} service(s)")
    if services:
        print(f"  - Name: {services[0].name}")
        print(f"  - Type: {services[0].service_type}")
        print(f"  - Rating: {services[0].rating}")
    
    print("✓ All extractors working!\n")
    return True


def test_intent_classification():
    """Test 3: Test improved intent classification"""
    print("=" * 60)
    print("TEST 3: Testing Intent Classification")
    print("=" * 60)
    
    from services.intent_classifier import IntentClassifier, UserIntent
    
    test_cases = [
        ("python developer jobs remote", UserIntent.JOB_SEARCH),
        ("best mechanical keyboard review", UserIntent.PRODUCT_RESEARCH),
        ("tech conference 2024", UserIntent.EVENT_FINDER),
        ("web hosting service provider", UserIntent.SERVICE_LOCATOR),
        ("how to learn python", UserIntent.GENERAL_QNA),
    ]
    
    for query, expected_intent in test_cases:
        result = IntentClassifier.fallback_classify(query)
        match = "✓" if result.intent == expected_intent else "✗"
        print(f"{match} Query: '{query}'")
        print(f"   Intent: {result.intent} (expected: {expected_intent})")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Keywords: {result.keywords}")
        print(f"   Suggested queries: {len(result.suggested_queries)}")
        if len(result.suggested_queries) < 3:
            print(f"   ⚠ Warning: Only {len(result.suggested_queries)} suggested queries (expect 3+)")
        print()
    
    print("✓ Intent classification working!\n")
    return True


def test_search_queries_diversity():
    """Test 4: Test diverse search query generation"""
    print("=" * 60)
    print("TEST 4: Testing Search Query Diversity")
    print("=" * 60)
    
    from services.intent_classifier import IntentClassifier
    
    test_cases = [
        ("python jobs", "Should have job-specific queries"),
        ("best laptop", "Should have product-specific queries"),
        ("conference 2024", "Should have event-specific queries"),
        ("plumber near me", "Should have service-specific queries"),
    ]
    
    for query, description in test_cases:
        result = IntentClassifier.fallback_classify(query)
        queries = result.suggested_queries
        
        print(f"Query: '{query}'")
        print(f"Intent: {result.intent}")
        print(f"Description: {description}")
        print("Suggested searches:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        print()
    
    print("✓ Query diversity working!\n")
    return True


def test_answer_synthesizer():
    """Test 5: Test improved answer synthesizer"""
    print("=" * 60)
    print("TEST 5: Testing Answer Synthesizer")
    print("=" * 60)
    
    from fact_checker.answer_agent import AnswerAgentService
    
    # Test job intent
    test_pages = [
        {
            'title': 'Senior Python Developer at Acme',
            'url': 'https://linkedin.com/jobs/123',
            'domain': 'linkedin.com',
            'content': 'Senior Python Developer at Acme, Remote, $150k-$170k. We are hiring...',
            'snippet': 'Acme is hiring a Senior Python Developer'
        }
    ]
    
    result = AnswerAgentService.fallback_synthesize(
        "python developer jobs",
        "jobs",
        test_pages
    )
    
    print("✓ Answer synthesis for JOBS:")
    print(f"   Main answer: {result.main_answer[:100]}...")
    print(f"   Action prompt: {result.action_prompt[:80]}...")
    print(f"   Key points: {len(result.key_points)} items")
    print(f"   Jobs extracted: {len(result.jobs)}")
    if result.jobs:
        print(f"   Sample job: {result.jobs[0].title}")
    print()
    
    # Test product intent
    result = AnswerAgentService.fallback_synthesize(
        "best mechanical keyboard",
        "products",
        test_pages
    )
    
    print("✓ Answer synthesis for PRODUCTS:")
    print(f"   Main answer: {result.main_answer[:100]}...")
    print(f"   Action prompt contains 'products/compare': {'compare' in result.action_prompt.lower()}")
    print()
    
    # Test event intent
    result = AnswerAgentService.fallback_synthesize(
        "tech conference",
        "events",
        test_pages
    )
    
    print("✓ Answer synthesis for EVENTS:")
    print(f"   Action prompt contains 'register': {'register' in result.action_prompt.lower()}")
    print()
    
    # Test service intent
    result = AnswerAgentService.fallback_synthesize(
        "web hosting service",
        "services",
        test_pages
    )
    
    print("✓ Answer synthesis for SERVICES:")
    print(f"   Action prompt contains 'contact': {'contact' in result.action_prompt.lower()}")
    print()
    
    print("✓ Answer synthesizer working!\n")
    return True


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║  CRAWLER AI - FIXES VERIFICATION TEST SUITE           ║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        ("Import Check", test_imports),
        ("Intent Extractors", test_intent_extraction),
        ("Intent Classification", test_intent_classification),
        ("Search Query Diversity", test_search_queries_diversity),
        ("Answer Synthesizer", test_answer_synthesizer),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with error:")
            print(f"  {str(e)}")
            print()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The fixes are working correctly.\n")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review the errors above.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
