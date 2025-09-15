#!/usr/bin/env python3
"""
Test script to verify API key authentication.
"""

import requests
import sys

# API configuration
API_BASE_URL = "http://127.0.0.1:8058"
API_KEY = "J_qfzc5WsTZ5GgyyOhFGplfI7zoDSFrY0XqTitDadmE"

def test_health_endpoint():
    """Test health endpoint (should not require API key)."""
    print("Testing health endpoint...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Health endpoint accessible without API key")
    else:
        print("  ✗ Health endpoint failed")
    return response.status_code == 200

def test_without_api_key():
    """Test protected endpoint without API key (should fail)."""
    print("\nTesting protected endpoint without API key...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "Hello"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 401:
        print("  ✓ Correctly rejected request without API key")
        return True
    else:
        print(f"  ✗ Expected 401, got {response.status_code}")
        return False

def test_with_invalid_api_key():
    """Test protected endpoint with invalid API key (should fail)."""
    print("\nTesting protected endpoint with invalid API key...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "Hello"},
        headers={"Authorization": "Bearer invalid-key-12345"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 401:
        print("  ✓ Correctly rejected request with invalid API key")
        return True
    else:
        print(f"  ✗ Expected 401, got {response.status_code}")
        return False

def test_with_valid_api_key():
    """Test protected endpoint with valid API key (should succeed)."""
    print("\nTesting protected endpoint with valid API key...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "What is RAG?"},
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Successfully authenticated with valid API key")
        data = response.json()
        print(f"  Response: {data.get('message', '')[:100]}...")
        return True
    else:
        print(f"  ✗ Expected 200, got {response.status_code}")
        if response.text:
            print(f"  Error: {response.text}")
        return False

def test_search_endpoints():
    """Test search endpoints with API key."""
    print("\nTesting search endpoints with API key...")
    
    endpoints = [
        ("/search/vector", {"query": "test", "limit": 5}),
        ("/documents", None)
    ]
    
    all_passed = True
    for endpoint, data in endpoints:
        if data:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
        else:
            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
        
        print(f"  {endpoint}: Status {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"    ✓ Endpoint accessible with API key")
        else:
            print(f"    ✗ Failed with status {response.status_code}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests."""
    print("=" * 60)
    print("API Key Authentication Test Suite")
    print("=" * 60)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"\n✗ API is not running at {API_BASE_URL}")
        print("  Please start the API with: python -m agent.api")
        return 1
    
    tests = [
        test_health_endpoint,
        test_without_api_key,
        test_with_invalid_api_key,
        test_with_valid_api_key,
        test_search_endpoints
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! API key authentication is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())