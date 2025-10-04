from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Offer, Lead
from .serializers import OfferSerializer, LeadSerializer
import csv
import io
from django.conf import settings
from openai import OpenAI, RateLimitError
from django.db.models import Max, Q

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def _get_unique_leads(self, scored_only=False):
        """Helper to get unique leads by company and name"""
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
        """Get scored leads with pagination"""
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
        """Upload leads from CSV file"""
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

    def _score_lead_with_rules(self, lead):
        """Fallback rule-based scoring"""
        score = 0
        reasoning = []
        
        # Role scoring
        role_lower = lead.role.lower()
        if any(title in role_lower for title in ['ceo', 'founder', 'owner']):
            score += 35
            reasoning.append("Senior decision maker")
        elif any(title in role_lower for title in ['head', 'director', 'vp']):
            score += 25
            reasoning.append("Mid-level decision maker")
        elif any(title in role_lower for title in ['manager']):
            score += 15
            reasoning.append("Team manager")
            
        # Industry scoring
        industry_lower = lead.industry.lower()
        if 'saas' in industry_lower or 'software' in industry_lower:
            score += 35
            reasoning.append("Direct industry match")
        elif any(ind in industry_lower for ind in ['tech', 'it', 'digital']):
            score += 25
            reasoning.append("Related industry")
            
        # Bio scoring
        if lead.linkedin_bio:
            bio_lower = lead.linkedin_bio.lower()
            if any(term in bio_lower for term in ['saas', 'software', 'technology']):
                score += 30
                reasoning.append("Relevant experience")
            if any(term in bio_lower for term in ['buying', 'purchasing', 'implementing']):
                score += 20
                reasoning.append("Shows buying behavior")
        
        return min(score, 100), " | ".join(reasoning)

    @action(detail=False, methods=['post'])
    def score(self, request):
        try:
            # Get only unscored unique leads
            leads = self._get_unique_leads().filter(score__isnull=True)
            results = []
            
            for lead in leads:
                try:
                    if settings.OPENAI_API_KEY:
                        # Try AI scoring first
                        messages = [{
                            "role": "system",
                            "content": "You are an AI trained to analyze B2B leads and provide a buying intent score and reasoning."
                        }, {
                            "role": "user",
                            "content": f"""
                            Analyze this B2B lead's buying intent based on their profile:
                            Role: {lead.role}
                            Company: {lead.company}
                            Industry: {lead.industry}
                            LinkedIn Bio: {lead.linkedin_bio}
                            
                            Consider:
                            1. Decision making authority (role seniority)
                            2. Industry fit (B2B SaaS focus)
                            3. Company profile
                            
                            Provide a score (0-100) and reasoning.
                            Format: score|reasoning
                            """
                        }]
                        
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            temperature=0.3,
                            max_tokens=150
                        )
                        
                        result = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
                        score_str, reasoning = result.split('|')
                        score = int(float(score_str))
                        
                    else:
                        # Fallback to rule-based scoring
                        score, reasoning = self._score_lead_with_rules(lead)
                    
                    # Set intent based on score
                    if score >= 70:
                        intent = "High"
                    elif score >= 40:
                        intent = "Medium"
                    else:
                        intent = "Low"
                    
                    lead.score = score
                    lead.intent = intent
                    lead.reasoning = reasoning.strip()
                    lead.save()
                    
                    results.append({
                        'name': lead.name,
                        'role': lead.role,
                        'company': lead.company,
                        'intent': intent,
                        'score': score,
                        'reasoning': reasoning.strip()
                    })
                    
                except RateLimitError:
                    # Fallback to rule-based scoring on API quota error
                    score, reasoning = self._score_lead_with_rules(lead)
                    lead.score = score
                    lead.intent = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
                    lead.reasoning = f"(Rule-based scoring) {reasoning}"
                    lead.save()
                    
                    results.append({
                        'name': lead.name,
                        'role': lead.role,
                        'company': lead.company,
                        'intent': lead.intent,
                        'score': score,
                        'reasoning': lead.reasoning
                    })
            
            return Response({'results': results})
            
        except Exception as e:
            return Response(
                {"error": f"Scoring failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export all leads to CSV file"""
        leads = Lead.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Role', 'Company', 'Industry', 'Intent', 'Score', 'Reasoning'])
        
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.role, 
                lead.company,
                lead.industry,
                lead.intent,
                lead.score,
                lead.reasoning
            ])
        return response
