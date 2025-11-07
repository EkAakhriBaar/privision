import cv2
import numpy as np
import mss
import time
import re
import pygetwindow as gw
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
SCALE = 0.5

# real-world tuned thresholds
MAX_HORIZONTAL_GAP = int(3 * PX_PER_CM)
MAX_VERTICAL_GAP = int(2 * PX_PER_CM)
API_KEY_PADDING = int(0.7 * PX_PER_CM)

# ---- Setup ----
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# patterns for API key detection
api_label_re = re.compile(r'(api[_\-\s]?key|[a-z0-9\-_]*secret\b)', re.I)
key_candidate_re = re.compile(r'^[A-Za-z0-9_\-]{16,}$')

# ---- GUI ----
cv2.namedWindow("Screen - Privacy Blur (No OCR)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen - Privacy Blur (No OCR)", 960, 540)

faces_cache = []
frame_idx, t_prev, fps = 0, time.time(), 0.0

print("=" * 60)
print("Screen Privacy Blur - Simplified Version (Without OCR)")
print("=" * 60)
print("Features:")
print("  ✓ Face detection and blurring")
print("  ✓ Sensitive window detection (.env, secrets, config, etc.)")
print("  ✓ Real-time FPS counter")
print("  ✓ Pattern-based API key detection")
print("\nPress ESC to exit")
print("=" * 60)

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
            cv2.putText(frame, "SENSITIVE WINDOW DETECTED - ENTIRE SCREEN BLURRED", (20, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
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

    # ---- FPS ----
    now = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps:0.1f}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    cv2.imshow("Screen - Privacy Blur (No OCR)", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cv2.destroyAllWindows()
print("\nApplication closed.")
