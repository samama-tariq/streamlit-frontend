import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
import streamlit as st
import os

# =========================
# Config
# =========================
API_BASE_URL = "https://val-project-b3fd.onrender.com/api/analyze"

# API_BASE_URL = st.secrets.get(
#     "API_BASE_URL",
#     os.getenv("API_BASE_URL", "https://val-project-b3fd.onrender.com/api/analyze"),
# )

PURPOSE_OPTIONS = [
    ("No specific purpose", None),
    ("Leadership / Innovation", "leadership_innovation"),
    ("Partnership / Harmony", "partnership_harmony"),
    ("Creative Expression", "creative_expression"),
    ("Foundation / Stability", "foundation_stability"),
    ("Transformation / Freedom", "transformation_freedom"),
    ("Nurturing / Service", "nurturing_service"),
    ("Spiritual / Wisdom", "spiritual_wisdom"),
    ("Abundance / Authority", "abundance_authority"),
    ("Completion / Universal Love", "completion_universal_love"),
]


# =========================
# Helpers
# =========================

def score_to_color(score: float) -> str:
    """Map 0–1 score to a simple color name."""
    if score is None:
        return "gray"
    if score >= 0.8:
        return "green"
    if score >= 0.6:
        return "orange"
    return "red"


def render_score_badge(label: str, score: float):
    color = score_to_color(score)
    st.markdown(
        f"<span style='background-color:{color};"
        f"color:white;padding:3px 10px;border-radius:999px;"
        f"font-size:0.8rem;'>{label}: {score:.2f}</span>",
        unsafe_allow_html=True,
    )


def render_engine_card(name: str, engine_data: dict):
    score = engine_data.get("score", 0.0)
    details = engine_data.get("details", {}) or {}

    with st.container():
        st.markdown(f"#### {name.capitalize()}")
        render_score_badge("Score", score)

        with st.expander("Details", expanded=False):
            if name == "sentiment":
                st.write("**Raw sentiment scores:**")
                st.json(details)
            elif name == "phonosemantic":
                st.write(
                    f"- Size: **{details.get('size', 'n/a')}**\n"
                    f"- Texture: **{details.get('texture', 'n/a')}**"
                )
                st.write("**Ratios & counts:**")
                st.json(details)
            elif name == "numerology":
                st.write(
                    f"- Chaldean sum: **{details.get('chaldean_sum', 'n/a')}**\n"
                    f"- Reduced: **{details.get('reduced', 'n/a')}**"
                )
                notes = details.get("notes", [])
                if notes:
                    st.write("**Notes:**")
                    for n in notes:
                        st.write(f"- {n}")
            elif name == "cultural":
                st.write(f"- Risk level: **{details.get('risk_level', 'n/a')}**")
                flags = details.get("flags", [])
                if flags:
                    st.write("**Flags:**")
                    for f in flags:
                        word = f.get("word", "")
                        severity = f.get("severity", "")
                        reason = f.get("reason", "")
                        st.write(f"- `{word}` ({severity}): {reason}")
                explanation = details.get("explanation")
                if explanation:
                    st.write("**Explanation:**")
                    st.write(explanation)
            else:
                st.json(details)


def render_alternative_card(alt: dict, idx: int):
    text = alt.get("text", "")
    composite_score = alt.get("composite_score", 0.0)
    engines = alt.get("engines", {})
    reason = alt.get("reason")

    with st.container():
        st.markdown("---")
        st.markdown(f"### Alternative #{idx + 1}: **{text}**")
        render_score_badge("Composite", composite_score)

        if reason:
            st.markdown(f"**Why:** {reason}")

        # mini per-engine scores row
        if engines:
            st.markdown("**Engine scores:**")
            cols = st.columns(len(engines))
            for (name, data), col in zip(engines.items(), cols):
                with col:
                    score = data.get("score", 0.0)
                    color = score_to_color(score)
                    col.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='font-size:0.85rem;color:#555;'>{name}</div>"
                        f"<div style='font-weight:bold;color:{color};'>{score:.2f}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        with st.expander("Full details for this alternative"):
            st.json(alt)


# =========================
# Streamlit app layout
# =========================

