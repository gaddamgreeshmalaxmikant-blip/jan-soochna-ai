from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models.scheme import UserProfile
from .services.rule_engine import RuleEngine

app = FastAPI(
    title="JanSoochna AI",
    description="Voice-First Eligibility Engine",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RULES_FILE = "data/rules/sample_schemes.json"
rule_engine = RuleEngine(RULES_FILE)

@app.get("/")
async def root():
    return {"message": "JanSoochna AI is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/check-eligibility")
async def check_eligibility(user: UserProfile):
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