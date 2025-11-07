import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import pygetwindow as gw
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ---- Config ----
MONITOR_INDEX = 1
BLUR_KSIZE = (51, 51)
BLUR_SIGMA = 30
FACE_DETECT_EVERY = 2
OCR_EVERY = 2
SCALE = 0.5

# Sensitive file keywords
SENSITIVE_FILES = [".env", "secrets", "config", "apikey", ".pem", ".key"]

# ---- Setup screen capture ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

# ---- Haar cascade ----
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# ---- Presidio Analyzer ----
config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
}

provider = NlpEngineProvider(nlp_configuration=config)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

SENSITIVE_TYPES = {
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "US_SSN",
    "IBAN_CODE",
    "LOCATION",
    "GPE",
    "FAC",
}
date_like = re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b")

# ---- GUI ----
cv2.namedWindow("Screen (Sensitive text)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (Sensitive text)", 960, 540)

faces_cache = []
sensitive_boxes = []  # cache for sensitive text bounding boxes
frame_idx = 0
t_prev = time.time()
fps = 0.0

print("\n🔍 Detecting and blurring sensitive text every", OCR_EVERY, "frames\n")

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # ---- Check active window for sensitive files ----
    blur_entire_screen = False
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            title = active_window.title.lower()
            if any(keyword in title for keyword in SENSITIVE_FILES):
                blur_entire_screen = True
    except Exception:
        pass

    # ---- If sensitive file detected, blur whole screen and skip detection ----
    if blur_entire_screen:
        frame = cv2.GaussianBlur(frame, (101, 101), 45)
    else:
        # ---- Face detection ----
        if frame_idx % FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=SCALE, fy=SCALE)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = face_cascade.detectMultiScale(gray_small, 1.1, 5, minSize=(24, 24))
            faces_cache = [(int(x/SCALE), int(y/SCALE), int(w/SCALE), int(h/SCALE)) for (x, y, w, h) in det]

        # ---- Blur faces ----
        for (x, y, w, h) in faces_cache:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)

        # ---- OCR + Sensitive text detection ----
        if frame_idx % OCR_EVERY == 0:
            sensitive_boxes.clear()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n = len(data["text"])

            for i in range(n):
                text = data["text"][i].strip()
                if not text:
                    continue

                results = analyzer.analyze(text=text, language="en")
                results = [r for r in results if r.entity_type in SENSITIVE_TYPES]

                if any(r.entity_type == "PHONE_NUMBER" for r in results):
                    if date_like.match(text):
                        results = [r for r in results if r.entity_type != "PHONE_NUMBER"]

                if results:
                    x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                    sensitive_boxes.append((x, y, w, h))
                    ent_types = ", ".join(r.entity_type for r in results)
                    print(f"Text: '{text}' | Type: {ent_types} | Box: ({x},{y},{w},{h})")

            print("--------------------------------------------------")

        # ---- Reapply blur for all cached sensitive boxes ----
        for (x, y, w, h) in sensitive_boxes:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)

    # ---- FPS overlay ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    # ---- Show frame ----
    cv2.imshow("Screen (Sensitive text)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
