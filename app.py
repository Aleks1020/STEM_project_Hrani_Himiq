
import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import cv2
import re
from datetime import datetime
import wikipedia

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Food Ingredient Scanner",
    page_icon="🥗",
    layout="wide"
)

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
        "ocr_detection": "OCR Разпознаване",
        "no_allergens": "Няма открити алергени.",
        "nutrition_ok": "Няма сериозни хранителни предупреждения.",
        "high_sugar": "Засечени са индикатори за високо съдържание на захар.",
        "salt": "Засечена е сол/натрий.",
        "low": "НИСКО",
        "medium": "СРЕДНО",
        "high": "ВИСОКО",
        "extended_info": "Разширена информация"
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
        "ocr_detection": "OCR Detection",
        "no_allergens": "No allergens detected.",
        "nutrition_ok": "No major nutrition warnings.",
        "high_sugar": "High sugar indicators detected.",
        "salt": "Salt/sodium detected.",
        "low": "LOW",
        "medium": "MEDIUM",
        "high": "HIGH",
        "extended_info": "Extended Information"
    },

    "de": {
        "title": "🥗 KI Lebensmittel Scanner",
        "upload": "Bild hochladen",
        "camera": "Foto aufnehmen",
        "scan": "Produkt scannen",
        "detected": "Erkannter Text",
        "harmful": "Gefundene schädliche Zutaten",
        "safe": "Keine gefährlichen Zutaten gefunden",
        "score": "Produktbewertung",
        "risk": "Risikostufe",
        "summary": "KI Zusammenfassung",
        "history": "Verlauf",
        "allergens": "Allergene",
        "nutrition": "Nährwertanalyse",
        "detected_ingredients": "Erkannte Zutaten",
        "category": "Kategorie",
        "danger": "Gefahrenstufe",
        "scanning": "Scannen...",
        "ocr_detection": "OCR Erkennung",
        "no_allergens": "Keine Allergene erkannt.",
        "nutrition_ok": "Keine größeren Ernährungswarnungen.",
        "high_sugar": "Hoher Zuckergehalt erkannt.",
        "salt": "Salz/Natrium erkannt.",
        "low": "NIEDRIG",
        "medium": "MITTEL",
        "high": "HOCH",
        "extended_info": "Erweiterte Informationen"
    },

    "es": {
        "title": "🥗 Escáner IA de Ingredientes",
        "upload": "Subir imagen",
        "camera": "Tomar foto",
        "scan": "Escanear producto",
        "detected": "Texto detectado",
        "harmful": "Ingredientes dañinos detectados",
        "safe": "No se detectaron ingredientes peligrosos",
        "score": "Puntuación del producto",
        "risk": "Nivel de riesgo",
        "summary": "Resumen IA",
        "history": "Historial",
        "allergens": "Alérgenos",
        "nutrition": "Análisis nutricional",
        "detected_ingredients": "Ingredientes detectados",
        "category": "Categoría",
        "danger": "Nivel de peligro",
        "scanning": "Escaneando...",
        "ocr_detection": "Detección OCR",
        "no_allergens": "No se detectaron alérgenos.",
        "nutrition_ok": "No hay advertencias nutricionales importantes.",
        "high_sugar": "Se detectó alto contenido de azúcar.",
        "salt": "Se detectó sal/sodio.",
        "low": "BAJO",
        "medium": "MEDIO",
        "high": "ALTO",
        "extended_info": "Información extendida"
    }
}

t = translations[LANG]

