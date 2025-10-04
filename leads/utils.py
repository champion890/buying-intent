from typing import Dict, List

def calculate_rule_score(lead: Dict, offer: Dict) -> tuple:
    """Calculate rule-based score for a lead."""
    score = 0
    reasons = []

    # Role relevance (max 20)
    decision_makers = ['ceo', 'cto', 'vp', 'head', 'director', 'founder']
    influencers = ['manager', 'lead', 'architect', 'senior']
    role = lead.get('role', '').lower()
    
    if any(role.find(dm) != -1 for dm in decision_makers):
        score += 20
        reasons.append("Decision maker role (+20)")
    elif any(role.find(inf) != -1 for inf in influencers):
        score += 10
        reasons.append("Influencer role (+10)")

    # Industry match (max 20)
    industry = lead.get('industry', '').lower()
    if industry in [use_case.lower() for use_case in offer.get('ideal_use_cases', [])]:
        score += 20
        reasons.append("Exact ICP match (+20)")
    elif any(icp.lower() in industry for icp in offer.get('ideal_use_cases', [])):
        score += 10
        reasons.append("Adjacent industry (+10)")

    # Data completeness (max 10)
    required_fields = ['name', 'role', 'company', 'industry', 'location', 'linkedin_bio']
    if all(lead.get(field) for field in required_fields):
        score += 10
        reasons.append("Complete profile (+10)")

    return score, reasons
