from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Lead, Offer
from .utils import calculate_rule_score

class LeadScoringTests(APITestCase):
    def setUp(self):
        self.offer = Offer.objects.create(
            name="Test Product",
            value_props=["test1", "test2"],
            ideal_use_cases=["B2B SaaS"]
        )
        
        self.lead = Lead.objects.create(
            name="Test User",
            role="CEO",
            company="Test Co",
            industry="B2B SaaS",
            location="Test Location",
            linkedin_bio="Test Bio"
        )

    def test_scoring_endpoint(self):
        response = self.client.post('/api/leads/score/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_results_endpoint(self):
        response = self.client.get('/api/leads/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_decision_maker_scoring(self):
        lead = {
            'role': 'CEO',
            'industry': 'B2B SaaS',
            'name': 'Test User',
            'company': 'Test Co',
            'location': 'NY',
            'linkedin_bio': 'Test bio'
        }
        offer = {
            'ideal_use_cases': ['B2B SaaS'],
            'value_props': ['Test']
        }
        
        score, reasons = calculate_rule_score(lead, offer)
        self.assertEqual(score, 50)  # 20 (role) + 20 (industry) + 10 (completeness)

    def test_incomplete_data_scoring(self):
        lead = {
            'role': 'Manager',
            'industry': 'B2B SaaS'
        }
        offer = {
            'ideal_use_cases': ['B2B SaaS'],
            'value_props': ['Test']
        }
        
        score, reasons = calculate_rule_score(lead, offer)
        self.assertEqual(score, 30)  # 10 (role) + 20 (industry) + 0 (incomplete)
