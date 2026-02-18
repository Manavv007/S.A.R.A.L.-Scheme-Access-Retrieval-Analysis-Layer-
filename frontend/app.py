"""
Streamlit frontend for BharatScheme-AI – Advisor Mode.
Premium UI with custom styling.
"""

import streamlit as st
from src.utils.api_client import get_chat_response, get_recommendations

# ── Localised UI labels ──────────────────────────────────
UI_TEXT = {
    "English": {
        "header": "Eligible Schemes for You",
        "status": "Status",
        "reason": "Reason",
        "eligible": "Eligible",
        "not_eligible": "Not Eligible",
        "no_schemes": "No eligible schemes found for your profile. Try adjusting your details.",
        "chat_header": "Ask the AI Advisor",
        "chat_placeholder": "Ask about a scheme...",
    },
    "Hindi": {
        "header": "आपके लिए पात्र योजनाएं",
        "status": "स्थिति",
        "reason": "कारण",
        "eligible": "पात्र",
        "not_eligible": "पात्र नहीं",
        "no_schemes": "आपकी प्रोफ़ाइल के लिए कोई पात्र योजना नहीं मिली। अपनी जानकारी बदलकर देखें।",
        "chat_header": "AI सलाहकार से पूछें",
        "chat_placeholder": "योजना के बारे में पूछें...",
    },
    "Gujarati": {
        "header": "તમારા માટે પાત્ર યોજનાઓ",
        "status": "સ્થિતિ",
        "reason": "કારણ",
        "eligible": "પાત્ર",
        "not_eligible": "પાત્ર નથી",
        "no_schemes": "તમારી પ્રોફાઇલ માટે કોઈ પાત્ર યોજના મળી નથી. તમારી વિગતો બદલીને જુઓ.",
        "chat_header": "AI સલાહકારને પૂછો",
        "chat_placeholder": "યોજના વિશે પૂછો...",
    },
    "Telugu": {
        "header": "మీకు అర్హమైన పథకాలు",
        "status": "స్థితి",
        "reason": "కారణం",
        "eligible": "అర్హత",
        "not_eligible": "అర్హత లేదు",
        "no_schemes": "మీ ప్రొఫైల్‌కు అర్హమైన పథకాలు కనుగొనబడలేదు.",
        "chat_header": "AI సలహాదారుని అడగండి",
        "chat_placeholder": "పథకం గురించి అడగండి...",
    },
    "Marathi": {
        "header": "तुमच्यासाठी पात्र योजना",
        "status": "स्थिती",
        "reason": "कारण",
        "eligible": "पात्र",
        "not_eligible": "पात्र नाही",
        "no_schemes": "तुमच्या प्रोफाइलसाठी कोणतीही पात्र योजना सापडली नाही.",
        "chat_header": "AI सल्लागाराला विचारा",
        "chat_placeholder": "योजनेबद्दल विचारा...",
    },
    "Tamil": {
        "header": "உங்களுக்கான தகுதியான திட்டங்கள்",
        "status": "நிலை",
        "reason": "காரணம்",
        "eligible": "தகுதியானது",
        "not_eligible": "தகுதி இல்லை",
        "no_schemes": "உங்கள் சுயவிவரத்திற்கு தகுதியான திட்டங்கள் எதுவும் கிடைக்கவில்லை.",
        "chat_header": "AI ஆலோசகரிடம் கேளுங்கள்",
        "chat_placeholder": "திட்டம் பற்றி கேளுங்கள்...",
    },
}

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="BharatScheme AI",
    layout="wide",
    page_icon="🇮🇳",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ─────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Hide Streamlit defaults ─────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Main background ─────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1e3f 0%, #141430 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    background: linear-gradient(90deg, #ffd700, #ff8c00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 1.25rem;
    letter-spacing: -0.3px;
}
section[data-testid="stSidebar"] label {
    color: #c0c0e0 !important;
    font-size: 0.82rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Hero banner ─────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner h1 {
    color: #fff;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
}
.hero-banner p {
    color: rgba(255, 255, 255, 0.85);
    font-size: 1rem;
    margin: 0.5rem 0 0;
    font-weight: 400;
}

/* ── Section headers ─────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 1rem;
}
.section-header .icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
}
.section-header .icon-green { background: rgba(16, 185, 129, 0.15); }
.section-header .icon-blue  { background: rgba(96, 165, 250, 0.15); }
.section-header h3 {
    color: #e0e0f0;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin: 0;
}

/* ── Scheme cards ────────────────────────────────── */
.scheme-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.scheme-card:hover {
    border-color: rgba(102, 126, 234, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}
.scheme-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #10b981, #34d399);
    border-radius: 4px 0 0 4px;
}
.scheme-name {
    color: #fff;
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.badge-eligible {
    display: inline-block;
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.scheme-reason {
    color: #b0b0d0;
    font-size: 0.92rem;
    line-height: 1.6;
    margin: 0;
}
.scheme-reason strong {
    color: #d0d0f0;
    font-weight: 600;
}

/* ── Chat section ────────────────────────────────── */
.chat-container {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.25rem;
    margin-top: 0.5rem;
}

/* ── Info box ────────────────────────────────────── */
.info-box {
    background: rgba(96, 165, 250, 0.08);
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #93c5fd;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ── Submit button ───────────────────────────────── */
section[data-testid="stSidebar"] .stFormSubmitButton button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1.5rem !important;
    width: 100%;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}
section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45) !important;
}

/* ── Form inputs ─────────────────────────────────── */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stNumberInput > div > div > input,
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #e0e0f0 !important;
}