# st.set_page_config(
#     page_title="VAL Language Analyzer",
#     page_icon="",
#     layout="wide",
# )

# st.title(" VAL Language Analyzer")
# st.caption(
#     "Analyze brand names & phrases across sentiment, sound symbolism, numerology, "
#     "and cultural risk – then discover better alternatives."
# )
st.set_page_config(
    page_title="V.A.L. – Vibration Analysis of Language",
    page_icon="✨",
    layout="wide",
)

st.title("V.A.L.")
st.subheader("Welcome to Vibration Analysis of Language")

st.markdown(
    """
**To use V.A.L.:**  
Key in your word or phrase, the region it applies to, which vibrational analysis you’re looking for,  
and its purpose (only if you’d like a numerological alignment analysis).
    """
)

# ---- Input Form on main page ----
with st.form("analyze_form"):
    st.markdown("### 1. Phrase & context")

    col1, col2 = st.columns([2, 1])

    with col1:
        text = st.text_area(
            "Word or short phrase",
            value="radiant glow",
            max_chars=250,
            help="Up to 250 characters.",
        )

    # with col2:
    #     target_market = st.selectbox(
    #         "Target market / region",
    #         options=["US", "GLOBAL", "EU", "MIDDLE_EAST", "OTHER"],
    #         index=0,
    #         help="Used mainly for cultural risk evaluation.",
    #     )


    #     purpose = st.selectbox(
    #         "Purpose",
    #         options=[
    #             "beauty_brand_tagline",
    #             "product_name",
    #             "brand_name",
    #             "campaign_slogan",
    #             "generic",
    #         ],
    #         index=0,
    #     )
    #     if purpose == "generic":
    #         purpose = None
    with col2:
        target_market = st.selectbox(
            "Region / market",
            options=["US", "GLOBAL", "EU", "MIDDLE_EAST", "OTHER"],
            index=0,
            help="Used for cultural risk analysis (where the phrase will be used).",
        )

        # Purpose is only meaningful when Numerology is enabled
        purpose_label_list = [label for (label, _value) in PURPOSE_OPTIONS]

        # When numerology is off, we disable the widget and force 'No specific purpose'
        if "purpose_index" not in st.session_state:
            st.session_state["purpose_index"] = 0

        purpose_index = st.selectbox(
            "Vibrational purpose (used only for numerology)",
            options=range(len(purpose_label_list)),
            format_func=lambda i: purpose_label_list[i],
            index=st.session_state["purpose_index"],
            disabled=False,  # we'll override below
            help="Choose the intended vibrational theme if Numerology is selected.",
        )

    # We’ll map this to the internal key later, taking numerology toggle into account.


    st.markdown("### 2. Engines & options")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Engines to apply**")
        sentiment_on = st.checkbox("Sentiment", value=True)
        phono_on = st.checkbox("Phonosemantic (sound symbolism)", value=True)
        numero_on = st.checkbox(
            "Numerology",
            value=True,
            help="Includes numerology value and alignment with the chosen purpose."
        )
        cultural_on = st.checkbox(
            "Cultural risk",
            value=True,
            help="LLM-based; adds some latency.",
        )

    with col4:
        st.markdown("**Alternatives**")
        generate_alternatives = st.checkbox("Generate alternatives", value=True)
        num_alternatives = st.slider(
            "Number of alternatives",
            min_value=1,
            max_value=10,
            value=5,
        )

    st.markdown("---")
    submit = st.form_submit_button("🚀 Analyze phrase", use_container_width=True)

if not submit:
    st.info(
        "Fill in the form above and click **“Analyze phrase”** to run the VAL engines "
        "and see composite scores plus AI-generated alternatives."
    )
    st.stop()

# ---- Validate and call backend ----
# if not text.strip():
#     st.error("Please enter a non-empty word or phrase.")
#     st.stop()

# payload = {
#     "text": text.strip(),
#     "target_market": target_market,
#     "purpose": purpose,
#     "engines": {
#         "sentiment": sentiment_on,
#         "phonosemantic": phono_on,
#         "numerology": numero_on,
#         "cultural": cultural_on,
#     },
#     "generate_alternatives": generate_alternatives,
#     "num_alternatives": num_alternatives,
# }

