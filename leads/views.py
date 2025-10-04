from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Offer, Lead
from .serializers import OfferSerializer, LeadSerializer
from .utils import calculate_rule_score
import csv
import io
from django.conf import settings
from openai import OpenAI, RateLimitError
from django.db.models import Max, Q

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product/offer information.
    Provides CRUD operations for offers with value propositions and ideal use cases.
    """
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer

class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads and scoring operations.
    Handles lead upload, scoring (rule-based + AI), and results retrieval.
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def _get_unique_leads(self, scored_only=False):
        """
        Helper to get unique leads by company and name.
        Prevents duplicate scoring of the same lead.
        """
        base_query = Lead.objects.all()
        if scored_only:
            base_query = base_query.filter(score__isnull=False)
        
        # Get the latest record for each company/name combination
        latest_leads = base_query.values('company', 'name').annotate(
            latest_id=Max('id')
        ).values('latest_id')
        
        return base_query.filter(id__in=latest_leads)

    @action(detail=False, methods=['get'])
    def results(self, request):
        """
        Get scored leads with pagination.
        Returns only leads that have been scored, ordered by score (highest first).
        """
        try:
            leads = self._get_unique_leads(scored_only=True).order_by('-score', 'company', 'name')
            page = self.paginate_queryset(leads)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload leads from CSV file.
        Expected columns: name, role, company, industry, location, linkedin_bio
        """
        try:
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided'}, status=400)
            
            csv_file = request.FILES['file']
            if not csv_file.name.endswith('.csv'):
                return Response({'error': 'File must be CSV format'}, status=400)

            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            leads = []
            for row in csv_data:
                lead = Lead.objects.create(**row)
                leads.append(lead)
            
            serializer = LeadSerializer(leads, many=True)
            return Response(serializer.data, status=201)

        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_ai_intent_score(self, lead, offer):
        """
        Get AI-based intent classification and score (0-50 points).
        
        Uses OpenAI GPT-3.5-Turbo to analyze lead profile against offer context.
        Maps intent classification to points: High=50, Medium=30, Low=10
        
        Args:
            lead: Lead model instance
            offer: Offer model instance
            
        Returns:
            tuple: (ai_score: int, intent: str, reasoning: str)
                - ai_score: 0-50 points based on intent classification
                - intent: "High", "Medium", or "Low"
                - reasoning: AI's explanation for the classification
        """
        try:
            # Construct prompt with both lead profile AND offer context
            # This allows AI to evaluate fit between prospect and product
            messages = [{
                "role": "system",
                "content": "You are an AI trained to analyze B2B lead buying intent by matching prospect profiles against product offerings."
            }, {
                "role": "user",
                "content": f"""
                Analyze this lead's buying intent for our product:
                
                LEAD PROFILE:
                - Name: {lead.name}
                - Role: {lead.role}
                - Company: {lead.company}
                - Industry: {lead.industry}
                - Location: {lead.location}
                - LinkedIn Bio: {lead.linkedin_bio}
                
                OUR PRODUCT/OFFER:
                - Product: {offer.name}
                - Value Propositions: {', '.join(offer.value_props)}
                - Ideal Customer Profile: {', '.join(offer.ideal_use_cases)}
                
                Evaluate:
                1. Does their role indicate decision-making authority?
                2. Does their industry/company match our ICP?
                3. Does their bio show relevant experience or pain points our product solves?
                4. Overall likelihood they would be interested in our offer
                
                Classify their buying intent as High, Medium, or Low.
                Provide 1-2 sentences explaining your classification.
                
                Format: Intent|Reasoning
                Example: High|VP of Sales in B2B SaaS matches ICP perfectly. Bio mentions scaling outreach challenges.
                """
            }]
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,  # Low temperature for consistent classifications
                max_tokens=150
            )
            
            # Parse response (format: "Intent|Reasoning")
            result = response.choices[0].message.content.strip()
            if '|' not in result:
                # Fallback if format is incorrect
                return 10, "Low", "AI response format error"
                
            intent, reasoning = result.split('|', 1)
            intent = intent.strip()
            
            # Map intent classification to points (as per assignment requirements)
            intent_map = {
                'High': 50,
                'Medium': 30,
                'Low': 10
            }
            
            ai_score = intent_map.get(intent, 10)
            
            return ai_score, intent, reasoning.strip()
            
        except Exception as e:
            # Return default low score on any error
            return 10, "Low", f"AI scoring error: {str(e)}"

    @action(detail=False, methods=['post'])
    def score(self, request):
        """
        Score all unscored leads using HYBRID approach (Rule-based + AI):
        
        SCORING PIPELINE (as per assignment):
        1. Rule Layer (0-50 points): Objective scoring based on role, industry, data completeness
        2. AI Layer (0-50 points): Contextual analysis using OpenAI to classify intent
        3. Final Score = rule_score + ai_score (max 100)
        
        Intent Classification:
        - High: Final score >= 70
        - Medium: Final score >= 40
        - Low: Final score < 40
        
        Returns:
            JSON with array of scored leads containing:
            - name, role, company, intent, score, reasoning
        """
        try:
            # Validate that an offer exists before scoring
            offer = Offer.objects.first()
            if not offer:
                return Response(
                    {'error': 'Please create an offer first using POST /api/offer/'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get only unscored unique leads to avoid re-scoring
            leads = self._get_unique_leads().filter(score__isnull=True)
            
            if not leads.exists():
                return Response(
                    {'message': 'No unscored leads found. Upload leads using POST /api/leads/upload/'}, 
                    status=status.HTTP_200_OK
                )
            
            results = []
            
            for lead in leads:
                try:
                    # STEP 1: Calculate Rule-Based Score (0-50 points)
                    # This uses objective criteria: role seniority, industry match, data completeness
                    lead_dict = {
                        'role': lead.role,
                        'industry': lead.industry,
                        'name': lead.name,
                        'company': lead.company,
                        'location': lead.location,
                        'linkedin_bio': lead.linkedin_bio
                    }
                    offer_dict = {
                        'ideal_use_cases': offer.ideal_use_cases,
                        'value_props': offer.value_props
                    }
                    
                    rule_score, rule_reasons = calculate_rule_score(lead_dict, offer_dict)
                    
                    # STEP 2: Calculate AI Score (0-50 points)
                    # This uses OpenAI to classify intent: High=50, Medium=30, Low=10
                    if settings.OPENAI_API_KEY:
                        ai_score, ai_intent, ai_reasoning = self._get_ai_intent_score(lead, offer)
                    else:
                        # If no API key, default to low AI score
                        ai_score, ai_intent, ai_reasoning = 10, "Low", "No AI API key configured"
                    
                    # STEP 3: Combine scores (HYBRID APPROACH)
                    # Final Score = Rule Score + AI Score (max 100)
                    final_score = min(rule_score + ai_score, 100)
                    
                    # Classify final intent based on combined score
                    if final_score >= 70:
                        final_intent = "High"
                    elif final_score >= 40:
                        final_intent = "Medium"
                    else:
                        final_intent = "Low"
                    
                    # Combine reasoning from both layers
                    combined_reasoning = f"[Rule: {', '.join(rule_reasons)}] [AI: {ai_reasoning}]"
                    
                    # Save results to database
                    lead.score = final_score
                    lead.intent = final_intent
                    lead.reasoning = combined_reasoning
                    lead.save()
                    
                    results.append({
                        'name': lead.name,
                        'role': lead.role,
                        'company': lead.company,
                        'intent': final_intent,
                        'score': final_score,
                        'reasoning': combined_reasoning,
                        'score_breakdown': {
                            'rule_score': rule_score,
                            'ai_score': ai_score
                        }
                    })
                    
                except RateLimitError:
                    # Fallback: Use only rule-based score if AI rate limited
                    final_score = min(rule_score * 2, 100)  # Scale up rule score to 0-100 range
                    final_intent = "High" if final_score >= 70 else "Medium" if final_score >= 40 else "Low"
                    fallback_reasoning = f"[Rule-based only - AI rate limited] {', '.join(rule_reasons)}"
                    
                    lead.score = final_score
                    lead.intent = final_intent
                    lead.reasoning = fallback_reasoning
                    lead.save()
                    
                    results.append({
                        'name': lead.name,
                        'role': lead.role,
                        'company': lead.company,
                        'intent': final_intent,
                        'score': final_score,
                        'reasoning': fallback_reasoning
                    })
                
                except Exception as lead_error:
                    # Log individual lead errors but continue processing others
                    print(f"Error scoring lead {lead.name}: {str(lead_error)}")
                    continue
            
            return Response({
                'results': results,
                'total_scored': len(results),
                'scoring_method': 'hybrid (rule + AI)' if settings.OPENAI_API_KEY else 'rule-based only'
            })
            
        except Exception as e:
            return Response(
                {"error": f"Scoring failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Export all scored leads to CSV file.
        Bonus feature: Allows downloading scored results for external analysis.
        """
        leads = Lead.objects.filter(score__isnull=False).order_by('-score')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Role', 'Company', 'Industry', 'Location', 'Intent', 'Score', 'Reasoning'])
        
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.role, 
                lead.company,
                lead.industry,
                lead.location,
                lead.intent,
                lead.score,
                lead.reasoning
            ])
        return response