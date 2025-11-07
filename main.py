import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import pygetwindow as gw
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from screeninfo import get_monitors

# ---- DPI and pixel scaling ----
width_mm = get_monitors()[0].width_mm
width_px = get_monitors()[0].width
DPI = width_px / (width_mm / 25.4)
PX_PER_CM = DPI / 2.54

# ---- Config ----
MONITOR_INDEX = 1
BLUR_KSIZE = (51, 51)
BLUR_SIGMA = 30
FACE_DETECT_EVERY = 2
OCR_EVERY = 2
SCALE = 0.5
API_KEY_MIN_LEN = 16

# real-world tuned thresholds
MAX_HORIZONTAL_GAP = int(3 * PX_PER_CM)  # ~3 cm to right
MAX_VERTICAL_GAP = int(2 * PX_PER_CM)    # ~2 cm below
API_KEY_PADDING = int(0.7 * PX_PER_CM)   # ~0.7 cm blur margin

# ---- Setup ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# ---- Presidio ----
config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
}
provider = NlpEngineProvider(nlp_configuration=config)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

SENSITIVE_TYPES = {
    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS",
    "US_SSN", "IBAN_CODE", "LOCATION", "GPE", "FAC"
}

# patterns
api_label_re = re.compile(r'(api[_\-\s]?key|[a-z0-9\-_]*secret\b)', re.I)
key_candidate_re = re.compile(r'^[A-Za-z0-9_\-]{16,}$')

# ---- GUI ----
cv2.namedWindow("Screen (API-key Blur)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (API-key Blur)", 960, 540)

faces_cache, sensitive_boxes, api_blur_boxes = [], [], []
frame_idx, t_prev, fps = 0, time.time(), 0.0

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # ---- check sensitive window ----
    blur_entire = False
    try:
        win = gw.getActiveWindow()
        if win and any(k in win.title.lower() for k in [".env", "secrets", "config", "apikey", ".pem", ".key"]):
            blur_entire = True
    except Exception:
        pass

    if blur_entire:
        frame = cv2.GaussianBlur(frame, (101, 101), 45)
    else:
        # ---- faces ----
        if frame_idx % FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=SCALE, fy=SCALE)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = face_cascade.detectMultiScale(gray_small, 1.1, 5, minSize=(24, 24))
            faces_cache = [(int(x/SCALE), int(y/SCALE), int(w/SCALE), int(h/SCALE)) for (x, y, w, h) in det]
        for (x, y, w, h) in faces_cache:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)

        # ---- OCR detection ----
        if frame_idx % OCR_EVERY == 0:
            api_blur_boxes.clear()
            sensitive_boxes.clear()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n = len(data["text"])
            words = [(data["text"][i].strip(),
                      (data["left"][i], data["top"][i], data["width"][i], data["height"][i]))
                     for i in range(n) if data["text"][i].strip()]

            for i, (label, lb) in enumerate(words):
                if not api_label_re.search(label):
                    continue
                lx, ly, lw, lh = lb
                lcx = lx + lw // 2
                lcy = ly + lh // 2

                for j, (cand, cb) in enumerate(words):
                    if i == j or not key_candidate_re.match(cand):
                        continue
                    cx, cy, cw, ch = cb
                    ccx = cx + cw // 2
                    ccy = cy + ch // 2

                    horiz_gap = cx - (lx + lw)
                    vert_gap = cy - (ly + lh)
                    if (0 < horiz_gap < MAX_HORIZONTAL_GAP and abs(ccy - lcy) < lh) or \
                       (0 < vert_gap < MAX_VERTICAL_GAP and abs(ccx - lcx) < lw):
                        x1 = max(0, min(lx, cx) - API_KEY_PADDING)
                        y1 = max(0, min(ly, cy) - API_KEY_PADDING)
                        x2 = min(frame.shape[1], max(lx+lw, cx+cw) + API_KEY_PADDING)
                        y2 = min(frame.shape[0], max(ly+lh, cy+ch) + API_KEY_PADDING)
                        api_blur_boxes.append((x1, y1, x2-x1, y2-y1))
                        break
                        
                # optional Presidio
                results = analyzer.analyze(text=label, language="en")
                results = [r for r in results if r.entity_type in SENSITIVE_TYPES]
                if results:
                    sensitive_boxes.append(lb)

        # ---- blur boxes ----
        for (x, y, w, h) in api_blur_boxes + sensitive_boxes:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)
                # debug
                # cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)

    # ---- FPS ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    cv2.imshow("Screen (API-key Blur)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
