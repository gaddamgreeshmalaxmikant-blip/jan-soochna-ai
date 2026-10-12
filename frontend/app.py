import streamlit as st
import requests
import json

# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="JanSoochna AI",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B35;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .scheme-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B35;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .eligible-badge {
        background-color: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .not-eligible-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .match-score {
        font-size: 1.5rem;
        font-weight: bold;
        color: #FF6B35;
    }
    .rule-trace {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.9rem;
        border-left: 4px solid #ffc107;
    }
    .stats-box {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown('<p class="main-header">🇮🇳 JanSoochna AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Voice-First Eligibility Engine for India\'s Welfare Schemes</p>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔍 How It Works")
st.sidebar.markdown("""
1. **Type your query** in natural language
2. **AI extracts your profile** (age, income, etc.)
3. **Smart RAG** finds relevant schemes
4. **Rule Engine** checks eligibility
5. **Get results** with full transparency
""")

st.sidebar.markdown("---")
st.sidebar.title("📊 System Stats")

try:
    stats_response = requests.get(f"{API_URL}/api/schemes/count", timeout=5)
    if stats_response.status_code == 200:
        stats = stats_response.json()
        st.sidebar.metric("Total Schemes", stats.get("total_schemes", 0))
except:
    st.sidebar.warning("⚠️ Backend not connected")

st.sidebar.markdown("---")
st.sidebar.markdown("**Built with:**")
st.sidebar.markdown("- 🧠 NLP + Intent Classification")
st.sidebar.markdown("- 🔍 Smart Hybrid RAG")
st.sidebar.markdown("- ⚙️ Rules-as-Code Engine")
st.sidebar.markdown("- 🌐 FastAPI + Streamlit")

# ============================================================
# MAIN APP - TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Smart Search",
    "📋 All Schemes",
    "🔎 Semantic Search",
    "ℹ️ About"
])

