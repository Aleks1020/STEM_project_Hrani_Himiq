import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import cv2
import re
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Food Ingredient Scanner AI",
    page_icon="🥗",
    layout="wide"
)

# =========================================================
# LANGUAGE SYSTEM
# =========================================================

LANGUAGES = {
    "Български": "bg",
    "English": "en"
}

lang_choice = st.sidebar.selectbox(
    "🌍 Language / Език",
    list(LANGUAGES.keys())
)

LANG = LANGUAGES[lang_choice]

translations = {
    "bg": {
        "title": "🥗 AI Скенер за Хранителни Съставки",
        "upload": "Качи снимка",
        "camera": "Направи снимка",
        "scan": "Сканирай продукт",
        "detected": "Разпознат текст",
        "harmful": "Открити вредни съставки",
        "safe": "Няма открити опасни съставки",
        "score": "Оценка на продукта",
        "risk": "Ниво на риск",
        "ingredients": "Анализ на съставките",
        "summary": "AI Обобщение",
        "history": "История",
        "allergens": "Алергени",
        "nutrition": "Хранителен анализ"
    },
    "en": {
        "title": "🥗 AI Food Ingredient Scanner",
        "upload": "Upload image",
        "camera": "Take photo",
        "scan": "Scan product",
        "detected": "Detected text",
        "harmful": "Detected harmful ingredients",
        "safe": "No harmful ingredients detected",
        "score": "Product score",
        "risk": "Risk level",
        "ingredients": "Ingredient analysis",
        "summary": "AI Summary",
        "history": "History",
        "allergens": "Allergens",
        "nutrition": "Nutrition analysis"
    }
}

t = translations[LANG]

# =========================================================
# HARMFUL INGREDIENT DATABASE
# =========================================================

harmful_ingredients = {
    "e621": {
        "name": "Monosodium Glutamate",
        "bg_name": "Мононатриев глутамат",
        "risk": "May cause headaches and water retention",
        "bg_risk": "Може да причини главоболие и задържане на вода",
        "level": "medium",
        "category": "Flavor Enhancer",
        "score": -15
    },
    "palm oil": {
        "name": "Palm Oil",
        "bg_name": "Палмово масло",
        "risk": "High saturated fat content",
        "bg_risk": "Високо съдържание на наситени мазнини",
        "level": "medium",
        "category": "Fat",
        "score": -10
    },
    "aspartame": {
        "name": "Aspartame",
        "bg_name": "Аспартам",
        "risk": "Artificial sweetener with controversial effects",
        "bg_risk": "Изкуствен подсладител с противоречиви ефекти",
        "level": "high",
        "category": "Sweetener",
        "score": -20
    },
    "e211": {
        "name": "Sodium Benzoate",
        "bg_name": "Натриев бензоат",
        "risk": "May cause hyperactivity",
        "bg_risk": "Може да причини хиперактивност",
        "level": "high",
        "category": "Preservative",
        "score": -18
    },
    "trans fat": {
        "name": "Trans Fat",
        "bg_name": "Транс мазнини",
        "risk": "Increases cardiovascular risk",
        "bg_risk": "Повишава риска от сърдечни заболявания",
        "level": "high",
        "category": "Fat",
        "score": -25
    },
    "e102": {
        "name": "Tartrazine",
        "bg_name": "Тартразин",
        "risk": "May cause allergic reactions",
        "bg_risk": "Може да причини алергични реакции",
        "level": "medium",
        "category": "Coloring",
        "score": -12
    }
}

# =========================================================
# ALLERGENS
# =========================================================

allergens = [
    "milk",
    "soy",
    "gluten",
    "nuts",
    "peanuts",
    "lactose",
    "wheat"
]

# =========================================================
# FUNCTIONS
# =========================================================

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en', 'bg'])

reader = load_reader()

def preprocess_image(image):
    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

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

def extract_text(image):
    processed = preprocess_image(image)

    results = reader.readtext(processed)

    extracted_text = " ".join([res[1] for res in results])

    return extracted_text, results

def analyze_ingredients(text):
    found = []

    lower_text = text.lower()

    for ingredient, data in harmful_ingredients.items():
        if ingredient in lower_text:
            found.append({
                "ingredient": ingredient,
                "data": data
            })

    return found

def detect_allergens(text):
    found = []

    lower_text = text.lower()

    for allergen in allergens:
        if allergen in lower_text:
            found.append(allergen)

    return found

def calculate_score(found_ingredients):
    score = 100

    for item in found_ingredients:
        score += item["data"]["score"]

    score = max(0, min(score, 100))

    return score

def get_score_color(score):
    if score >= 75:
        return "green"
    elif score >= 45:
        return "orange"
    else:
        return "red"

def get_risk_label(score):
    if score >= 75:
        return "LOW"
    elif score >= 45:
        return "MEDIUM"
    else:
        return "HIGH"

