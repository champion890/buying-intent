import json
import requests

BASE_URL = 'http://localhost:8000/api'

# Test offer creation
offer_data = {
    "name": "AI Outreach Automation",
    "value_props": ["24/7 outreach", "6x more meetings"],
    "ideal_use_cases": ["B2B SaaS mid-market"]
}

# Create test CSV content
csv_content = """name,role,company,industry,location,linkedin_bio
John Doe,Head of Growth,TechCorp,B2B SaaS,New York,15+ years in SaaS growth
Jane Smith,CEO,DataFlow,Enterprise Software,London,Founded 2 AI companies
Mike Johnson,Sales Manager,CloudTech,B2B SaaS,Austin,10 years B2B sales"""

# Save test CSV
with open('test_leads.csv', 'w') as f:
    f.write(csv_content)

# Test API endpoints
def test_apis():
    # 1. Create offer
    offer_response = requests.post(f'{BASE_URL}/offer/', json=offer_data)
    print("Offer created:", offer_response.json())

    # 2. Upload leads
    with open('test_leads.csv', 'rb') as f:
        files = {'file': ('test_leads.csv', f)}
        upload_response = requests.post(f'{BASE_URL}/leads/upload/', files=files)
    print("Leads uploaded:", upload_response.json())

    # 3. Score leads
    score_response = requests.post(f'{BASE_URL}/leads/score/')
    print("Scoring completed:", score_response.json())

    # 4. Export results
    export_response = requests.get(f'{BASE_URL}/leads/export_csv/')
    with open('results.csv', 'wb') as f:
        f.write(export_response.content)
    print("Results exported to results.csv")

if __name__ == '__main__':
    test_apis()
