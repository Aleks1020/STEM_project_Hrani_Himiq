
import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import cv2
import re
from datetime import datetime
import wikipedia
import warnings
import gc

warnings.filterwarnings("ignore")

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Food Ingredient Scanner",
    page_icon="🥗",
    layout="centered"
)

# =========================================================
# SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

# =========================================================
# LANGUAGES
# =========================================================

LANGUAGES = {
    "Български": "bg",
    "English": "en"
}

lang_choice = st.sidebar.selectbox(
    "🌍 Language",
    list(LANGUAGES.keys())
)

LANG = LANGUAGES[lang_choice]

# =========================================================
# TRANSLATIONS
# =========================================================

translations = {

    "bg": {
        "title": "🥗 AI Скенер за Хранителни Съставки",
        "upload": "Качи снимка",
        "camera": "Направи снимка",
        "scan": "Сканирай продукт",
        "detected": "Разпознат текст",
        "harmful": "Вредни съставки",
        "safe": "Няма открити опасни съставки",
        "score": "Оценка",
        "risk": "Риск",
        "summary": "Обобщение",
        "allergens": "Алергени",
        "replacement": "Алтернатива",
        "scanning": "Сканиране...",
        "low": "НИСКО",
        "medium": "СРЕДНО",
        "high": "ВИСОКО"
    },

    "en": {
        "title": "🥗 AI Food Ingredient Scanner",
        "upload": "Upload image",
        "camera": "Take photo",
        "scan": "Scan product",
        "detected": "Detected text",
        "harmful": "Harmful ingredients",
        "safe": "No harmful ingredients detected",
        "score": "Score",
        "risk": "Risk",
        "summary": "Summary",
        "allergens": "Allergens",
        "replacement": "Alternative",
        "scanning": "Scanning...",
        "low": "LOW",
        "medium": "MEDIUM",
        "high": "HIGH"
    }
}

t = translations[LANG]

# =========================================================
# INGREDIENT DATABASE
# =========================================================

harmful_ingredients = {

    "e621": {
        "name": "Monosodium Glutamate",
        "bg_name": "Мононатриев глутамат",
        "risk": "May cause headaches",
        "bg_risk": "Може да причини главоболие",
        "level": "medium",
        "score": -15
    },

    "e250": {
        "name": "Sodium Nitrite",
        "bg_name": "Натриев нитрит",
        "risk": "Linked to cancer risk",
        "bg_risk": "Свързва се с риск от рак",
        "level": "high",
        "score": -25
    },

    "aspartame": {
        "name": "Aspartame",
        "bg_name": "Аспартам",
        "risk": "Artificial sweetener",
        "bg_risk": "Изкуствен подсладител",
        "level": "high",
        "score": -20
    }
}

# =========================================================
# REPLACEMENTS
# =========================================================

healthy_alternatives = {
    "cola": "Sparkling water",
    "chips": "Baked chips",
    "energy drink": "Green tea",
    "candy": "Dark chocolate"
}

# =========================================================
# ALLERGENS
# =========================================================

allergens = [
    "milk",
    "soy",
    "gluten",
    "nuts",
    "egg"
]

# =========================================================
# OCR
# =========================================================

@st.cache_resource
def load_reader():

    try:

        return easyocr.Reader(
            ['bg', 'en'],
            gpu=False,
            verbose=False
        )

    except Exception as e:

        st.error(f"OCR Error: {e}")
        return None

reader = None

# =========================================================
# IMAGE PROCESSING
# =========================================================

def preprocess_image(image):

    try:

        img = np.array(image)

        if img is None or img.size == 0:
            return None

        # resize huge images
        max_width = 1200

        if img.shape[1] > max_width:

            scale = max_width / img.shape[1]

            img = cv2.resize(
                img,
                None,
                fx=scale,
                fy=scale
            )

        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        return thresh

    except:
        return None

# =========================================================
# OCR EXTRACTION
# =========================================================

