import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import pygetwindow as gw
from screeninfo import get_monitors
import threading

# ---- DPI and pixel scaling ----
width_mm = get_monitors()[0].width_mm
width_px = get_monitors()[0].width
DPI = width_px / (width_mm / 25.4)
PX_PER_CM = DPI / 2.54

MIN_PRESIDIO_SCORE = 0.7

# ---- Config ----
MONITOR_INDEX = 1
BLUR_KSIZE = (51, 51)
BLUR_SIGMA = 30
FACE_DETECT_EVERY = 1
OCR_EVERY = 1
SCALE = 0.5
API_KEY_MIN_LEN = 16

# real-world tuned thresholds
MAX_HORIZONTAL_GAP = int(7 * PX_PER_CM)  # ~7 cm to right
MAX_VERTICAL_GAP = int(2 * PX_PER_CM)    # ~2 cm below
API_KEY_PADDING = int(0.4 * PX_PER_CM)   # ~0.4 cm blur margin

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
    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", "LOCATION", "US_SSN", "IBAN_CODE", "GPE", "FAC" 
}

# patterns
api_label_re = re.compile(r'\b(api[_\-\s]?key|[A-Za-z0-9\-_]*secret)\b', re.I)
key_candidate_re = re.compile(r'^[A-Za-z0-9_\-]{16,}$')

# ---- GUI ----
cv2.namedWindow("Screen", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen", 960, 540)

faces_cache = []
frame_idx, t_prev, fps = 0, time.time(), 0.0

# OCR threading
ocr_lock = threading.Lock()
ocr_frame_gray = None
ocr_api_blur_boxes = []
found_credentials = []

def ocr_worker():
    """Background thread for OCR processing - STRICT confidential data detection ONLY"""
    global ocr_frame_gray, ocr_api_blur_boxes, found_credentials
    
    frame_count = 0
    while True:
        if ocr_frame_gray is not None:
            frame_count += 1
            try:
                gray = ocr_frame_gray
                
                # Fast OCR
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config='--psm 6')
                n = len(data["text"])
                
                temp_api_blur = []
                blurred_regions = set()
                frame_credentials = []
                
                # Extract all text segments with positions
                segments = []
                for i in range(n):
                    text = data["text"][i].strip()
                    if text and len(text) > 2:
                        box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                        segments.append((text, box, i))
                
                # ===== STRICT PATTERN MATCHING =====
                # Check entire text content for confidential patterns
                full_text = ' '.join([seg[0] for seg in segments])
                
                # Check each compiled pattern against full text
                for pattern, pattern_name in COMPILED_PATTERNS:
                    matches = pattern.finditer(full_text)
                    for match in matches:
                        matched_text = match.group(0)
                        
                        # Skip if it looks like a filename or path
                        if IGNORE_PATTERNS.search(matched_text):
                            continue
                        
                        frame_credentials.append(pattern_name)
                        
                        # Find which segments contain this match
                        match_pos = match.start()
                        char_count = 0
                        
                        for text, box, idx in segments:
                            segment_len = len(text) + 1  # +1 for space
                            if char_count <= match_pos < char_count + segment_len:
                                lx, ly, lw, lh = box
                                x1 = max(0, lx - API_KEY_PADDING * 2)
                                y1 = max(0, ly - API_KEY_PADDING)
                                x2 = min(gray.shape[1], lx + lw + API_KEY_PADDING * 2)
                                y2 = min(gray.shape[0], ly + lh + API_KEY_PADDING)
                                
                                # Avoid duplicate blurs
                                region_key = (x1, y1, x2, y2)
                                if region_key not in blurred_regions:
                                    temp_api_blur.append((x1, y1, x2 - x1, y2 - y1))
                                    blurred_regions.add(region_key)
                            
                            char_count += segment_len
                
                # ===== LINE-BY-LINE CONTEXTUAL MATCHING =====
                # For patterns like: API_KEY = value, PASSWORD = value, etc.
                for i, (text, box, idx) in enumerate(segments):
                    # Check if this text contains a confidential label
                    if re.search(r'(api_key|client_id|client_secret|password|db_password|secret|token|access_token|refresh_token|jwt_secret|key|credentials|auth|bearer)\s*[=:]', text, re.I):
                        frame_credentials.append('CONTEXTUAL')
                        lx, ly, lw, lh = box
                        
                        # Blur this text segment
                        x1 = max(0, lx - API_KEY_PADDING * 2)
                        y1 = max(0, ly - API_KEY_PADDING)
                        x2 = min(gray.shape[1], lx + lw + API_KEY_PADDING * 2)
                        y2 = min(gray.shape[0], ly + lh + API_KEY_PADDING)
                        region_key = (x1, y1, x2, y2)
                        if region_key not in blurred_regions:
                            temp_api_blur.append((x1, y1, x2 - x1, y2 - y1))
                            blurred_regions.add(region_key)
                        
                        # Also blur next few segments (they likely contain the value)
                        for j in range(i + 1, min(i + 8, len(segments))):
                            next_text, next_box, next_idx = segments[j]
                            if next_text in ['=', ':', '-', '_', '+', ',', '||', '&&']:
                                continue
                            
                            nx1, ny1, nw, nh = next_box
                            nx1 = max(0, nx1 - API_KEY_PADDING)
                            ny1 = max(0, ny1 - API_KEY_PADDING)
                            nx2 = min(gray.shape[1], nx1 + nw + API_KEY_PADDING)
                            ny2 = min(gray.shape[0], ny1 + nh + API_KEY_PADDING)
                            region_key = (nx1, ny1, nx2, ny2)
                            if region_key not in blurred_regions:
                                temp_api_blur.append((nx1, ny1, nx2 - nx1, ny2 - ny1))
                                blurred_regions.add(region_key)
                            break
                
                if frame_count % 30 == 0 and frame_credentials:
                    print(f"[OCR] Found credentials: {set(frame_credentials)} | Regions: {len(temp_api_blur)}")
                
                with ocr_lock:
                    ocr_api_blur_boxes = temp_api_blur
                    found_credentials = frame_credentials
                    ocr_frame_gray = None
                    
            except Exception as e:
                print(f"[OCR Error] {str(e)}")
                with ocr_lock:
                    ocr_frame_gray = None
        
        time.sleep(0.003)