# ------------------------------------------------------------
# TAB 1: SMART SEARCH (Main Feature)
# ------------------------------------------------------------
with tab1:
    st.markdown("### 🎯 Tell us about yourself")
    st.markdown("*Example: I am a 45 year old farmer from Maharashtra earning 2.5 lakh*")
    
    query = st.text_input(
        "Your query (in natural language):",
        placeholder="e.g., I am a 45 year old farmer from Maharashtra earning 2.5 lakh",
        key="smart_query"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.number_input("Results", min_value=1, max_value=20, value=5)
    with col2:
        search_button = st.button("🔍 Find Schemes", type="primary", use_container_width=True)
    
    if search_button and query:
        with st.spinner("🧠 Processing your query..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/smart-search",
                    json={"query": query, "top_k": top_k},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Show extracted profile
                    st.markdown("---")
                    st.markdown("### 👤 Your Extracted Profile")
                    
                    profile = data.get("extracted_profile", {})
                    if profile:
                        profile_cols = st.columns(4)
                        if profile.get("age"):
                            profile_cols[0].metric("Age", profile["age"])
                        if profile.get("annual_income"):
                            profile_cols[1].metric("Income", f"₹{profile['annual_income']:,.0f}")
                        if profile.get("state"):
                            profile_cols[2].metric("State", profile["state"])
                        if profile.get("occupation"):
                            profile_cols[3].metric("Occupation", profile["occupation"])
                    
                    # Show eligibility results
                    st.markdown("---")
                    eligibility = data.get("eligibility_results", [])
                    relevant = data.get("relevant_schemes", [])
                    
                    if eligibility:
                        st.markdown(f"### ✅ Found {len(eligibility)} Relevant Schemes")
                        
                        for scheme in eligibility:
                            eligible = scheme.get("eligible", False)
                            match = scheme.get("match_percentage", 0)
                            
                            with st.expander(f"📌 {scheme.get('scheme_name', 'Unknown')} — Match: {match}%", expanded=True):
                                c1, c2 = st.columns([3, 1])
                                with c1:
                                    badge = "✅ ELIGIBLE" if eligible else "❌ NOT ELIGIBLE"
                                    badge_class = "eligible-badge" if eligible else "not-eligible-badge"
                                    st.markdown(f'<span class="{badge_class}">{badge}</span>', unsafe_allow_html=True)
                                    
                                    st.markdown(f"**Benefits:** {scheme.get('benefits', 'N/A')}")
                                    st.markdown(f"**Documents Required:** {', '.join(scheme.get('documents_required', []))}")
                                    st.markdown(f"**Official Source:** [{scheme.get('source', 'N/A')}]({scheme.get('source', '#')})")
                                
                                with c2:
                                    st.markdown(f'<p class="match-score">{match}%</p>', unsafe_allow_html=True)
                                
                                # Rule Trace
                                st.markdown("**🔍 Rule Trace (Why this decision):**")
                                checks = scheme.get("checks", [])
                                if checks:
                                    trace_html = ""
                                    for check in checks:
                                        symbol = "✅" if check.get("passed") else "❌"
                                        field = check.get("field", "")
                                        actual = check.get("actual", "N/A")
                                        condition = check.get("condition", "")
                                        trace_html += f"<p>{symbol} <b>{field}</b> = {actual} ({condition})</p>"
                                    st.markdown(f'<div class="rule-trace">{trace_html}</div>', unsafe_allow_html=True)
                    else:
                        st.info("No eligibility results. Try a different query.")
                    
                    # Show relevant schemes from RAG
                    if relevant and not eligibility:
                        st.markdown("### 📋 Relevant Schemes (from RAG)")
                        for scheme in relevant:
                            st.markdown(f"- **{scheme.get('name')}** — {scheme.get('description')}")
                
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.json(response.json())
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ------------------------------------------------------------
# TAB 2: ALL SCHEMES
# ------------------------------------------------------------
with tab2:
    st.markdown("### 📋 All Available Schemes")
    
    try:
        response = requests.get(f"{API_URL}/api/schemes/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            schemes = data.get("schemes", [])
            
            st.markdown(f"**Total: {len(schemes)} schemes**")
            
            # Filter by department
            departments = list(set([s.get("department", "Other") for s in schemes]))
            selected_dept = st.selectbox("Filter by Department:", ["All"] + departments)
            
            filtered = schemes if selected_dept == "All" else [
                s for s in schemes if s.get("department") == selected_dept
            ]
            
            for scheme in filtered:
                with st.expander(f"📌 {scheme.get('name')}"):
                    st.markdown(f"**ID:** `{scheme.get('scheme_id')}`")
                    st.markdown(f"**Department:** {scheme.get('department')}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ------------------------------------------------------------
# TAB 3: SEMANTIC SEARCH
# ------------------------------------------------------------
with tab3:
    st.markdown("### 🔎 Semantic Search (RAG)")
    st.markdown("*Search by meaning, not just keywords*")
    
    sem_query = st.text_input("Search query:", placeholder="e.g., help for my crops", key="sem_query")
    sem_top_k = st.slider("Number of results:", 1, 10, 3)
    
    if st.button("🔍 Semantic Search") and sem_query:
        with st.spinner("Searching..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/semantic-search",
                    json={"query": sem_query, "top_k": sem_top_k},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    st.markdown(f"**Found {len(results)} results**")
                    
                    for scheme in results:
                        score = scheme.get("similarity_score", 0)
                        st.markdown(f"""
                        <div class="scheme-card">
                            <h4>{scheme.get('name')}</h4>
                            <p><b>Score:</b> {score:.3f}</p>
                            <p><b>Description:</b> {scheme.get('description')}</p>
                            <p><b>Benefits:</b> {scheme.get('benefits')}</p>
                            <p><b>Categories:</b> {', '.join(scheme.get('matched_categories', ['none']))}</p>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ------------------------------------------------------------
# TAB 4: ABOUT
# ------------------------------------------------------------
with tab4:
    st.markdown("### ℹ️ About JanSoochna AI")
    
    st.markdown("""
    #### 🎯 Mission
    Help every Indian citizen discover government welfare schemes they qualify for — 
    in their own language, with auditable and verifiable results.
    
    #### 🧠 Technology Stack
    
    | Component | Technology |
    |-----------|------------|
    | **Backend** | FastAPI |
    | **Frontend** | Streamlit |
    | **NLP** | Custom parser + Synonym expansion |
    | **Search** | Smart Hybrid RAG (TF-IDF + Intent Classification) |
    | **Eligibility** | Rules-as-Code Engine |
    | **Data** | 20 Government Schemes |
    
    #### 🔑 Key Features
    
    - ✅ **Natural Language Input** — Type in plain English
    - ✅ **Intent Classification** — Understands what you need
    - ✅ **Synonym Expansion** — "crops" → farmer, agriculture, kisan
    - ✅ **Deterministic Eligibility** — Zero hallucination
    - ✅ **Rule Trace** — See exactly why you qualify
    - ✅ **20 Schemes** — Agriculture, Health, Education, Finance, Housing
    
    #### 📚 Research Foundation
    
    1. ACL 2025 — Voice-first > form-based for emergent users
    2. GAR 2026 — 94.8% factual precision
    3. POLRAG 2025 — Multi-channel RAG
    4. IJRCMS 2026 — India's DPI needs trustworthy AI
    5. Zenodo 2026 — BHASHINI for 22 language voice services
    
    #### 🏗️ Architecture
    """)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
"<p style='text-align: center; color: #888;'>Built with ❤️ for India's Next Billion Users</p>",
unsafe_allow_html=True
)