def extract_text(image):

    global reader

    if reader is None:
        reader = load_reader()

    if reader is None:
        return ""

    processed = preprocess_image(image)

    if processed is None:
        return ""

    try:

        results = reader.readtext(
            processed,
            detail=0,
            paragraph=False
        )

        extracted_text = " ".join(results)

        return extracted_text

    except Exception as e:

        st.error(f"OCR Processing Error: {e}")
        return ""

# =========================================================
# ANALYSIS
# =========================================================

def normalize_text(text):

    return (
        text.lower()
        .replace("-", "")
        .replace(" ", "")
        .replace(",", "")
    )

def analyze_ingredients(text):

    found = []

    normalized_text = normalize_text(text)

    for ingredient, data in harmful_ingredients.items():

        if normalize_text(ingredient) in normalized_text:

            found.append(data)

    return found

def detect_allergens(text):

    found = []

    lower = text.lower()

    for allergen in allergens:

        if allergen in lower:
            found.append(allergen)

    return list(set(found))

def calculate_score(found):

    score = 100

    for item in found:
        score += item["score"]

    return max(0, min(score, 100))

def get_risk(score):

    if score >= 75:
        return t["low"]

    elif score >= 45:
        return t["medium"]

    return t["high"]

def get_summary(score):

    if score >= 75:
        return "✅ Safe product"

    elif score >= 45:
        return "⚠️ Moderate risk"

    return "🚨 High risk product"

def suggest_replacement(text):

    lower = text.lower()

    for key, value in healthy_alternatives.items():

        if key in lower:
            return value

    return "Fresh natural food"

# =========================================================
# WIKIPEDIA
# =========================================================

@st.cache_data(show_spinner=False)
def get_extended_info(name):

    try:

        wikipedia.set_lang("en")

        return wikipedia.summary(
            name,
            sentences=2
        )[:300]

    except:
        return None

# =========================================================
# UI
# =========================================================

st.title(t["title"])

uploaded_file = st.file_uploader(
    t["upload"],
    type=["png", "jpg", "jpeg"]
)

camera_image = st.camera_input(t["camera"])

image = None

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")

elif camera_image:
    image = Image.open(camera_image).convert("RGB")

# =========================================================
# MAIN
# =========================================================

if image is not None:

    st.image(image, use_container_width=True)

    if st.button(t["scan"], use_container_width=True):

        with st.spinner(t["scanning"]):

            extracted_text = extract_text(image)

            harmful_found = analyze_ingredients(extracted_text)

            allergens_found = detect_allergens(extracted_text)

            score = calculate_score(harmful_found)

            risk = get_risk(score)

            summary = get_summary(score)

            replacement = suggest_replacement(extracted_text)

        # TEXT

        st.subheader(t["detected"])

        st.text_area(
            "",
            extracted_text,
            height=180
        )

        # SCORE

        st.subheader(t["score"])

        st.progress(score / 100)

        st.metric(
            label=t["risk"],
            value=risk
        )

        # SUMMARY

        st.subheader(t["summary"])

        st.info(summary)

        # HARMFUL INGREDIENTS

        st.subheader(t["harmful"])

        if harmful_found:

            for item in harmful_found:

                ingredient_name = (
                    item["bg_name"]
                    if LANG == "bg"
                    else item["name"]
                )

                risk_text = (
                    item["bg_risk"]
                    if LANG == "bg"
                    else item["risk"]
                )

                st.error(
                    f"{ingredient_name}\n\n{risk_text}"
                )

                extra = get_extended_info(item["name"])

                if extra:
                    st.info(extra)

        else:

            st.success(t["safe"])

        # REPLACEMENT

        st.subheader(t["replacement"])

        st.success(replacement)

        # ALLERGENS

        st.subheader(t["allergens"])

        if allergens_found:

            for allergen in allergens_found:
                st.warning(allergen.upper())

        # HISTORY

        st.session_state.history.append({
            "Date": datetime.now(),
            "Score": score,
            "Risk": risk
        })

        history_df = pd.DataFrame(
            st.session_state.history
        )

        st.dataframe(
            history_df,
            use_container_width=True
        )

        gc.collect()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("---")

st.sidebar.info(
    """
AI Food Ingredient Scanner

• OCR recognition
• Harmful ingredient analysis
• Health score
• Allergens
• Product alternatives
"""
)