# Start OCR worker thread
print("[*] Starting OCR worker thread...")
ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
ocr_thread.start()
print("[+] OCR worker started. Press ESC to stop.\n")

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    starttime = time.time()

    # ---- check sensitive window ----
    blur_entire = False
    if frame_idx % 5 == 0:
        try:
            win = gw.getActiveWindow()
            if win and any(k in win.title.lower() for k in [".env", "secrets", "config", "apikey", ".pem", ".key"]):
                blur_entire = True
        except Exception:
            pass

    if blur_entire:
        frame = cv2.GaussianBlur(frame, (51, 51), 25)
    else:
        # ---- faces ----
        if frame_idx % FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_NEAREST)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = face_cascade.detectMultiScale(gray_small, 1.3, 3, minSize=(15, 15))
            faces_cache = [(int(x/SCALE), int(y/SCALE), int(w/SCALE), int(h/SCALE)) for (x, y, w, h) in det]
        
        # Apply cached face blurs
        for (x, y, w, h) in faces_cache:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x+w), min(frame.shape[0], y+h)
            if x2 > x1 and y2 > y1:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)

        # ---- OCR detection (async via thread) ----
        if frame_idx % OCR_EVERY == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n = len(data["text"])
            words = [(data["text"][i].strip(),
                      (data["left"][i], data["top"][i], data["width"][i], data["height"][i]))
                     for i in range(n) if data["text"][i].strip()]
            for i, (label, lb) in enumerate(words):
                results = analyzer.analyze(text=label, language="en")
                for r in results:
                    if r.entity_type in SENSITIVE_TYPES and r.score >= MIN_PRESIDIO_SCORE:
                        sensitive_boxes.append(lb)
                        break
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
                        
    
        # ---- blur boxes ----
        for (x, y, w, h) in api_blur_boxes + sensitive_boxes:
            roi = frame[y:y+h, x:x+w]
            if roi.size:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, BLUR_KSIZE, BLUR_SIGMA)
                # debug
                # cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)
    # print(f"total time:,{time.time()-starttime} for frame {frame_idx}")

    # ---- FPS ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    cv2.imshow("Screen", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

print("\n[+] Exiting...")
cv2.destroyAllWindows()