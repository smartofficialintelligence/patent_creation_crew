from typing import Dict, Any, List

class PatentValidationError(Exception):
    """Custom exception for patent validation errors"""
    pass

def validate_patent_dict(patent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and ensure patent data has all required fields"""
    required_fields = ['id', 'title', 'description', 'key_claims']
    missing_fields = [field for field in required_fields if field not in patent_data or patent_data[field] is None]
    
    if missing_fields:
        raise PatentValidationError(f"Missing required fields: {missing_fields}")
    
    # Ensure optional fields have defaults
    patent_data.setdefault('technical_features', [])
    patent_data.setdefault('value_estimate', '$1-5M')
    patent_data.setdefault('market_applications', [])
    patent_data.setdefault('differentiation', '')
    patent_data.setdefault('implementation_complexity', 'Medium')
    patent_data.setdefault('prior_art_risk', 'Medium')
    
    return patent_data

def validate_patent_data(patent_ideas: Dict[str, List[Dict]]) -> bool:
    """Validate the entire patent ideas database structure"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not isinstance(patent_ideas, dict):
        logger.error("Patent ideas must be a dictionary")
        return False
    
    required_tiers = ['tier_1', 'tier_2', 'tier_3']
    
    for tier in required_tiers:
        if tier not in patent_ideas:
            logger.error(f"Missing required tier: {tier}")
            return False
        
        if not isinstance(patent_ideas[tier], list):
            logger.error(f"Tier {tier} must be a list of patent dictionaries")
            return False
        
        if not patent_ideas[tier]:
            logger.warning(f"Tier {tier} is empty")
            continue
        
        # Validate each patent in the tier
        for i, patent in enumerate(patent_ideas[tier]):
            try:
                validate_patent_dict(patent)
            except PatentValidationError as e:
                logger.error(f"Patent {i+1} in {tier} validation failed: {e}")
                return False
    
    logger.info("Patent data validation passed")
    return True 