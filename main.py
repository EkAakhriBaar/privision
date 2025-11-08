import cv2
import numpy as np
import mss
import pytesseract
import time
import re
import platform
import subprocess
import threading
import pygetwindow as gw
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from screeninfo import get_monitors
import sounddevice as sd

# ==== STREAM CONFIG ====
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2/"
STREAM_KEY = "c1es-08v4-k611-zbpp-6zye"
FPS = 30

# ==== DPI and Scaling ====
width_mm = get_monitors()[0].width_mm
width_px = get_monitors()[0].width
DPI = width_px / (width_mm / 25.4)
PX_PER_CM = DPI / 2.54

# ==== Monitor ====
MONITOR_INDEX = 1
sct = mss.mss()
monitor = sct.monitors[MONITOR_INDEX]
width, height = monitor["width"], monitor["height"]

# ==== Blur & Detection Config ====
BLUR_KSIZE = (25, 25)
BLUR_SIGMA = 15
FACE_DETECT_EVERY = 4
OCR_EVERY = 1
SCALE = 0.5
API_KEY_PADDING = int(0.5 * PX_PER_CM)

# ==== Face Cascade ====
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Could not load Haar cascade")

# ==== Presidio Setup ====
config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]}
provider = NlpEngineProvider(nlp_configuration=config)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
SENSITIVE_TYPES = {"EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS", "US_SSN", "IBAN_CODE", "LOCATION"}

api_label_re = re.compile(r'\b(api[_\-\s]?key|[A-Za-z0-9\-_]*secret)\b', re.I)

# ==== OCR Thread ====
ocr_lock = threading.Lock()
ocr_frame_gray = None
ocr_sensitive_boxes = []
ocr_api_blur_boxes = []


def ocr_worker():
    global ocr_frame_gray, ocr_sensitive_boxes, ocr_api_blur_boxes
    while True:
        if ocr_frame_gray is not None:
            try:
                gray = ocr_frame_gray
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config="--psm 6")
                n = len(data["text"])
                temp_sensitive, temp_api_blur = [], []
                blurred_words = set()
                words_list = []

                for i in range(n):
                    text = data["text"][i].strip()
                    if text and len(text) > 1:
                        box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                        words_list.append((text, box, i))

                # === PASS 1: API key blur ===
                for i, (text, box, idx) in enumerate(words_list):
                    if idx in blurred_words:
                        continue
                    if api_label_re.search(text):
                        lx, ly, lw, lh = box
                        for j in range(idx + 1, min(idx + 6, len(words_list))):
                            next_text, next_box, next_idx = words_list[j]
                            if len(next_text) >= 6:
                                cx, cy, cw, ch = next_box
                                x1 = max(0, min(lx, cx) - API_KEY_PADDING * 3)
                                y1 = max(0, min(ly, cy) - API_KEY_PADDING * 2)
                                x2 = min(gray.shape[1], max(lx + lw, cx + cw) + API_KEY_PADDING * 3)
                                y2 = min(gray.shape[0], max(ly + lh, cy + ch) + API_KEY_PADDING * 2)
                                temp_api_blur.append((x1, y1, x2 - x1, y2 - y1))
                                blurred_words.add(idx)
                                blurred_words.add(next_idx)
                                break

                # === PASS 2: Presidio sensitive data ===
                for text, box, idx in words_list:
                    if idx in blurred_words or len(text) < 3:
                        continue
                    results = analyzer.analyze(text=text, language="en")
                    for r in results:
                        if r.entity_type in SENSITIVE_TYPES:
                            lx, ly, lw, lh = box
                            x1 = max(0, lx - API_KEY_PADDING)
                            y1 = max(0, ly - API_KEY_PADDING)
                            x2 = min(gray.shape[1], lx + lw + API_KEY_PADDING)
                            y2 = min(gray.shape[0], ly + lh + API_KEY_PADDING)
                            temp_sensitive.append((x1, y1, x2 - x1, y2 - y1))
                            break

                with ocr_lock:
                    ocr_sensitive_boxes = temp_sensitive
                    ocr_api_blur_boxes = temp_api_blur
                    ocr_frame_gray = None
            except Exception:
                with ocr_lock:
                    ocr_frame_gray = None


ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
ocr_thread.start()

# ==== FFmpeg Setup ====
system = platform.system().lower()
use_anullsrc = False
mic_name = None

try:
    devices = sd.query_devices()
    default_input = sd.default.device[0]
    if default_input is not None and default_input >= 0:
        mic_name = devices[default_input]["name"]
except Exception:
    use_anullsrc = True

ffmpeg_cmd = [
    "ffmpeg",
    "-loglevel", "warning",
    "-y",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{width}x{height}",
    "-r", str(FPS),
    "-i", "-",
]

# if not use_anullsrc:
#     if "windows" in system:
#         # Try to get the real DirectShow device name
#         dshow_out = subprocess.run(
#             ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
#             capture_output=True, text=True
#         )
#         audio_device = None
#         for line in dshow_out.stderr.splitlines():
#             if "Microphone" in line and '"' in line:
#                 audio_device = line.split('"')[1]
#                 break

#         if audio_device:
#             ffmpeg_cmd += ["-f", "dshow", "-i", f'audio={audio_device}']
#         else:
#             print("⚠️ No microphone found. Using silent audio.")
#             use_anullsrc = True
#     elif "linux" in system:
#         ffmpeg_cmd += ["-f", "pulse", "-i", "default"]
#     elif "darwin" in system:
#         ffmpeg_cmd += ["-f", "avfoundation", "-i", ":0"]
# else:
ffmpeg_cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

ffmpeg_cmd += [
    "-vf", "scale=1280:720",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-b:v", "4500k",
    "-g", str(FPS * 2),
    "-c:a", "aac",
    "-ar", "44100",
    "-b:a", "128k",
    "-f", "flv",
    f"{RTMP_URL}{STREAM_KEY}",
]

print("🎬 Starting FFmpeg...")
process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

# ==== Main Loop ====
cv2.namedWindow("Screen (Live Stream)", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Screen (Live Stream)", 960, 540)

frame_idx, t_prev, fps_calc = 0, time.time(), 0.0
faces_cache = []

while True:
    frame_idx += 1
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

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
        if frame_idx % FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=SCALE, fy=SCALE)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = face_cascade.detectMultiScale(gray_small, 1.3, 3, minSize=(15, 15))
            faces_cache = [(int(x/SCALE), int(y/SCALE), int(w/SCALE), int(h/SCALE)) for (x, y, w, h) in det]

        for (x, y, w, h) in faces_cache:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)

        if frame_idx % OCR_EVERY == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            with ocr_lock:
                ocr_frame_gray = gray.copy()

        with ocr_lock:
            sensitive_boxes = ocr_sensitive_boxes.copy()
            api_blur_boxes = ocr_api_blur_boxes.copy()

        for (x, y, w, h) in api_blur_boxes + sensitive_boxes:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(frame[y1:y2, x1:x2], BLUR_KSIZE, BLUR_SIGMA)

    process.stdin.write(frame.tobytes())

    now = time.time()
    fps_calc = 0.9 * fps_calc + 0.1 * (1.0 / (now - t_prev))
    t_prev = now
    cv2.putText(frame, f"FPS: {fps_calc:0.1f}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 220, 20), 2)

    cv2.imshow("Screen (Live Stream)", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
process.stdin.close()
process.wait()