if not text.strip():
    st.error("Please enter a non-empty word or phrase.")
    st.stop()

# Map selected index to internal purpose key
if numero_on:
    # If numerology is ON, we honour the user’s selection
    selected_label, selected_key = PURPOSE_OPTIONS[purpose_index]
    st.session_state["purpose_index"] = purpose_index  # remember selection
    purpose_value = selected_key  # may be None for "No specific purpose"
else:
    # If numerology is OFF, purpose is irrelevant
    purpose_value = None

payload = {
    "text": text.strip(),
    "target_market": target_market,
    "purpose": purpose_value,
    "engines": {
        "sentiment": sentiment_on,
        "phonosemantic": phono_on,
        "numerology": numero_on,
        "cultural": cultural_on,
    },
    "generate_alternatives": generate_alternatives,
    "num_alternatives": num_alternatives,
}


# with st.spinner("Analyzing phrase with VAL engines..."):
#     try:
#         resp = requests.post(API_BASE_URL, json=payload, timeout=60)
#     except Exception as e:
#         st.error(f"Could not reach backend API: {e}")
#         st.stop()

# if resp.status_code != 200:
#     st.error(f"API error [{resp.status_code}]: {resp.text}")
#     st.stop()

with st.spinner("Analyzing phrase with VAL engines..."):
    try:
        # shorter timeout so it fails fast when the instance is waking up
        resp = requests.post(API_BASE_URL, json=payload, timeout=20)
    except Timeout:
        st.warning(
            "The analysis service is taking a bit longer to respond, likely because it is just starting up "
            "on the server. Please click **“🚀 Analyze phrase”** again."
        )
        st.stop()
    except ConnectionError:
        st.warning(
            "Could not reach the analysis service. It may still be starting or temporarily unavailable. "
            "Please try running the analysis again."
        )
        st.stop()
    except RequestException as e:
        st.error(
            "An unexpected error occurred while talking to the analysis service. "
            "Please try again, and if the problem persists, contact support."
        )
        # If you want to reveal the raw error for debugging, uncomment:
        # st.caption(str(e))
        st.stop()

# Handle non-200 responses nicely
if resp.status_code >= 500:
    st.warning(
        "The analysis service returned a server error. This can happen briefly when the backend is waking up "
        "on the free hosting tier. Please run the analysis again."
    )
    st.stop()
elif resp.status_code != 200:
    st.error(f"API error [{resp.status_code}]: {resp.text}")
    st.stop()

data = resp.json()

# =========================
# Results layout
# =========================

st.markdown("## 3. Results")

# --- Original phrase summary ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown(f"### Original phrase: **\"{data.get('text', '')}\"**")
    st.write(f"Length: `{data.get('length', 0)}` characters")

    composite = data.get("composite_score", 0.0)
    st.markdown("**Overall composite score**")
    render_score_badge("Composite", composite)
    st.progress(min(max(composite, 0.0), 1.0))

with col_right:
    st.markdown("**Quick engine scores**")
    engines = data.get("engines", {}) or {}
    if engines:
        for name, engine_data in engines.items():
            score = engine_data.get("score", 0.0)
            color = score_to_color(score)
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-bottom:4px;'>"
                f"<span style='font-size:0.85rem;'>{name.capitalize()}</span>"
                f"<span style='font-weight:bold;color:{color};'>{score:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.write("No engines enabled.")

# --- Engine detail cards ---
if engines:
    st.markdown("### 4. Engine details")
    cols = st.columns(4)
    idx = 0
    for name, engine_data in engines.items():
        with cols[idx % 4]:
            render_engine_card(name, engine_data)
        idx += 1

# --- Alternatives ---
alternatives = data.get("alternatives", []) or []
if generate_alternatives:
    st.markdown("---")
    st.markdown("### 5. AI-generated alternatives")

    if not alternatives:
        st.warning("No alternatives returned by the model.")
    else:
        st.caption(
            "Alternatives are generated by OpenAI, then scored with the same engines "
            "and ranked by composite score."
        )
        for i, alt in enumerate(alternatives):
            render_alternative_card(alt, i)

# --- Optional raw response ---
with st.expander("🔍 Raw API response (debug)", expanded=False):
    st.json(data)
