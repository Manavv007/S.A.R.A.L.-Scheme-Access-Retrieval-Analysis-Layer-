import sys
import os
import html

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from src.utils.api_client import get_chat_response, get_recommendations

try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "PINECONE_API_KEY" in st.secrets:
        os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]
    if "HF_TOKEN" in st.secrets:
        os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]
except Exception:
    pass

st.set_page_config(
    page_title="S.A.R.A.L. - Scheme Access Retrieval Analysis Layer",
    layout="wide",
    page_icon="🇮🇳",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.stApp {
    background: #080c1a;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(56, 189, 248, 0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
    animation: gridShift 8s ease-in-out infinite alternate;
}

@keyframes gridShift {
    0% { transform: translate(0, 0); }
    100% { transform: translate(15px, 15px); }
}

h1 {
    font-size: 2.2rem !important;
    color: #f8fafc !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h2 { font-size: 1.4rem !important; color: #e2e8f0 !important; font-weight: 700 !important; letter-spacing: -0.01em !important; }
h3 { font-size: 1.1rem !important; color: #e2e8f0 !important; font-weight: 600 !important; }
.stMarkdown p { font-size: 0.9rem !important; line-height: 1.6 !important; color: #cbd5e1; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1126 0%, #0f172a 100%) !important;
    border-right: 1px solid rgba(51, 65, 85, 0.4) !important;
}

.scheme-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(51, 65, 85, 0.4);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    backdrop-filter: blur(20px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    height: 100%;
    min-height: 180px;
    display: flex;
    flex-direction: column;
}
.scheme-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #10b981, #38bdf8);
    opacity: 0;
    transition: opacity 0.3s;
}
.scheme-card:hover::before { opacity: 1; }
.scheme-card:hover {
    transform: translateY(-4px);
    border-color: rgba(56, 189, 248, 0.2);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(16, 185, 129, 0.05);
}

.scheme-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
    gap: 12px;
}
.scheme-title {
    color: #f1f5f9;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.4;
    word-break: break-word;
    flex: 1;
}
.eligible-badge {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
    flex-shrink: 0;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
    animation: pulseGlow 2s ease-in-out infinite;
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }
    50% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.4); }
}
.reason-text {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.6;
    flex-grow: 1;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(30, 41, 59, 0.8) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(51, 65, 85, 0.5) !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    min-height: 42px;
    transition: all 0.2s;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important;
}
.stSelectbox div[data-baseweb="select"] span { font-size: 0.9rem !important; color: #f1f5f9 !important; }
.stSelectbox div[data-baseweb="select"] { background: rgba(30, 41, 59, 0.8) !important; border-color: rgba(51, 65, 85, 0.5) !important; }
label { font-size: 0.82rem !important; color: #94a3b8 !important; font-weight: 500 !important; }

div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2) !important;
    cursor: pointer;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(16, 185, 129, 0.3) !important;
}

.chat-message { padding: 1rem 1.2rem; border-radius: 12px; margin-bottom: 1rem; display: flex; flex-direction: column; }
.chat-message.user {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(56, 189, 248, 0.1));
    border: 1px solid rgba(99, 102, 241, 0.2);
    align-items: flex-end;
}
.chat-message.bot {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(51, 65, 85, 0.3);
    align-items: flex-start;
}
.chat-message .message-content { color: #e2e8f0; font-size: 0.95rem; }

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(16, 185, 129, 0.2);
}
.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: dotPulse 1.5s ease-in-out infinite;
}
@keyframes dotPulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
    50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
}

.glow-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, #10b981, #38bdf8, #8b5cf6, transparent);
    width: 100%;
    margin: 8px 0;
    border-radius: 2px;
    animation: shimmer 3s ease-in-out infinite;
    background-size: 200% 100%;
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

footer {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0c1126; }
::-webkit-scrollbar-thumb { background: rgba(51, 65, 85, 0.5); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(71, 85, 105, 0.5); }

[data-testid="stChatInput"] {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(51, 65, 85, 0.4) !important;
    border-radius: 12px !important;
    transition: all 0.2s;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1) !important;
}

