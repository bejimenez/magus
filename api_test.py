"""
Simple script to test the Name Generator API
Run this after starting the FastAPI server
"""

import requests
import json
from typing import Dict, Any, Optional

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, method: str = "GET", data: Optional[Dict[Any, Any]] = None) -> None:
    """Test a single API endpoint and print results."""
    url = f"{BASE_URL}{endpoint}"

    print(f"\n{'='*50}")
    print(f"Testing {method} {endpoint}")
    print(f"{'='*50}")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print("Error Response:")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Is the server running?")
    except Exception as e:
        print(f"Error: {str(e)}")

def run_tests():
    """Run a series of API tests"""
    print("Starting API Tests...")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    
    # Test 1: Root endpoint
    test_endpoint("/")
    
    # Test 2: Health check
    test_endpoint("/health")
    
    # Test 3: Get available cultures
    test_endpoint("/cultures")
    
    # Test 4: Generate a single generic name
    test_endpoint("/generate", "POST", {
        "culture": "generic",
        "count": 1
    })
    
    # Test 5: Generate multiple elvish female names
    test_endpoint("/generate", "POST", {
        "culture": "elvish",
        "gender": "female",
        "count": 3
    })
    
    # Test 6: Generate norse male names
    test_endpoint("/generate", "POST", {
        "culture": "norse",
        "gender": "male",
        "count": 2
    })
    
    # Test 7: Test error handling - invalid culture
    test_endpoint("/generate", "POST", {
        "culture": "invalid_culture",
        "count": 1
    })
    
    # Test 8: Test error handling - too many names
    test_endpoint("/generate", "POST", {
        "culture": "generic",
        "count": 100  # Should fail - limit is 50
    })
    
    print(f"\n{'='*50}")
    print("Tests completed!")
    print(f"{'='*50}")

if __name__ == "__main__":
    run_tests()
