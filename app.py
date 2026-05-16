
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

warnings.filterwarnings("ignore")

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Food Ingredient Scanner",
    page_icon="🥗",
    layout="wide"
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
    "English": "en",
    "Deutsch": "de",
    "Español": "es"
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
        "harmful": "Открити вредни съставки",
        "safe": "Няма открити опасни съставки",
        "score": "Оценка на продукта",
        "risk": "Ниво на риск",
        "summary": "AI Обобщение",
        "history": "История",
        "allergens": "Алергени",
        "nutrition": "Хранителен анализ",
        "detected_ingredients": "Засечени съставки",
        "category": "Категория",
        "danger": "Ниво на опасност",
        "scanning": "Сканиране...",
        "replacement": "По-здравословна алтернатива",
        "ocr_detection": "OCR Разпознаване",
        "no_allergens": "Няма открити алергени.",
        "nutrition_ok": "Няма сериозни хранителни предупреждения.",
        "high_sugar": "Засечено е високо съдържание на захар.",
        "salt": "Засечена е сол/натрий.",
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
        "harmful": "Detected harmful ingredients",
        "safe": "No harmful ingredients detected",
        "score": "Product score",
        "risk": "Risk level",
        "summary": "AI Summary",
        "history": "History",
        "allergens": "Allergens",
        "nutrition": "Nutrition analysis",
        "detected_ingredients": "Detected ingredients",
        "category": "Category",
        "danger": "Danger level",
        "scanning": "Scanning...",
        "replacement": "Healthier alternative",
        "ocr_detection": "OCR Detection",
        "no_allergens": "No allergens detected.",
        "nutrition_ok": "No major nutrition warnings.",
        "high_sugar": "High sugar detected.",
        "salt": "Salt/sodium detected.",
        "low": "LOW",
        "medium": "MEDIUM",
        "high": "HIGH"
    }
}

t = translations.get(LANG, translations["en"])

# =========================================================
# HARMFUL INGREDIENTS DATABASE
# =========================================================

harmful_ingredients = {

    "e621": {
        "name": "Monosodium Glutamate",
        "bg_name": "Мононатриев глутамат",
        "risk": "May cause headaches and water retention",
        "bg_risk": "Може да причини главоболие",
        "level": "medium",
        "category": "Flavor Enhancer",
        "score": -15
    },

    "e407": {
        "name": "Carrageenan",
        "bg_name": "Карагенан",
        "risk": "May cause inflammation",
        "bg_risk": "Може да причини възпаления",
        "level": "high",
        "category": "Stabilizer",
        "score": -20
    },

    "e250": {
        "name": "Sodium Nitrite",
        "bg_name": "Натриев нитрит",
        "risk": "Linked to cancer risk",
        "bg_risk": "Свързва се с риск от рак",
        "level": "high",
        "category": "Preservative",
        "score": -25
    },

    "aspartame": {
        "name": "Aspartame",
        "bg_name": "Аспартам",
        "risk": "Artificial sweetener",
        "bg_risk": "Изкуствен подсладител",
        "level": "high",
        "category": "Sweetener",
        "score": -20
    },

    "transfat": {
        "name": "Trans Fat",
        "bg_name": "Транс мазнини",
        "risk": "Increases cardiovascular risk",
        "bg_risk": "Повишава риска от сърдечни заболявания",
        "level": "high",
        "category": "Fat",
        "score": -25
    }
}

# =========================================================
# HEALTHY REPLACEMENTS
# =========================================================

healthy_alternatives = {
    "cola": "Sparkling water with lemon",
    "chips": "Baked chips",
    "nutella": "Natural peanut butter",
    "energy drink": "Green tea",
    "processed meat": "Fresh grilled chicken",
    "candy": "Dark chocolate",
    "soda": "Mineral water",
    "instant noodles": "Whole grain pasta"
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
    "wheat",
    "egg"
]

# =========================================================
# OCR
# =========================================================

@st.cache_resource
def load_reader(lang):

    try:

        if lang == "bg":
            return easyocr.Reader(['bg', 'en'], gpu=False)

        elif lang == "de":
            return easyocr.Reader(['de', 'en'], gpu=False)

        elif lang == "es":
            return easyocr.Reader(['es', 'en'], gpu=False)

        return easyocr.Reader(['en'], gpu=False)

    except Exception as e:
        st.error(f"OCR Error: {e}")
        return None

reader = load_reader(LANG)

# =========================================================
# IMAGE PROCESSING
# =========================================================

def preprocess_image(image):

    try:

        img = np.array(image)

        if img is None or img.size == 0:
            return None

        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=0)

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

    if reader is None:
        return "", []

    processed = preprocess_image(image)

    if processed is None:
        return "", []

    try:

        results = reader.readtext(
            processed,
            detail=1,
            paragraph=False
        )

        results = [
            r for r in results
            if r[2] > 0.4
        ]

        extracted_text = " ".join(
            [res[1] for res in results]
        )

        return extracted_text, results

    except Exception as e:

        st.error(f"OCR Processing Error: {e}")
        return "", []

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

        normalized_ingredient = normalize_text(ingredient)

        if normalized_ingredient in normalized_text:

            found.append({
                "ingredient": ingredient,
                "data": data
            })

    return found

def detect_e_numbers(text):

    return re.findall(r'e\d{3,4}', text.lower())