# =========================================================
# HARMFUL INGREDIENTS DATABASE
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

    "e407": {
        "name": "Carrageenan",
        "bg_name": "Карагенан",
        "risk": "May cause inflammation and digestive issues",
        "bg_risk": "Може да причини възпаления и храносмилателни проблеми",
        "level": "high",
        "category": "Stabilizer",
        "score": -20
    },

    "e250": {
        "name": "Sodium Nitrite",
        "bg_name": "Натриев нитрит",
        "risk": "Linked to cancer risk",
        "bg_risk": "Свързва се с риск от онкологични заболявания",
        "level": "high",
        "category": "Preservative",
        "score": -25
    },

    "e330": {
        "name": "Citric Acid",
        "bg_name": "Лимонена киселина",
        "risk": "May damage tooth enamel",
        "bg_risk": "Може да увреди зъбния емайл",
        "level": "low",
        "category": "Acidity Regulator",
        "score": -5
    },

    "e952": {
        "name": "Cyclamate",
        "bg_name": "Цикламат",
        "risk": "Artificial sweetener with controversial effects",
        "bg_risk": "Изкуствен подсладител със спорни ефекти",
        "level": "medium",
        "category": "Sweetener",
        "score": -15
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

    "trans fat": {
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
# OCR
# =========================================================

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en', 'bg', 'de', 'es'])

reader = load_reader()

# =========================================================
# FUNCTIONS
# =========================================================

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

    normalized_text = lower_text.replace("-", "").replace(" ", "")

    for ingredient, data in harmful_ingredients.items():

        normalized_ingredient = ingredient.replace("-", "").replace(" ", "")

        if normalized_ingredient in normalized_text:

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

    return "red"

def get_risk_label(score):

    if score >= 75:
        return t["low"]

    elif score >= 45:
        return t["medium"]

    return t["high"]

def generate_summary(score):

    if LANG == "bg":

        if score >= 75:
            return "Продуктът изглежда сравнително безопасен."

        elif score >= 45:
            return "Продуктът съдържа потенциално вредни съставки."

        return "Продуктът съдържа множество вредни съставки."

    elif LANG == "de":

        if score >= 75:
            return "Dieses Produkt scheint relativ sicher zu sein."

        elif score >= 45:
            return "Dieses Produkt enthält potenziell schädliche Inhaltsstoffe."

        return "Dieses Produkt enthält mehrere schädliche Inhaltsstoffe."

    elif LANG == "es":

        if score >= 75:
            return "Este producto parece relativamente seguro."

        elif score >= 45:
            return "Este producto contiene ingredientes potencialmente dañinos."

        return "Este producto contiene múltiples ingredientes dañinos."

    else:

        if score >= 75:
            return "This product appears relatively safe."

        elif score >= 45:
            return "This product contains some potentially harmful ingredients."

        return "This product contains multiple harmful ingredients."

def get_extended_info(ingredient):

    try:

        wikipedia.set_lang("en")

        summary = wikipedia.summary(ingredient, sentences=2)

        return summary

    except:
        return None

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

    st.image(image, use_column_width=True)

    if st.button(t["scan"]):

        with st.spinner(t["scanning"]):

            extracted_text, ocr_results = extract_text(image)

            harmful_found = analyze_ingredients(extracted_text)

            allergen_found = detect_allergens(extracted_text)

            score = calculate_score(harmful_found)

            color = get_score_color(score)

            risk = get_risk_label(score)

            summary = generate_summary(score)

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
        # DETECTED INGREDIENTS
        # =====================================================

        st.subheader(f"🧪 {t['detected_ingredients']}")

        words = re.findall(r'\b[a-zA-ZА-Яа-я0-9\-]+\b', extracted_text)

        unique_words = sorted(set(words))

        st.write(", ".join(unique_words[:150]))

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

                    - {t['category']}: {data['category']}
                    - {t['risk']}: {risk_text}
                    - {t['danger']}: {data['level'].upper()}
                    """
                )

                extra = get_extended_info(data["name"])

                if extra:
                    st.info(extra)

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
            st.success(t["no_allergens"])

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
                nutrition_notes.append(t["high_sugar"])
                break

        for word in salt_patterns:

            if word in lower_text:
                nutrition_notes.append(t["salt"])
                break

        if nutrition_notes:

            for note in nutrition_notes:
                st.warning(note)

        else:
            st.success(t["nutrition_ok"])

        # =====================================================
        # OCR BOXES
        # =====================================================

        st.subheader(f"📦 {t['ocr_detection']}")

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
# SIDEBAR
# =========================================================

st.sidebar.markdown("---")

if LANG == "bg":

    st.sidebar.info(
        """
        🧠 AI Скенер за Съставки

        Функции:
        - OCR разпознаване
        - Засичане на вредни съставки
        - Оценка на риска
        - Алергени
        - Камера
        - BG / EN / DE / ES
        """
    )

elif LANG == "de":

    st.sidebar.info(
        """
        🧠 KI Zutaten Scanner

        Funktionen:
        - OCR Erkennung
        - Schädliche Inhaltsstoffe
        - Risikoanalyse
        - Allergene
        - Kamera
        - BG / EN / DE / ES
        """
    )

elif LANG == "es":

    st.sidebar.info(
        """
        🧠 Escáner IA

        Funciones:
        - OCR
        - Ingredientes dañinos
        - Riesgo
        - Alérgenos
        - Cámara
        - BG / EN / DE / ES
        """
    )

else:

    st.sidebar.info(
        """
        🧠 AI Ingredient Scanner

        Features:
        - OCR recognition
        - Harmful ingredient detection
        - Health score
        - Allergen detection
        - Camera support
        - BG / EN / DE / ES
        """
    )
```
