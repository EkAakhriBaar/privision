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

# ---- Config ----
MONITOR_INDEX = 1
BLUR_KSIZE = (35, 35)  # Blur kernel size
BLUR_SIGMA = 25        # Blur intensity
FACE_DETECT_EVERY = 4  # Detect faces every 4 frames
OCR_EVERY = 1          # OCR every frame (in background thread)
SCALE = 0.25           # Downscaling for face detection

# Padding around detected credentials
API_KEY_PADDING = int(0.5 * PX_PER_CM)

# ---- Setup ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ==================== STRICT CREDENTIAL DETECTION PATTERNS ====================
# These patterns match ONLY confidential data - NO filenames, NO console
CONFIDENTIAL_PATTERNS = [
    # API Keys and Secrets (with or without assignment)
    (r'sk_live_[A-Za-z0-9_]{20,}', 'API_KEY_STRIPE'),
    (r'sk_test_[A-Za-z0-9_]{20,}', 'API_KEY_STRIPE_TEST'),
    (r'api[_\-\s]?key\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{12,})[\'"]?', 'API_KEY'),
    (r'client[_\-]?id\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{12,})[\'"]?', 'CLIENT_ID'),
    (r'client[_\-]?secret\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{12,})[\'"]?', 'CLIENT_SECRET'),
    (r'access[_\-]?token\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{20,})[\'"]?', 'ACCESS_TOKEN'),
    (r'refresh[_\-]?token\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{20,})[\'"]?', 'REFRESH_TOKEN'),
    (r'secret\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{16,})[\'"]?', 'SECRET'),
    (r'password\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.@!#$%^&*]{8,})[\'"]?', 'PASSWORD'),
    (r'db[_\-]?password\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.@!#$%^&*]{8,})[\'"]?', 'DB_PASSWORD'),
    (r'jwt[_\-]?secret\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{16,})[\'"]?', 'JWT_SECRET'),
    (r'eyJ[A-Za-z0-9_\-\.]+', 'JWT_TOKEN'),  # JWT tokens (base64 starting with ey)
    
    # Phone numbers (more flexible matching)
    (r'\+91[\s\-]?[6-9][\d\s\-]{9,}', 'PHONE_INDIA'),
    (r'\+[0-9]{1,3}[\s\-]?[0-9]{6,14}', 'PHONE_INTL'),
    (r'\b[0-9]{3}[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{4}\b', 'PHONE_US'),
    
    # Credit/Debit Card Numbers (with and without spaces)
    (r'\b[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b', 'CARD_NUMBER'),
    (r'\b[0-9]{16}\b', 'CARD_16_DIGIT'),
    (r'\b[0-9]{15}\b', 'CARD_AMEX'),
    (r'\b[0-9]{13,19}\b(?=.*[0-9]{4})', 'CARD_GENERIC'),
    
    # Email addresses (including internal/local domains)
    (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', 'EMAIL'),
    (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(internal|local|company|corp)\b', 'EMAIL_INTERNAL'),
    
    # IP Addresses (private and public)
    (r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
     r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', 'IP_ADDRESS'),
    
    # SSN format (XXX-XX-XXXX and variations)
    (r'\b[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{4}\b', 'SSN'),
]

# Compile patterns
COMPILED_PATTERNS = [(re.compile(pattern, re.IGNORECASE), name) for pattern, name in CONFIDENTIAL_PATTERNS]

# Filenames to IGNORE (don't blur these)
IGNORE_PATTERNS = re.compile(
    r'\.(txt|pdf|docx|xlsx|jpg|png|exe|py|java|js|html|css|json|xml|log|csv|sql|db|sh|bat|'
    r'mp4|avi|mkv|mov|zip|rar|7z|tar|gz|dll|so|o|app|dmg)$|'
    r'(C:\\|D:\\|E:\\|F:\\|G:\\|H:\\|:\\\\|/|file|folder|directory|downloads|documents|desktop|'
    r'\.git|\.env|\.json|\.xml|\.log|\.txt|__pycache__|node_modules|/home/user|/usr/)',
    re.IGNORECASE
)

# ---- GUI ----
cv2.namedWindow("Screen (API-key Blur)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (API-key Blur)", 960, 540)

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
            with ocr_lock:
                ocr_frame_gray = gray.copy()
        
        # Get results from OCR thread (non-blocking)
        with ocr_lock:
            api_blur_boxes = ocr_api_blur_boxes.copy() if ocr_api_blur_boxes else []
            creds = found_credentials.copy() if found_credentials else []
        
        # ---- blur boxes ----
        for (x, y, w, h) in api_blur_boxes:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x+w), min(frame.shape[0], y+h)
            if x2 > x1 and y2 > y1:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)
    
    # Print status
    if frame_idx % 30 == 0:
        elapsed = time.time() - starttime
        with ocr_lock:
            num_boxes = len(ocr_api_blur_boxes)
        print(f"Frame {frame_idx:5d} | {elapsed*1000:6.2f}ms | Blur regions: {num_boxes}")

    # ---- FPS ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)
    
    # Show blur status
    with ocr_lock:
        if ocr_api_blur_boxes:
            cv2.putText(frame, f"Blurring: {len(ocr_api_blur_boxes)} regions", (12, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Screen (API-key Blur)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

print("\n[+] Exiting...")
cv2.destroyAllWindows()


# Start OCR worker thread
ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
ocr_thread.start()

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    starttime = time.time()

    # ---- check sensitive window ----
    blur_entire = False
    if frame_idx % 5 == 0:  # Only check window title every 5 frames
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
        
        # Apply cached face blurs (vectorized)
        for (x, y, w, h) in faces_cache:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x+w), min(frame.shape[0], y+h)
            if x2 > x1 and y2 > y1:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)

        # ---- OCR detection (async via thread) ----
        if frame_idx % OCR_EVERY == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            with ocr_lock:
                ocr_frame_gray = gray.copy()
        
        # Get results from OCR thread (non-blocking)
        with ocr_lock:
            api_blur_boxes = ocr_api_blur_boxes.copy() if ocr_api_blur_boxes else []
            creds = found_credentials.copy() if found_credentials else []
        
        # ---- blur boxes ----
        for (x, y, w, h) in api_blur_boxes:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x+w), min(frame.shape[0], y+h)
            if x2 > x1 and y2 > y1:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)
    
    # Print status
    if frame_idx % 30 == 0:
        elapsed = time.time() - starttime
        with ocr_lock:
            num_boxes = len(ocr_api_blur_boxes)
        print(f"Frame {frame_idx:5d} | {elapsed*1000:6.2f}ms | Blur regions: {num_boxes}")

    # ---- FPS ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)
    
    # Show blur status
    with ocr_lock:
        if ocr_api_blur_boxes:
            cv2.putText(frame, f"Blurring: {len(ocr_api_blur_boxes)} regions", (12, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Screen (API-key Blur)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

print("\n[+] Exiting...")
cv2.destroyAllWindows()