div[data-testid="metric-container"] {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.4));
    border: 1px solid rgba(51, 65, 85, 0.3);
    border-radius: 12px;
    padding: 16px;
}
div[data-testid="metric-container"] > label {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="metric-container"] > div {
    color: #f1f5f9 !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}

.stAlert { border-radius: 12px !important; border: 1px solid rgba(51, 65, 85, 0.3) !important; }
.st-ax { background-color: transparent !important; }
.st-b8 { background-color: transparent !important; }
.st-cf { background-color: transparent !important; }

[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

.stSpinner > div { border-color: #10b981 !important; border-right-color: transparent !important; }

.not-eligible-badge {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
    flex-shrink: 0;
    border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "loading" not in st.session_state:
    st.session_state.loading = False

with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
        <div style="font-size: 1.8rem;">🇮🇳</div>
        <div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">S.A.R.A.L.</div>
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 500;">Scheme Access Retrieval Analysis Layer</div>
        </div>
    </div>
    <div class="glow-line"></div>
    """, unsafe_allow_html=True)

    st.markdown("#### 👤 User Profile")
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

        income = st.number_input("Annual Income (₹)", min_value=0, value=100000, step=10000)

        caste = st.selectbox("Category", [
            "General", "OBC", "SC", "ST", "EWS", "Other",
        ])

        language = st.selectbox("Language", ["English", "Hindi", "Gujarati", "Telugu", "Marathi", "Tamil"])

        submitted = st.form_submit_button("⚡ Run Eligibility Check", help="Click to find schemes")

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
        st.session_state.loading = True

        with st.spinner("Analyzing government database..."):
            try:
                result, debug_info = get_recommendations(profile_data)
                if result is None:
                    error_msg = debug_info.get("error", "Unknown Engine Error")
                    st.error(f"🚨 Backend Error: {error_msg}")
            except Exception as e:
                st.error(f"🚨 Frontend Error: {str(e)}")
                result = None

        if result:
            st.session_state.recommendations = result.get("recommendations", [])
        else:
            st.session_state.recommendations = "Error connecting to engine."
        st.session_state.loading = False
        st.rerun()

    st.markdown("---")
    st.markdown("#### ℹ️ About")
    st.caption("RAG-powered AI that matches your profile against thousands of government schemes to find what you're eligible for.")

    st.markdown("""
    <div class="system-info">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
            <span class="status-dot"></span>
            <span style="color: #10b981; font-weight: 600;">System Online</span>
        </div>
        <div><strong style="color: #94a3b8;">Mode:</strong> Cloud Production ☁️</div>
        <div><strong style="color: #94a3b8;">Retriever:</strong> Hybrid RAG v2.1</div>
        <div><strong style="color: #94a3b8;">Engine:</strong> Groq Llama-3.3</div>
        <div><strong style="color: #94a3b8;">Languages:</strong> 6 supported</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([0.75, 0.25])
with col1:
    st.title("S.A.R.A.L. Dashboard")
    st.markdown('<p style="color: #64748b; margin-top: -8px; font-size: 0.9rem;">Scheme Access Retrieval Analysis Layer — AI-Powered Eligibility Engine</p>', unsafe_allow_html=True)
with col2:
    st.markdown("""
        <div class="status-badge" style="margin-top: 20px; float: right;">
            <span class="status-dot"></span>
            SYSTEM ONLINE
        </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

if st.session_state.recommendations is not None:
    recs = st.session_state.recommendations

    filtered_schemes = []
    if isinstance(recs, list):
        filtered_schemes = [
            s for s in recs
            if s.get("eligibility_status", "").lower() == "eligible"
        ]

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Schemes Found", len(filtered_schemes) if isinstance(recs, list) else 0)
    with col_m2:
        profile = st.session_state.profile or {}
        st.metric("Occupation", profile.get("occupation", "—"))
    with col_m3:
        profile = st.session_state.profile or {}
        st.metric("State", profile.get("state", "—"))

    st.markdown("")

    if filtered_schemes:
        for i in range(0, len(filtered_schemes), 3):
            chunk = filtered_schemes[i : i + 3]
            cols = st.columns(3)
            for j, scheme in enumerate(chunk):
                name = html.escape(str(scheme.get("scheme_name", "Unknown Scheme")))
                reason = html.escape(str(scheme.get("reason", "No reason provided.")))
                card_html = f"""
                <div class="scheme-card">
                    <div class="scheme-header">
                        <span class="scheme-title">{name}</span>
                        <span class="eligible-badge">✓ ELIGIBLE</span>
                    </div>
                    <div class="reason-text">{reason}</div>
                </div>
                """
                with cols[j]:
                    st.markdown(card_html, unsafe_allow_html=True)
    elif isinstance(recs, list):
        st.info("No matching schemes found based on your profile.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

st.markdown("#### 💬 AI Consultant")
st.markdown('<p style="color: #64748b; margin-top: -8px; font-size: 0.85rem;">Ask about schemes, application processes, or eligibility details</p>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
            st.error(f"Backend Error (Chat): {error_msg}")
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
