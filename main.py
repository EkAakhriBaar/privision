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
API_KEY_MIN_LEN = 16    # treat tokens >= this as potential keys
API_KEY_PADDING = 24    # px padding around detected box

# ---- Setup screen capture ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

# ---- Haar cascade (faces) ----
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# ---- Presidio Analyzer (kept for other sensitive detection) ----
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

# regex to detect label tokens like "api_key", "api key", "api-key"
api_label_re = re.compile(r'(api[_\-\s]?key|[a-z0-9\-_]*secret\b)', re.I)

# --- GUI setup ---
cv2.namedWindow("Screen (API-key Blur)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (API-key Blur)", 960, 540)

faces_cache = []
sensitive_boxes = []  # cache for sensitive text bounding boxes
api_blur_boxes = []   # cache for api-key-related blur boxes
frame_idx = 0
t_prev = time.time()
fps = 0.0

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # ---- Check active window for sensitive files (keep existing behavior) ----
    blur_entire_screen = False
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            title = active_window.title.lower()
            # check keywords for sensitive files - keep this list if you were using earlier
            if any(k in title for k in [".env", "secrets", "config", "apikey", ".pem", ".key"]):
                blur_entire_screen = True
    except Exception:
        pass

    if blur_entire_screen:
        # full-screen blur when a sensitive file is open
        frame = cv2.GaussianBlur(frame, (101, 101), 45)
        # show and skip further detection
    else:
        # ---- face detection (periodic) ----
        if frame_idx % FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=SCALE, fy=SCALE)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = face_cascade.detectMultiScale(gray_small, 1.1, 5, minSize=(24, 24))
            faces_cache = [(int(x/SCALE), int(y/SCALE), int(w/SCALE), int(h/SCALE)) for (x, y, w, h) in det]

        # ---- blur faces ----
        for (x, y, w, h) in faces_cache:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)

        # ---- OCR + sensitive detection (periodic) ----
        if frame_idx % OCR_EVERY == 0:
            api_blur_boxes.clear()
            sensitive_boxes.clear()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # run tesseract word-level
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n = len(data["text"])

            # build a list of OCR words with their boxes to allow looking ahead
            words = []
            for i in range(n):
                wtext = data["text"][i].strip()
                if not wtext:
                    words.append(("", None))
                    continue
                bbox = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                words.append((wtext, bbox))

            # scan OCR words for api label or clipboard token or other sensitive types via Presidio
            for i, (wtext, bbox) in enumerate(words):
                if not wtext or bbox is None:
                    continue

                # 1) If the word is an API label like "api_key"
                if api_label_re.search(wtext):
                    # look at next 1-2 words for actual key token
                    candidate_boxes = [bbox]  # include label box
                    key_found = False
                    for j in (i+1, i+2):
                        if j < len(words):
                            nxt_text, nxt_bbox = words[j]
                            if nxt_text and nxt_bbox:
                                # if the next token looks like a key, include it
                                if looks_like_key(nxt_text):
                                    candidate_boxes.append(nxt_bbox)
                                    key_found = True
                                    break
                                # also include if next token is punctuation followed by token
                                # include as candidate even if not key-looking (cover edge cases)
                                candidate_boxes.append(nxt_bbox)
                    # union the candidate boxes and add padding
                    if candidate_boxes:
                        xs = [b[0] for b in candidate_boxes]
                        ys = [b[1] for b in candidate_boxes]
                        ws = [b[2] for b in candidate_boxes]
                        hs = [b[3] for b in candidate_boxes]
                        x_min = min(xs)
                        y_min = min(ys)
                        x_max = max([xs[k] + ws[k] for k in range(len(ws))])
                        y_max = max([ys[k] + hs[k] for k in range(len(hs))])
                        # pad
                        x_min = max(0, x_min - API_KEY_PADDING)
                        y_min = max(0, y_min - API_KEY_PADDING)
                        x_max = min(frame.shape[1], x_max + API_KEY_PADDING)
                        y_max = min(frame.shape[0], y_max + API_KEY_PADDING)
                        api_blur_boxes.append((x_min, y_min, x_max - x_min, y_max - y_min))

                # 3) continue standard Presidio detection for other sensitive types and keep boxes
                # (e.g., email, phones, etc.) - optional, kept minimal here for performance
                # you can uncomment the following if you want to also collect other sensitive boxes:
                results = analyzer.analyze(text=wtext, language="en")
                results = [r for r in results if r.entity_type in SENSITIVE_TYPES]
                if results:
                    x, y, w, h = bbox
                    sensitive_boxes.append((x, y, w, h))

            # deduplicate and merge overlapping api_blur_boxes
            merged = []
            for box in api_blur_boxes:
                x, y, w, h = box
                merged_flag = False
                for idx, mb in enumerate(merged):
                    mx, my, mw, mh = mb
                    # overlap check
                    if not (x + w < mx or mx + mw < x or y + h < my or my + mh < y):
                        # merge
                        nx = min(x, mx); ny = min(y, my)
                        nx2 = max(x + w, mx + mw); ny2 = max(y + h, my + mh)
                        merged[idx] = (nx, ny, nx2 - nx, ny2 - ny)
                        merged_flag = True
                        break
                if not merged_flag:
                    merged.append(box)
            api_blur_boxes = merged

        # ---- Reapply blur for all cached sensitive boxes (other sensitive_boxes kept for older logic) ----
        for (x, y, w, h) in sensitive_boxes + api_blur_boxes:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)
                # optional: draw rectangle briefly for debug (comment out in production)
                # cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)

    # ---- FPS overlay ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    # ---- Show frame ----
    cv2.imshow("Screen (API-key Blur)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
