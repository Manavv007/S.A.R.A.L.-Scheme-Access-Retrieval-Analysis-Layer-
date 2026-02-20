"""
Streamlit frontend for YojanaSetu (BharatScheme-AI) – Modern SaaS UI.
Design: GovTech / Engineering-First / Dark Mode.
URGENT FIX: Raw HTML Rendering & Layout Overhaul.
"""

import sys
import os

# 1. Dynamically add the project root to the Python path
# (This goes up one level from 'frontend' to project root)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 2. Set Cloud Environment Flag
os.environ["DEPLOYMENT_ENV"] = "CLOUD"

# FORCE INJECT SECRETS INTO OS ENVIRONMENT FOR LANGCHAIN
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "PINECONE_API_KEY" in st.secrets:
        os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]
    if "HF_TOKEN" in st.secrets:
        os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]
except Exception:
    pass  # Fails gracefully locally if st.secrets isn't set up

import streamlit as st
from src.utils.api_client import get_chat_response, get_recommendations

# ── Page Configuration ───────────────────────────────────
st.set_page_config(
    page_title="S.A.R.A.L. - Scheme Access Retrieval Analysis Layer",
    layout="wide",
    page_icon="🇮🇳",
    initial_sidebar_state="expanded",
)

# ── Global CSS Injection (User Provided) ─────────────────
st.markdown("""
<style>
/* Global Theme */
.stApp {
    background-color: #0f172a; /* Navy Blue */
    font-size: 16px; /* Reduced base font size */
}
/* Card Style */
.scheme-card {
    background-color: #1e293b; /* Slate */
    border: 1px solid #334155;
    border-radius: 10px; /* Slightly smaller radius */
    padding: 16px; /* Reduced padding */
    margin-bottom: 16px;
    box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* Ensure alignment */
    height: 100%;
    min-height: 200px; /* Minimum height for consistency */
}
.scheme-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

/* Typography */
h1 { font-size: 2.0rem !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
h2 { font-size: 1.75rem !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; font-weight: 600 !important; }
h3 { font-size: 1.5rem !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; font-weight: 600 !important; }

/* Streamlit Markdown Text */
.stMarkdown p {
    font-size: 1.0rem !important;
    line-height: 1.5 !important;
}

.scheme-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; gap: 10px; }
.scheme-title { color: #f1f5f9; font-size: 1.15rem; font-weight: 700; line-height: 1.3; word-break: break-word; }
.eligible-badge { background-color: #10b981; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; flex-shrink: 0; }
.reason-text { color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin-top: 8px; flex-grow: 1; }

/* Hide Streamlit Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Chat Styling */
.chat-message { padding: 1.0rem; border-radius: 8px; margin-bottom: 1.0rem; display: flex; flex-direction: column; }
.chat-message.user { background-color: #2b303b; align-items: flex-end; }
.chat-message.bot { background-color: #1e293b; align-items: flex-start; }
.chat-message .message-content { color: white; font-size: 1.0rem; }

/* Input Styling Override */
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
    background-color: #1e293b;
    color: white;
    border: 1px solid #334155;
    font-size: 1.0rem !important;
    min-height: 40px;
}
.stSelectbox div[data-baseweb="select"] span {
    font-size: 1.0rem !important;
}
label {
    font-size: 0.95rem !important;
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Logic ──────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "profile" not in st.session_state:
    st.session_state.profile = None

# ── Sidebar: Control Panel (ALL INPUTS HERE) ─────────────
with st.sidebar:
    st.title("🇮🇳 S.A.R.A.L.")
    st.caption("Scheme Access Retrieval Analysis Layer")
    st.markdown("---")
    
    st.markdown("### 👤 User Profile")
    with st.form("profile_form"):
        age = st.number_input("Age", min_value=1, max_value=120, value=25)
        
        state_options = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
            "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
            "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
            "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
            "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
            "West Bengal", "Delhi", "Jammu & Kashmir", "Ladakh",
        ]
        state = st.selectbox("State of Residence", state_options)

        occupation = st.selectbox("Occupation", [
            "Farmer", "Student", "Business", "Salaried",
            "Self-Employed", "Unemployed", "Retired", "Other",
        ])

        # Clean Integer Input for Income
        income = st.number_input("Annual Income (₹)", min_value=0, value=100000, step=10000)

        caste = st.selectbox("Category", [
            "General", "OBC", "SC", "ST", "EWS", "Other",
        ])

        language = st.selectbox("Language", ["English", "Hindi"]) 
        
        submitted = st.form_submit_button("Run Eligibility Check", help="Click to find schemes")

    if submitted:
        profile_data = {
            "age": age,
            "occupation": occupation,
            "state": state,
            "income": str(income),
            "caste": caste,
            "language": language,
        }
        st.session_state.profile = profile_data

        with st.spinner("Analyzing government database..."):
            try:
                result, debug_info = get_recommendations(profile_data)

                if result is None:
                    error_msg = debug_info.get("error", "Unknown Engine Error")
                    st.error(f"🚨 Raw Backend Error (Recommendations): {error_msg}")
                    
            except Exception as e:
                st.error(f"🚨 Frontend Error: {str(e)}")
                result = None

        if result:
            st.session_state.recommendations = result.get("recommendations", [])
        else:
            st.session_state.recommendations = "Error connecting to engine."

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("This tool uses an RAG pipeline to match your profile against thousands of government schemes.")

    st.markdown("""
    <div style="margin-top: 20px; font-size: 0.8rem; color: #64748b;">
        <strong>System Info:</strong><br>
        • Mode: Cloud Production ☁️<br>
        • Retriever: Hybrid RAG (v2.1)<br>
        • Engine: Groq Llama-3
    </div>
    """, unsafe_allow_html=True)


# ── Main Content Area (Header -> Results -> Chat) ────────

# 1. Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("S.A.R.A.L. Dashboard")
    st.caption("Scheme Access Retrieval Analysis Layer - AI Engine")
with col2:
    st.markdown("""
        <div style="background-color: rgba(16, 185, 129, 0.1); color: #34d399; padding: 5px 10px; border-radius: 20px; text-align: center; border: 1px solid rgba(16, 185, 129, 0.2); font-weight: 600; font-size: 0.8rem; margin-top: 20px;">
            ● SYSTEM ONLINE
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 2. Results Section
if st.session_state.recommendations is not None:
    recs = st.session_state.recommendations
    
    st.subheader(f"📋 Recommendation Results ({len(recs) if isinstance(recs, list) else 0})")
    
    if isinstance(recs, list) and len(recs) > 0:
        # Filter for eligible only
        eligible_schemes = [
            s for s in recs 
            if s.get("eligibility_status", "").lower() == "eligible"
        ]
        
        if eligible_schemes:
            # Grid Layout using Columns
            # We create a 3-column grid
            cols = st.columns(3)
            
            for idx, scheme in enumerate(eligible_schemes):
                name = scheme.get("scheme_name", "Unknown Scheme")
                reason = scheme.get("reason", "No reason provided.")
                
                # Construct HTML String
                card_html = f"""
                <div class="scheme-card">
                    <div class="scheme-header">
                        <span class="scheme-title">{name}</span>
                        <span class="eligible-badge">ELIGIBLE</span>
                    </div>
                    <div class="reason-text">
                        {reason}
                    </div>
                </div>
                """
                
                # Render IMMEDIATELY with unsafe_allow_html=True
                # Use modulo to place in correct column
                with cols[idx % 3]:
                    st.markdown(card_html, unsafe_allow_html=True)
            
        else:
            st.info("No matching schemes found based on your profile.")
    else:
        st.warning(str(recs))

    st.markdown("---")

# Invisible spacer to push content above the fixed chat input
st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)

# 3. Chat Interface
st.subheader("💬 AI Consultant")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
query = st.chat_input("Ask about a scheme, application process, or eligibility...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Consulting knowledge base..."):
            response, debug_info = get_chat_response(
                query,
                profile=st.session_state.profile,
                history=st.session_state.messages,
            )
        
        if response:
             answer = response.get("answer", "Error getting response.")
        else:
             error_msg = debug_info.get("error", "Unknown Chat Error")
             answer = f"🚨 **Connection Error:** {error_msg}"
             st.error(f"Raw Backend Error (Chat): {error_msg}")
        st.markdown(answer)
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
