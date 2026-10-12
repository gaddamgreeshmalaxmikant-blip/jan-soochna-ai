import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingsService:
    """
    Smart RAG service with:
    - Category-based intent classification
    - Synonym expansion
    - Hybrid scoring (keyword + category)
    """
    
    CATEGORY_KEYWORDS = {
        "agriculture": [
            "farmer", "crop", "crops", "farming", "farm", "agriculture",
            "kisan", "fasal", "harvest", "land", "soil", "irrigation",
            "seeds", "fertilizer", "pesticide", "cattle", "dairy"
        ],
        "education": [
            "student", "school", "college", "study", "education",
            "scholarship", "daughter", "son", "girl", "boy", "child",
            "academic", "university", "degree", "tuition", "exam"
        ],
        "health": [
            "health", "medical", "hospital", "insurance", "sick",
            "illness", "medicine", "treatment", "surgery", "doctor"
        ],
        "housing": [
            "house", "home", "housing", "awas", "rent",
            "shelter", "construction", "building", "roof"
        ],
        "finance": [
            "money", "loan", "credit", "business", "income", "financial",
            "bank", "cash", "fund", "capital", "investment", "mudra",
            "vendor", "shop", "small business", "entrepreneur"
        ],
        "pension": [
            "pension", "retirement", "old age", "elderly", "senior",
            "senior citizen", "monthly pension"
        ],
        "women": [
            "women", "woman", "female", "wife", "mother", "widow",
            "girl child", "beti", "maternity", "pregnancy"
        ],
        "insurance": [
            "insurance", "life insurance", "accident", "death",
            "disability", "coverage", "bima"
        ],
        "skill": [
            "skill", "training", "employment", "job", "unemployed",
            "worker", "vocational", "kaushal"
        ]
    }
    
    SYNONYMS = {
        "crop": "farmer agriculture kisan fasal",
        "crops": "farmer agriculture kisan fasal",
        "farming": "farmer agriculture kisan",
        "farm": "farmer agriculture kisan",
        "daughter": "girl female child beti student",
        "son": "boy male child student",
        "girl": "female daughter beti",
        "boy": "male son",
        "school": "student education scholarship",
        "college": "student education scholarship",
        "study": "student education scholarship",
        "money": "income financial loan business",
        "poor": "income below poverty",
        "loan": "loan mudra business credit",
        "business": "loan mudra vendor",
        "shop": "vendor business loan",
        "house": "housing awas",
        "home": "housing awas",
        "old": "pension senior citizen",
        "sick": "health insurance",
        "medicine": "health medical",
        "hospital": "health insurance",
        "work": "employment worker",
        "job": "employment worker",
        "widow": "female woman women",
        "wife": "female woman",
        "mother": "female woman maternity",
    }
    
    def __init__(self, schemes_file: str, index_path: str = "data/processed/smart_index"):
        self.schemes_file = schemes_file
        self.index_path = index_path
        self.schemes = []
        self.vectorizer = None
        self.tfidf_matrix = None
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.load_schemes()
        self.build_or_load_index()
    
    def load_schemes(self):
        with open(self.schemes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.schemes = data.get('schemes', [])
        
        for scheme in self.schemes:
            scheme['categories'] = self.detect_scheme_categories(scheme)
        
        print(f"✅ Loaded {len(self.schemes)} schemes")
    
    def detect_scheme_categories(self, scheme: dict) -> list:
        text = (
            f"{scheme.get('name', '')} "
            f"{scheme.get('description', '')} "
            f"{scheme.get('department', '')} "
            f"{scheme.get('benefits', '')}"
        ).lower()
        
        matched = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    matched.append(category)
                    break
        return matched
    
    def detect_query_categories(self, query: str) -> list:
        query_lower = query.lower()
        matched = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    matched.append(category)
                    break
        return matched
    
    def create_scheme_text(self, scheme: dict) -> str:
        parts = [
            scheme.get('name', ''),
            scheme.get('description', ''),
            scheme.get('department', ''),
            scheme.get('benefits', ''),
            ' '.join(scheme.get('documents_required', [])),
            ' '.join(scheme.get('categories', [])),
        ]
        return ' '.join(parts).strip()
    
    def expand_query(self, query: str) -> str:
        query_lower = query.lower()
        expanded_terms = [query_lower]
        for keyword, synonyms in self.SYNONYMS.items():
            if keyword in query_lower:
                expanded_terms.append(synonyms)
        return ' '.join(expanded_terms)
    
    def build_or_load_index(self):
        matrix_file = f"{self.index_path}_matrix.pkl"
        vectorizer_file = f"{self.index_path}_vectorizer.pkl"
        
        if os.path.exists(matrix_file) and os.path.exists(vectorizer_file):
            print("📂 Loading smart index...")
            with open(matrix_file, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
            with open(vectorizer_file, 'rb') as f:
                self.vectorizer = pickle.load(f)
            print(f"✅ Loaded index with {len(self.schemes)} schemes")
        else:
            print("🔨 Building smart index...")
            self.build_index()
    
    def build_index(self):
        texts = [self.create_scheme_text(s) for s in self.schemes]
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000,
            min_df=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        with open(f"{self.index_path}_matrix.pkl", 'wb') as f:
            pickle.dump(self.tfidf_matrix, f)
        with open(f"{self.index_path}_vectorizer.pkl", 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        print(f"✅ Built smart index with {len(self.schemes)} schemes")
    
    def hybrid_search(self, query: str, top_k: int = 5) -> list:
        expanded_query = self.expand_query(query)
        query_vec = self.vectorizer.transform([expanded_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        query_categories = self.detect_query_categories(query)
        
        scored_results = []
        for idx, scheme in enumerate(self.schemes):
            base_score = float(similarities[idx])
            
            category_boost = 0.0
            if query_categories:
                matched_cats = set(query_categories) & set(scheme.get('categories', []))
                if matched_cats:
                    category_boost = 0.5 * len(matched_cats) / len(query_categories)
            
            final_score = base_score + category_boost
            
            scored_results.append({
                'idx': idx,
                'scheme': scheme,
                'base_score': base_score,
                'category_boost': category_boost,
                'final_score': final_score
            })
        
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        results = []
        for r in scored_results[:top_k]:
            scheme = r['scheme'].copy()
            scheme['similarity_score'] = r['final_score']
            scheme['matched_categories'] = list(
                set(query_categories) & set(scheme.get('categories', []))
            )
            results.append(scheme)
        
        return results
    
    def search(self, query: str, top_k: int = 5) -> list:
        return self.hybrid_search(query, top_k)
    
    def rebuild_index(self):
        self.load_schemes()
        self.build_index()