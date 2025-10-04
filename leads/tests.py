from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Lead, Offer
from .utils import calculate_rule_score

class LeadScoringTests(APITestCase):
    """
    Test suite for lead scoring API endpoints and rule-based scoring logic.
    Tests the hybrid scoring system components and API functionality.
    """
    
    def setUp(self):
        """
        Set up test data before each test method.
        Creates a test offer and lead for use in test cases.
        """
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

    def test_offer_creation(self):
        """Test that offers can be created via API."""
        response = self.client.post('/api/offer/', {
            'name': 'New Product',
            'value_props': ['prop1', 'prop2'],
            'ideal_use_cases': ['B2B SaaS', 'Enterprise']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')

    def test_scoring_endpoint(self):
        """
        Test the hybrid scoring endpoint.
        Verifies that scoring returns results with proper structure.
        """
        response = self.client.post('/api/leads/score/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('total_scored', response.data)
        self.assertIn('scoring_method', response.data)

    def test_scoring_without_offer(self):
        """
        Test scoring fails gracefully when no offer exists.
        Should return 400 Bad Request with helpful error message.
        """
        Offer.objects.all().delete()
        response = self.client.post('/api/leads/score/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_results_endpoint(self):
        """
        Test results endpoint returns scored leads.
        Verifies pagination structure is present.
        """
        response = self.client.get('/api/leads/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

    def test_decision_maker_scoring(self):
        """
        Test rule-based scoring for decision maker roles.
        CEO with exact ICP match and complete profile should score 50 points.
        """
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
        self.assertEqual(len(reasons), 3)
        self.assertIn('Decision maker role', reasons[0])
        self.assertIn('Exact ICP match', reasons[1])
        self.assertIn('Complete profile', reasons[2])

    def test_influencer_scoring(self):
        """
        Test rule-based scoring for influencer roles.
        Manager with exact ICP match and complete profile should score 40 points.
        """
        lead = {
            'role': 'Manager',
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
        self.assertEqual(score, 40)  # 10 (role) + 20 (industry) + 10 (completeness)

    def test_incomplete_data_scoring(self):
        """
        Test rule-based scoring with incomplete lead data.
        Missing required fields should not award completeness points.
        """
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

    def test_no_match_scoring(self):
        """
        Test rule-based scoring when lead doesn't match ICP.
        Non-decision maker in non-target industry should score low.
        """
        lead = {
            'role': 'Analyst',
            'industry': 'Healthcare',
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
        self.assertEqual(score, 10)  # 0 (role) + 0 (industry) + 10 (completeness)

    def test_adjacent_industry_scoring(self):
        """
        Test rule-based scoring for adjacent/related industries.
        Should receive partial industry match points.
        """
        lead = {
            'role': 'VP',
            'industry': 'B2B SaaS startup',
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
        self.assertGreaterEqual(score, 30)  # At least 20 (role) + 10 (adjacent)

    def test_multiple_decision_maker_titles(self):
        """
        Test that various decision maker titles are recognized.
        """
        decision_maker_roles = ['CEO', 'CTO', 'VP of Sales', 'Director', 'Founder', 'Head of Marketing']
        
        for role in decision_maker_roles:
            lead = {
                'role': role,
                'industry': 'Tech',
                'name': 'Test',
                'company': 'Test Co',
                'location': 'NY',
                'linkedin_bio': 'Bio'
            }
            offer = {
                'ideal_use_cases': ['Tech'],
                'value_props': ['Test']
            }
            
            score, reasons = calculate_rule_score(lead, offer)
            self.assertGreaterEqual(score, 20, f"Role '{role}' should get decision maker points")

    def test_csv_upload_endpoint(self):
        """
        Test CSV upload functionality.
        Note: This test requires a mock file upload.
        """
        # This would need a proper CSV file mock for complete testing
        # Just testing endpoint accessibility here
        response = self.client.post('/api/leads/upload/')
        # Should return 400 because no file provided
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_csv_endpoint(self):
        """
        Test CSV export endpoint returns proper response.
        """
        response = self.client.get('/api/leads/export_csv/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_lead_model_fields(self):
        """
        Test that Lead model has all required fields.
        """
        self.assertTrue(hasattr(self.lead, 'name'))
        self.assertTrue(hasattr(self.lead, 'role'))
        self.assertTrue(hasattr(self.lead, 'company'))
        self.assertTrue(hasattr(self.lead, 'industry'))
        self.assertTrue(hasattr(self.lead, 'location'))
        self.assertTrue(hasattr(self.lead, 'linkedin_bio'))
        self.assertTrue(hasattr(self.lead, 'intent'))
        self.assertTrue(hasattr(self.lead, 'score'))
        self.assertTrue(hasattr(self.lead, 'reasoning'))

    def test_offer_model_fields(self):
        """
        Test that Offer model has all required fields.
        """
        self.assertTrue(hasattr(self.offer, 'name'))
        self.assertTrue(hasattr(self.offer, 'value_props'))
        self.assertTrue(hasattr(self.offer, 'ideal_use_cases'))
        self.assertIsInstance(self.offer.value_props, list)
        self.assertIsInstance(self.offer.ideal_use_cases, list)