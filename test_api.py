"""
Comprehensive API Testing Script for Lead Scoring Backend

This script tests all major endpoints of the lead scoring API:
1. POST /api/offer/ - Create product/offer with value props
2. POST /api/leads/upload/ - Upload CSV file with lead data
3. POST /api/leads/score/ - Run hybrid scoring pipeline (rule-based + AI)
4. GET /api/leads/results/ - Retrieve paginated scored results

Usage:
    python test_api.py

Requirements:
    - Backend server running on localhost:8001
    - Python packages: requests
    - Valid OpenAI API key configured in .env (for AI scoring)

Features:
    - Automatic server availability check
    - HTTP retry strategy for transient failures
    - Detailed response logging
    - Automatic test data cleanup

Author: Lead Scoring Backend Team
"""

import requests
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = 'http://localhost:8001/api'  # Match Django's running port

def check_server():
    """
    Verify that the backend server is running and accessible.
    Attempts connection up to 3 times with 2-second delays.
    
    Returns:
        bool: True if server is accessible, False otherwise
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:8001/admin/')
            if response.status_code == 200 or response.status_code == 404:
                return True
        except requests.exceptions.ConnectionError:
            if attempt < max_attempts - 1:
                print(f"Server not ready, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
            continue
    return False

# Configure retry strategy for handling transient network errors
retry_strategy = Retry(
    total=3,  # Maximum retry attempts
    backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # Retry on server errors
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

def test_create_offer():
    """
    Test POST /api/offer/ endpoint.
    Creates a sample product offer with value propositions and ideal use cases.
    
    Returns:
        bool: True if offer creation succeeds, False otherwise
    """
    if not check_server():
        print(" Server is not running!")
        return False
    print("\n1. Testing Offer Creation...")
    offer_data = {
        "name": "AI Outreach Automation",
        "value_props": ["24/7 outreach", "6x more meetings"],
        "ideal_use_cases": ["B2B SaaS mid-market"]
    }
    response = session.post(f'{BASE_URL}/offer/', json=offer_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def create_test_csv():
    """
    Generate a test CSV file with sample lead data.
    Creates leads with varying roles (CEO, Head of Sales, Manager) and industries.
    
    Returns:
        str: Filename of the created CSV file
    """
    print("\n2. Creating test CSV...")
    csv_content = """name,role,company,industry,location,linkedin_bio
John Doe,CEO,TechCorp,B2B SaaS,New York,Experienced CEO with 15 years in SaaS
Jane Smith,Head of Sales,DataFlow,B2B SaaS,San Francisco,10+ years leading enterprise sales teams
Mike Wilson,Manager,CloudTech,Healthcare,London,Technology implementation specialist"""
    
    with open('test_leads.csv', 'w') as f:
        f.write(csv_content)
    return 'test_leads.csv'

def test_upload_leads(csv_file):
    """
    Test POST /api/leads/upload/ endpoint.
    Uploads a CSV file containing lead information.
    
    Args:
        csv_file (str): Path to the CSV file to upload
    
    Returns:
        bool: True if upload succeeds, False otherwise
    """
    print("\n3. Testing Lead Upload...")
    with open(csv_file, 'rb') as f:
        response = session.post(f'{BASE_URL}/leads/upload/', files={'file': f})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def test_score_leads():
    """
    Test POST /api/leads/score/ endpoint.
    Triggers the hybrid scoring pipeline (rule-based + AI) for all unscored leads.
    
    Returns:
        bool: True if scoring succeeds, False otherwise
    """
    print("\n4. Testing Lead Scoring...")
    response = session.post(f'{BASE_URL}/leads/score/')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def test_get_results():
    """
    Test GET /api/leads/results/ endpoint.
    Retrieves paginated results of scored leads with intent classification.
    
    Returns:
        bool: True if results retrieval succeeds, False otherwise
    """
    print("\n5. Testing Results Retrieval...")
    response = session.get(f'{BASE_URL}/leads/results/')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def main():
    """
    Main test execution flow.
    Runs all API tests sequentially and reports success/failure.
    Automatically cleans up test data on completion.
    """
    print("Starting API Tests...")
    
    # Run tests in sequence
    if not test_create_offer():
        print("Offer creation failed!")
        return
    
    csv_file = create_test_csv()
    if not test_upload_leads(csv_file):
        print("Lead upload failed!")
        return
    
    if not test_score_leads():
        print("Lead scoring failed!")
        return
    
    if not test_get_results():
        print("Results retrieval failed!")
        return
    
    print("\n All tests completed successfully!")
    
    # Cleanup test artifacts
    os.remove(csv_file)

if __name__ == "__main__":
    main()