def generate_summary(score, harmful_count):
    if score >= 75:
        return "This product appears relatively safe."
    elif score >= 45:
        return "This product contains some potentially harmful ingredients."
    else:
        return "This product contains multiple harmful ingredients and is not recommended for frequent consumption."

# =========================================================
# HEADER
# =========================================================

st.title(t["title"])

# =========================================================
# INPUTS
# =========================================================

uploaded_file = st.file_uploader(
    t["upload"],
    type=["png", "jpg", "jpeg"]
)

camera_image = st.camera_input(t["camera"])

image = None

if uploaded_file:
    image = Image.open(uploaded_file)

elif camera_image:
    image = Image.open(camera_image)

# =========================================================
# MAIN PROCESS
# =========================================================

if image is not None:

    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button(t["scan"]):

        with st.spinner("Scanning..."):

            extracted_text, ocr_results = extract_text(image)

            harmful_found = analyze_ingredients(extracted_text)

            allergen_found = detect_allergens(extracted_text)

            score = calculate_score(harmful_found)

            color = get_score_color(score)

            risk = get_risk_label(score)

            summary = generate_summary(score, len(harmful_found))

        # =====================================================
        # OCR TEXT
        # =====================================================

        st.subheader(f"📝 {t['detected']}")

        st.text_area(
            "",
            extracted_text,
            height=200
        )

        # =====================================================
        # SCORE
        # =====================================================

        st.subheader(f"📊 {t['score']}")

        st.markdown(
            f"""
            <div style="
                padding:20px;
                border-radius:15px;
                background-color:{color};
                color:white;
                text-align:center;
                font-size:30px;
                font-weight:bold;
            ">
                {score}/100
                <br>
                Risk: {risk}
            </div>
            """,
            unsafe_allow_html=True
        )

        # =====================================================
        # SUMMARY
        # =====================================================

        st.subheader(f"🤖 {t['summary']}")

        st.info(summary)

        # =====================================================
        # HARMFUL INGREDIENTS
        # =====================================================

        st.subheader(f"⚠️ {t['harmful']}")

        if harmful_found:

            for item in harmful_found:

                data = item["data"]

                if data["level"] == "high":
                    emoji = "🔴"
                elif data["level"] == "medium":
                    emoji = "🟡"
                else:
                    emoji = "🟢"

                ingredient_name = (
                    data["bg_name"]
                    if LANG == "bg"
                    else data["name"]
                )

                risk_text = (
                    data["bg_risk"]
                    if LANG == "bg"
                    else data["risk"]
                )

                st.markdown(
                    f"""
                    ### {emoji} {ingredient_name}

                    - Category: {data['category']}
                    - Risk: {risk_text}
                    - Danger Level: {data['level'].upper()}
                    """
                )

        else:
            st.success(t["safe"])

        # =====================================================
        # ALLERGENS
        # =====================================================

        st.subheader(f"🚨 {t['allergens']}")

        if allergen_found:

            for allergen in allergen_found:
                st.warning(allergen.upper())

        else:
            st.success("No allergens detected.")

        # =====================================================
        # NUTRITION ANALYSIS
        # =====================================================

        st.subheader(f"🥦 {t['nutrition']}")

        nutrition_notes = []

        lower_text = extracted_text.lower()

        sugar_patterns = [
            "sugar",
            "glucose",
            "fructose",
            "corn syrup"
        ]

        salt_patterns = [
            "salt",
            "sodium"
        ]

        for word in sugar_patterns:
            if word in lower_text:
                nutrition_notes.append(
                    "High sugar indicators detected."
                )
                break

        for word in salt_patterns:
            if word in lower_text:
                nutrition_notes.append(
                    "Salt/sodium detected."
                )
                break

        if nutrition_notes:
            for note in nutrition_notes:
                st.warning(note)
        else:
            st.success("No major nutrition warnings.")

        # =====================================================
        # OCR BOXES VISUALIZATION
        # =====================================================

        st.subheader("📦 OCR Detection")

        img_array = np.array(image)

        for detection in ocr_results:

            bbox = detection[0]

            top_left = tuple(map(int, bbox[0]))
            bottom_right = tuple(map(int, bbox[2]))

            cv2.rectangle(
                img_array,
                top_left,
                bottom_right,
                (0, 255, 0),
                2
            )

        st.image(img_array, use_column_width=True)

        # =====================================================
        # HISTORY
        # =====================================================

        st.subheader(f"📁 {t['history']}")

        history_data = {
            "Date": [datetime.now()],
            "Score": [score],
            "Risk": [risk],
            "Detected Harmful Ingredients": [len(harmful_found)]
        }

        history_df = pd.DataFrame(history_data)

        st.dataframe(history_df)

# =========================================================
# SIDEBAR INFO
# =========================================================

st.sidebar.markdown("---")

st.sidebar.info(
    """
    🧠 AI Ingredient Scanner

    Features:
    - OCR text recognition
    - Harmful ingredient detection
    - Health score
    - Allergen detection
    - Camera support
    - Bulgarian & English support
    """
)
