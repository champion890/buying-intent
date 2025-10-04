from typing import Dict, List

def calculate_rule_score(lead: Dict, offer: Dict) -> tuple:
    """
    Calculate rule-based score for a lead based on role, industry, and data completeness.
    
    This function implements the rule layer of the hybrid scoring system, providing
    up to 50 points based on objective criteria that can be evaluated without AI.
    
    Args:
        lead (Dict): Lead information containing:
            - role: Job title/position
            - industry: Company industry
            - name, company, location, linkedin_bio: Profile fields
        offer (Dict): Offer information containing:
            - ideal_use_cases: List of target industries/segments
            - value_props: Product value propositions
    
    Returns:
        tuple: (score: int, reasons: list[str]) where:
            - score: Integer from 0-50 representing rule-based fit
            - reasons: List of strings explaining each scoring decision
    
    Scoring Breakdown:
        - Role Relevance (0-20 points):
            * Decision makers (C-level, VP, Director, Founder): +20
            * Influencers (Manager, Lead, Architect, Senior): +10
            * Others: 0
        - Industry Match (0-20 points):
            * Exact ICP match: +20
            * Adjacent/related industry: +10
            * No match: 0
        - Data Completeness (0-10 points):
            * All required fields present: +10
            * Missing fields: 0
    
    Example:
        >>> lead = {'role': 'CEO', 'industry': 'B2B SaaS', 'name': 'John', ...}
        >>> offer = {'ideal_use_cases': ['B2B SaaS'], ...}
        >>> score, reasons = calculate_rule_score(lead, offer)
        >>> print(score)  # 50 (20 + 20 + 10)
    """
    score = 0
    reasons = []

    # Role relevance scoring (max 20 points)
    # Decision makers have budget authority and can make purchase decisions
    decision_makers = ['ceo', 'cto', 'vp', 'head', 'director', 'founder']
    # Influencers can advocate for the product but need approval from decision makers
    influencers = ['manager', 'lead', 'architect', 'senior']
    role = lead.get('role', '').lower()
    
    if any(role.find(dm) != -1 for dm in decision_makers):
        score += 20
        reasons.append("Decision maker role (+20)")
    elif any(role.find(inf) != -1 for inf in influencers):
        score += 10
        reasons.append("Influencer role (+10)")

    # Industry match scoring (max 20 points)
    # Prioritize leads from industries that match the offer's ideal customer profile (ICP)
    industry = lead.get('industry', '').lower()
    if industry in [use_case.lower() for use_case in offer.get('ideal_use_cases', [])]:
        score += 20
        reasons.append("Exact ICP match (+20)")
    elif any(icp.lower() in industry for icp in offer.get('ideal_use_cases', [])):
        score += 10
        reasons.append("Adjacent industry (+10)")

    # Data completeness scoring (max 10 points)
    # Complete profiles indicate higher quality leads and enable better AI analysis
    required_fields = ['name', 'role', 'company', 'industry', 'location', 'linkedin_bio']
    if all(lead.get(field) for field in required_fields):
        score += 10
        reasons.append("Complete profile (+10)")

    return score, reasons