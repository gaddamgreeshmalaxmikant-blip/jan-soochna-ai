from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .models.scheme import UserProfile
from .services.rule_engine import RuleEngine
from .services.nlp_parser import NLPParser
from .services.embeddings import EmbeddingsService

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

# ============================================================
# INITIALIZE SERVICES
# ============================================================

RULES_FILE = "data/rules/sample_schemes.json"
rule_engine = RuleEngine(RULES_FILE)
nlp_parser = NLPParser()
embeddings_service = EmbeddingsService(RULES_FILE)


# ============================================================
# REQUEST MODELS
# ============================================================

class NaturalLanguageQuery(BaseModel):
    query: str


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


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
    return {
        "total_schemes": len(rule_engine.schemes_data),
        "status": "success"
    }


@app.get("/api/schemes/list")
async def list_schemes():
    schemes = []
    for scheme in rule_engine.schemes_data:
        schemes.append({
            "scheme_id": scheme.get("scheme_id"),
            "name": scheme.get("name"),
            "department": scheme.get("department")
        })
    return {"total": len(schemes), "schemes": schemes}


# ============================================================
# ELIGIBILITY ENDPOINTS
# ============================================================

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


# ============================================================
# NATURAL LANGUAGE ENDPOINTS
# ============================================================

@app.post("/api/parse-query")
async def parse_natural_language(request: NaturalLanguageQuery):
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
    try:
        profile_dict = nlp_parser.parse(request.query)
        
        if not profile_dict.get("age") or not profile_dict.get("annual_income"):
            return {
                "status": "incomplete",
                "message": "Could not extract age or income.",
                "extracted_profile": profile_dict
            }
        
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


# ============================================================
# RAG / SEMANTIC SEARCH ENDPOINTS
# ============================================================

@app.post("/api/semantic-search")
async def semantic_search(request: SearchQuery):
    try:
        results = embeddings_service.search(request.query, request.top_k)
        return {
            "status": "success",
            "query": request.query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/smart-search")
async def smart_search(request: SearchQuery):
    try:
        # Step 1: Parse natural language
        profile_dict = nlp_parser.parse(request.query)
        
        # Step 2: Semantic search
        search_results = embeddings_service.search(request.query, request.top_k)
        
        # Step 3: Check eligibility
        eligibility_results = []
        if profile_dict.get("age") and profile_dict.get("annual_income"):
            profile_dict.setdefault("state", "Maharashtra")
            user = UserProfile(**profile_dict)
            
            for scheme_data in search_results:
                from .models.scheme import Scheme
                scheme_clean = {
                    k: v for k, v in scheme_data.items() 
                    if k not in ['similarity_score', 'categories', 'matched_categories']
                }
                scheme = Scheme(**scheme_clean)
                result = rule_engine.check_eligibility(scheme, user)
                result['similarity_score'] = scheme_data.get('similarity_score', 0)
                eligibility_results.append(result)
            
            # NEW: Sort eligible first, then by similarity
            eligibility_results.sort(
                key=lambda x: (x.get('eligible', False), x.get('similarity_score', 0)),
                reverse=True
            )
        
        return {
            "status": "success",
            "query": request.query,
            "extracted_profile": profile_dict,
            "relevant_schemes": [
                {
                    "scheme_id": s.get("scheme_id"),
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "similarity_score": s.get("similarity_score"),
                    "matched_categories": s.get("matched_categories", [])
                }
                for s in search_results
            ],
            "eligibility_results": eligibility_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rebuild-index")
async def rebuild_index():
    try:
        embeddings_service.rebuild_index()
        return {
            "status": "success",
            "message": "Index rebuilt successfully",
            "total_schemes": len(embeddings_service.schemes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))