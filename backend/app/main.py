from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .models.scheme import UserProfile
from .services.rule_engine import RuleEngine
from .services.nlp_parser import NLPParser

app = FastAPI(
    title="JanSoochna AI",
    description="Voice-First Eligibility Engine for India's Welfare Schemes",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Rule Engine
RULES_FILE = "data/rules/sample_schemes.json"
rule_engine = RuleEngine(RULES_FILE)

# Initialize NLP Parser
nlp_parser = NLPParser()


# ============================================================
# REQUEST MODELS
# ============================================================

class NaturalLanguageQuery(BaseModel):
    query: str


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {"message": "JanSoochna AI is running!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/schemes/count")
async def scheme_count():
    """Get total number of schemes loaded"""
    return {
        "total_schemes": len(rule_engine.schemes_data),
        "status": "success"
    }


@app.get("/api/schemes/list")
async def list_schemes():
    """List all available schemes"""
    schemes = []
    for scheme in rule_engine.schemes_data:
        schemes.append({
            "scheme_id": scheme.get("scheme_id"),
            "name": scheme.get("name"),
            "department": scheme.get("department")
        })
    return {
        "total": len(schemes),
        "schemes": schemes
    }


# ============================================================
# ELIGIBILITY ENDPOINTS
# ============================================================

@app.post("/api/check-eligibility")
async def check_eligibility(user: UserProfile):
    """Check eligibility for ALL schemes (structured input)"""
    try:
        eligible = rule_engine.find_eligible_schemes(user)
        return {
            "status": "success",
            "user_profile": user.dict(),
            "eligible_schemes": eligible,
            "total_eligible": len(eligible)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check-scheme/{scheme_id}")
async def check_specific_scheme(scheme_id: str, user: UserProfile):
    """Check eligibility for a SPECIFIC scheme"""
    try:
        for scheme_data in rule_engine.schemes_data:
            if scheme_data.get('scheme_id') == scheme_id:
                from .models.scheme import Scheme
                scheme = Scheme(**scheme_data)
                result = rule_engine.check_eligibility(scheme, user)
                return {
                    "status": "success",
                    "user_profile": user.dict(),
                    "result": result
                }
        raise HTTPException(status_code=404, detail="Scheme not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# NATURAL LANGUAGE ENDPOINTS (NEW!)
# ============================================================

@app.post("/api/parse-query")
async def parse_natural_language(request: NaturalLanguageQuery):
    """
    Parse natural language query into structured profile.
    
    Example: "I am a 45 year old farmer from Maharashtra earning 2.5 lakh"
    Returns: {"age": 45, "annual_income": 250000, "state": "Maharashtra", "occupation": "Farmer"}
    """
    try:
        profile = nlp_parser.parse(request.query)
        return {
            "status": "success",
            "original_query": request.query,
            "extracted_profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/smart-check")
async def smart_check(request: NaturalLanguageQuery):
    """
    Parse natural language query AND check eligibility in one call.
    
    Example: "I am a 45 year old farmer from Maharashtra earning 2.5 lakh"
    Returns: Extracted profile + Eligible schemes
    """
    try:
        profile_dict = nlp_parser.parse(request.query)
        
        if not profile_dict.get("age") or not profile_dict.get("annual_income"):
            return {
                "status": "incomplete",
                "message": "Could not extract age or income. Please provide more details.",
                "extracted_profile": profile_dict
            }
        
        # Fill default state if missing
        profile_dict.setdefault("state", "Maharashtra")
        
        user = UserProfile(**profile_dict)
        eligible = rule_engine.find_eligible_schemes(user)
        
        return {
            "status": "success",
            "original_query": request.query,
            "extracted_profile": profile_dict,
            "eligible_schemes": eligible,
            "total_eligible": len(eligible)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))