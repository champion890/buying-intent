from typing import Dict, List, Tuple

def calculate_rule_score(lead: Dict, offer: Dict) -> Tuple[int, List[str]]:
    """
    Calculate rule-based score for a lead based on role, industry, and data completeness.
    
    This function implements the RULE LAYER of the hybrid scoring system as per assignment:
    - Maximum 50 points from objective, rule-based criteria
    - Combined with AI layer (also max 50 points) for final score (max 100)
    
    Assignment Scoring Breakdown:
    ================================
    Rule Layer (max 50 points):
    1. Role relevance: decision maker (+20), influencer (+10), else 0
    2. Industry match: exact ICP (+20), adjacent (+10), else 0
    3. Data completeness: all fields present (+10)
    
    Args:
        lead (Dict): Lead information containing:
            - role: Job title/position (e.g., "CEO", "Head of Sales")
            - industry: Company industry (e.g., "B2B SaaS")
            - name: Lead's full name
            - company: Company name
            - location: Geographic location
            - linkedin_bio: Professional bio/summary
            
        offer (Dict): Offer information containing:
            - ideal_use_cases: List of target industries/segments (ICP)
            - value_props: Product value propositions
    
    Returns:
        Tuple[int, List[str]]: 
            - score (int): Integer from 0-50 representing rule-based fit
            - reasons (List[str]): List of strings explaining each scoring decision
    
    Example:
        >>> lead = {
        ...     'role': 'CEO', 
        ...     'industry': 'B2B SaaS', 
        ...     'name': 'John Doe',
        ...     'company': 'TechCorp',
        ...     'location': 'San Francisco',
        ...     'linkedin_bio': '15 years in SaaS'
        ... }
        >>> offer = {
        ...     'ideal_use_cases': ['B2B SaaS'], 
        ...     'value_props': ['AI automation']
        ... }
        >>> score, reasons = calculate_rule_score(lead, offer)
        >>> print(score)  # 50 (20 + 20 + 10)
        >>> print(reasons)
        ['Decision maker role (+20)', 'Exact ICP match (+20)', 'Complete profile (+10)']
    """
    score = 0
    reasons = []

    # ============================================================================
    # CRITERION 1: Role Relevance (0-20 points)
    # ============================================================================
    # Decision makers have budget authority and can make final purchase decisions
    # These roles typically control B2B buying decisions
    decision_makers = ['ceo', 'cto', 'cfo', 'vp', 'head', 'director', 'founder', 'owner', 'president']
    
    # Influencers can advocate for the product but usually need approval
    # They're important in the buying process but not final decision makers
    influencers = ['manager', 'lead', 'architect', 'senior', 'principal']
    
    role = lead.get('role', '').lower()
    
    if any(dm in role for dm in decision_makers):
        score += 20
        reasons.append("Decision maker role (+20)")
    elif any(inf in role for inf in influencers):
        score += 10
        reasons.append("Influencer role (+10)")
    else:
        # No points for roles without clear buying authority
        pass

    # ============================================================================
    # CRITERION 2: Industry Match (0-20 points)
    # ============================================================================
    # Prioritize leads from industries matching the offer's ideal customer profile (ICP)
    # Exact matches indicate perfect product-market fit
    industry = lead.get('industry', '').lower()
    ideal_use_cases = offer.get('ideal_use_cases', [])
    
    # Check for exact match first (case-insensitive)
    if any(industry == use_case.lower() for use_case in ideal_use_cases):
        score += 20
        reasons.append("Exact ICP match (+20)")
    # Check for partial/adjacent match (industry contains ICP keyword)
    elif any(icp.lower() in industry or industry in icp.lower() for icp in ideal_use_cases):
        score += 10
        reasons.append("Adjacent industry (+10)")
    else:
        # No points for industries outside target ICP
        pass

    # ============================================================================
    # CRITERION 3: Data Completeness (0-10 points)
    # ============================================================================
    # Complete profiles indicate:
    # - Higher quality leads (more engaged prospects)
    # - Better data for AI analysis layer
    # - More reliable scoring outcomes
    required_fields = ['name', 'role', 'company', 'industry', 'location', 'linkedin_bio']
    
    if all(lead.get(field) and str(lead.get(field)).strip() for field in required_fields):
        score += 10
        reasons.append("Complete profile (+10)")
    else:
        # Missing fields reduce confidence in lead quality
        pass

    return score, reasons