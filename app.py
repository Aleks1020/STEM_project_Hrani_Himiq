
import streamlit as st
import numpy as np
from PIL import Image
import pandas as pd
import cv2
import re
from datetime import datetime
import pytesseract
import warnings

warnings.filterwarnings("ignore")

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Food Scanner",
    page_icon="🥗",
    layout="centered"
)

if "history" not in st.session_state:
    st.session_state.history = []

# =========================================================
# LANGUAGE
# =========================================================

LANGUAGES = {"BG": "bg", "EN": "en"}
lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
LANG = LANGUAGES[lang]

t = {
    "bg": {
        "title": "🥗 AI Скенер",
        "upload": "Качи снимка",
        "camera": "Камера",
        "scan": "Сканирай",
        "text": "Текст",
        "score": "Оценка",
        "risk": "Риск",
        "harmful": "Вредни съставки",
        "safe": "Без опасни съставки"
    },
    "en": {
        "title": "🥗 AI Scanner",
        "upload": "Upload image",
        "camera": "Camera",
        "scan": "Scan",
        "text": "Text",
        "score": "Score",
        "risk": "Risk",
        "harmful": "Harmful ingredients",
        "safe": "No harmful ingredients"
    }
}[LANG]

# =========================================================
# OCR ENHANCED PREPROCESSING
# =========================================================

def preprocess(image):

    img = np.array(image)

    # resize (VERY IMPORTANT for cloud stability)
    h, w = img.shape[:2]
    if w > 1200:
        scale = 1200 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # denoise
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)

    # adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh

# =========================================================
# OCR
# =========================================================

def extract_text(image):

    try:
        processed = preprocess(image)

        config = r'--oem 3 --psm 6'

        text = pytesseract.image_to_string(
            processed,
            lang="eng",
            config=config
        )

        # cleanup OCR noise
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    except Exception as e:
        st.error(f"OCR error: {e}")
        return ""

# =========================================================
# SIMPLE INGREDIENT CHECK
# =========================================================

harmful = {
    "e621": -15,
    "e250": -25,
    "aspartame": -20,
    "msg": -10,
    "trans": -25
}

def analyze(text):

    text = text.lower().replace(" ", "")

    found = []
    score = 100

    for k, v in harmful.items():
        if k in text:
            found.append(k)
            score += v

    return found, max(0, min(100, score))

# =========================================================
# UI
# =========================================================

st.title(t["title"])

file = st.file_uploader(t["upload"], type=["png", "jpg", "jpeg"])
cam = st.camera_input(t["camera"])

img = None

if file:
    img = Image.open(file).convert("RGB")
elif cam:
    img = Image.open(cam).convert("RGB")

# =========================================================
# MAIN
# =========================================================

if img:

    st.image(img, use_container_width=True)

    if st.button(t["scan"], type="primary"):

        with st.spinner("Processing..."):

            text = extract_text(img)
            found, score = analyze(text)

        # TEXT
        st.subheader(t["text"])
        st.text_area("", text, height=150)

        # SCORE
        st.subheader(t["score"])
        st.progress(score / 100)

        # HARMFUL
        st.subheader(t["harmful"])

        if found:
            st.error(", ".join(found))
        else:
            st.success(t["safe"])

        # HISTORY
        st.session_state.history.append({
            "time": datetime.now(),
            "score": score
        })

        st.dataframe(pd.DataFrame(st.session_state.history))