/* ── Counter badge ───────────────────────────────── */
.counter-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 20px;
    padding: 4px 14px;
    color: #34d399;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

/* ── Divider ─────────────────────────────────────── */
.styled-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 2rem 0;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "English"

# ── Sidebar: User Profile Form ──────────────────────────
with st.sidebar:
    st.markdown("## 🇮🇳 Your Profile")
    with st.form("profile_form"):
        age = st.number_input("Age", min_value=1, max_value=120, value=25)
        state = st.selectbox("State", [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
            "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
            "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
            "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
            "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
            "West Bengal", "Delhi", "Jammu & Kashmir", "Ladakh",
        ])
        occupation = st.selectbox("Occupation", [
            "Farmer", "Student", "Business", "Salaried",
            "Self-Employed", "Unemployed", "Retired", "Other",
        ])
        income = st.text_input("Annual Income", placeholder="e.g. 2.5 Lakh")
        caste = st.selectbox("Caste Category", [
            "General", "OBC", "SC", "ST", "EWS", "Other",
        ])
        language = st.selectbox("Language", [
            "English", "Hindi", "Gujarati", "Telugu", "Marathi", "Tamil",
        ])

        submitted = st.form_submit_button("🔍  Check Eligibility")

    if submitted:
        st.session_state.selected_language = language
        profile_data = {
            "age": age,
            "occupation": occupation,
            "state": state,
            "income": income or "Not specified",
            "caste": caste,
            "language": language,
        }
        st.session_state.profile = profile_data

        with st.spinner("Finding eligible schemes..."):
            try:
                with st.expander("🔌 Debug Metadata", expanded=True):
                    st.write("Sending profile:", profile_data)
                    result = get_recommendations(profile_data)
                    st.write("Received response:", result)
            except Exception as e:
                st.error(f"Error: {e}")
                result = None

        if result:
            st.session_state.recommendations = result.get(
                "recommendations", "No recommendations found."
            )
        else:
            st.session_state.recommendations = (
                "⚠️ Could not reach the server. Is the backend running?"
            )

# ── Resolve current language labels ──────────────────────
lang = st.session_state.selected_language
labels = UI_TEXT.get(lang, UI_TEXT["English"])

# ── Hero Banner ──────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🇮🇳 BharatScheme AI Advisor</h1>
    <p>Discover government schemes you're eligible for — powered by AI</p>
</div>
""", unsafe_allow_html=True)

# ── Recommendations Section ──────────────────────────────
if st.session_state.recommendations:
    recs = st.session_state.recommendations

    # Section header
    st.markdown(f"""
    <div class="section-header">
        <div class="icon icon-green">📋</div>
        <h3>{labels["header"]}</h3>
    </div>
    """, unsafe_allow_html=True)

    if isinstance(recs, list):
        eligible = [
            s for s in recs
            if s.get("eligibility_status", "").strip().lower() == "eligible"
        ]
        if eligible:
            # Counter
            st.markdown(
                f'<div class="counter-badge">✅ {len(eligible)} scheme'
                f'{"s" if len(eligible) > 1 else ""} found</div>',
                unsafe_allow_html=True,
            )
            for scheme in eligible:
                name = scheme.get("scheme_name", "Unknown Scheme")
                reason = scheme.get("reason", "N/A")
                st.markdown(f"""
                <div class="scheme-card">
                    <div class="scheme-name">
                        🏛️ {name}
                        <span class="badge-eligible">{labels["eligible"]}</span>
                    </div>
                    <p class="scheme-reason">
                        <strong>{labels["reason"]}:</strong> {reason}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-box">
                ℹ️ {labels["no_schemes"]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="info-box">
            ℹ️ {recs}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

# ── Chat Section ─────────────────────────────────────────
st.markdown(f"""
<div class="section-header">
    <div class="icon icon-blue">💬</div>
    <h3>{labels["chat_header"]}</h3>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input(labels["chat_placeholder"])

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_chat_response(
                query,
                profile=st.session_state.profile,
                history=st.session_state.messages,
            )

        if response:
            answer = response.get("answer", "No answer received.")
        else:
            answer = "⚠️ Could not reach the server. Is the backend running?"

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
