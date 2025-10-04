import requests
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = 'http://localhost:8001/api'  # Match Django's running port

def check_server():
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

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

def test_create_offer():
    if not check_server():
        print("❌ Server is not running!")
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
    print("\n2. Creating test CSV...")
    csv_content = """name,role,company,industry,location,linkedin_bio
John Doe,CEO,TechCorp,B2B SaaS,New York,Experienced CEO with 15 years in SaaS
Jane Smith,Head of Sales,DataFlow,B2B SaaS,San Francisco,10+ years leading enterprise sales teams
Mike Wilson,Manager,CloudTech,Healthcare,London,Technology implementation specialist"""
    
    with open('test_leads.csv', 'w') as f:
        f.write(csv_content)
    return 'test_leads.csv'

def test_upload_leads(csv_file):
    print("\n3. Testing Lead Upload...")
    with open(csv_file, 'rb') as f:
        response = session.post(f'{BASE_URL}/leads/upload/', files={'file': f})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def test_score_leads():
    print("\n4. Testing Lead Scoring...")
    response = session.post(f'{BASE_URL}/leads/score/')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def test_get_results():
    print("\n5. Testing Results Retrieval...")
    response = session.get(f'{BASE_URL}/leads/results/')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.ok

def main():
    print("Starting API Tests...")
    
    # Run tests
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
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup
    os.remove(csv_file)

if __name__ == "__main__":
    main()