def detect_allergens(text):

    found = []

    lower_text = text.lower()

    for allergen in allergens:

        if allergen in lower_text:
            found.append(allergen)

    return list(set(found))

def calculate_score(found_ingredients):

    score = 100

    for item in found_ingredients:
        score += item["data"]["score"]

    return max(0, min(score, 100))

def get_score_color(score):

    if score >= 75:
        return "#22c55e"

    elif score >= 45:
        return "#f59e0b"

    return "#ef4444"

def get_risk_label(score):

    if score >= 75:
        return t["low"]

    elif score >= 45:
        return t["medium"]

    return t["high"]

def generate_summary(score):

    if score >= 75:
        return "✅ Product appears relatively safe."

    elif score >= 45:
        return "⚠️ Product contains some potentially harmful ingredients."

    return "🚨 Product contains multiple harmful ingredients."

def suggest_replacement(text):

    lower = text.lower()

    for key, value in healthy_alternatives.items():

        if key in lower:
            return value

    return "Fresh natural foods"

# =========================================================
# WIKIPEDIA
# =========================================================

@st.cache_data(show_spinner=False)
def get_extended_info(ingredient):

    try:

        wikipedia.set_lang("en")

        summary = wikipedia.summary(
            ingredient,
            sentences=2
        )

        return summary[:500]

    except:
        return None

# =========================================================
# HEADER
# =========================================================

st.title(t["title"])

# =========================================================
# FILE INPUT
# =========================================================

uploaded_file = st.file_uploader(
    t["upload"],
    type=["png", "jpg", "jpeg"]
)

with st.container():
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

    scan_btn = st.button(
        t["scan"],
        use_container_width=True,
        type="primary"
    )

    if scan_btn:

        with st.spinner(t["scanning"]):

            extracted_text, ocr_results = extract_text(image)

            harmful_found = analyze_ingredients(extracted_text)

            allergen_found = detect_allergens(extracted_text)

            e_numbers = detect_e_numbers(extracted_text)

            score = calculate_score(harmful_found)

            color = get_score_color(score)

            risk = get_risk_label(score)

            summary = generate_summary(score)

            replacement = suggest_replacement(extracted_text)

        # =====================================================
        # DETECTED TEXT
        # =====================================================

        st.subheader(f"📝 {t['detected']}")

        st.text_area(
            "",
            extracted_text,
            height=200
        )

        # =====================================================
        # DETECTED INGREDIENTS
        # =====================================================

        st.subheader(f"🧪 {t['detected_ingredients']}")

        words = re.findall(
            r'\b[a-zA-ZА-Яа-я0-9\-]+\b',
            extracted_text
        )

        unique_words = sorted(set(words))

        st.write(", ".join(unique_words[:150]))

        # =====================================================
        # E NUMBERS
        # =====================================================

        if e_numbers:

            st.subheader("🧬 E-Numbers")

            st.warning(", ".join(set(e_numbers)))

        # =====================================================
        # SCORE
        # =====================================================

        st.subheader(f"📊 {t['score']}")

        st.markdown(
            f"""
            <div style="
                padding:20px;
                border-radius:15px;
                background:{color};
                color:white;
                text-align:center;
                font-size:32px;
                font-weight:bold;
            ">
                {score}/100
                <br>
                {t['risk']}: {risk}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(score / 100)

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

                st.error(
                    f"""
Ingredient: {ingredient_name}

Category: {data['category']}
Risk: {risk_text}
Danger: {data['level'].upper()}
"""
                )

                extra = get_extended_info(data["name"])

                if extra:
                    st.info(extra)

        else:

            st.success(t["safe"])

        # =====================================================
        # REPLACEMENT
        # =====================================================

        st.subheader(f"🥦 {t['replacement']}")

        st.success(replacement)

        # =====================================================
        # ALLERGENS
        # =====================================================

        st.subheader(f"🚨 {t['allergens']}")

        if allergen_found:

            for allergen in allergen_found:
                st.warning(allergen.upper())

        else:

            st.success(t["no_allergens"])

        # =====================================================
        # NUTRITION
        # =====================================================

        st.subheader(f"🥗 {t['nutrition']}")

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

        if any(word in lower_text for word in sugar_patterns):
            nutrition_notes.append(t["high_sugar"])

        if any(word in lower_text for word in salt_patterns):
            nutrition_notes.append(t["salt"])

        if nutrition_notes:

            for note in nutrition_notes:
                st.warning(note)

        else:

            st.success(t["nutrition_ok"])

        # =====================================================
        # OCR BOXES
        # =====================================================

        st.subheader(f"📦 {t['ocr_detection']}")

        img_array = np.array(image).copy()

        for detection in ocr_results:

            try:

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

            except:
                pass

        st.image(
            img_array,
            use_container_width=True
        )

        # =====================================================
        # HISTORY
        # =====================================================

        st.session_state.history.append({
            "Date": datetime.now(),
            "Score": score,
            "Risk": risk,
            "Detected Ingredients": len(harmful_found)
        })

        st.subheader(f"📁 {t['history']}")

        history_df = pd.DataFrame(
            st.session_state.history
        )

        st.dataframe(
            history_df,
            use_container_width=True
        )

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("---")

st.sidebar.info(
    """
🥗 AI Food Ingredient Scanner

Features:
- OCR text recognition
- Harmful ingredient detection
- Health score
- Allergen detection
- Product replacement
- Camera support
- Multi-language
- Streamlit optimized
"""
)
