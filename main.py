import cv2
import numpy as np
import mss
import pytesseract
import time
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine

# optional tesseract path on Windows
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---- Config ----
MONITOR_INDEX = 1
BLUR_KSIZE = (51, 51)
BLUR_SIGMA = 30
FACE_DETECT_EVERY = 2
OCR_EVERY = 10
SCALE = 0.5

# ---- Setup screen capture ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

# ---- Haar cascade ----
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# ---- Presidio Analyzer ----
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
}

nlp_engine = SpacyNlpEngine(ner_model_configuration=configuration)
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

cv2.namedWindow("Screen (Sensitive text)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (Sensitive text)", 960, 540)

faces_cache = []
frame_idx = 0
t_prev = time.time()
fps = 0.0

print("\n🔍  Detecting sensitive text every", OCR_EVERY, "frames\n")

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

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

    # ---- OCR + Sensitive detection ----
    if frame_idx % OCR_EVERY == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

        n = len(data["text"])
        print(f"\n----- Frame {frame_idx} | Sensitive findings -----")
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue

            # Ask Presidio if this text looks sensitive
            results = analyzer.analyze(text=text, language="en")

            if results:   # something flagged as PII
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                ent_types = ", ".join(r.entity_type for r in results)
                print(f"Text: '{text}' | Type: {ent_types} | Box: ({x},{y},{w},{h})")
                # highlight in red
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        print("--------------------------------------------------")

    # ---- FPS overlay ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    cv2.imshow("Screen (Sensitive text)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
