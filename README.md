
# 🛡️ Privision — Real-Time Privacy Protection for Streamers

**Protect your privacy before it’s too late.**
**Privision** is a smart desktop application that automatically detects and blurs sensitive information — whether it’s text, faces, or on-screen credentials — **in real-time** during streaming or video recording.  
Stream safely, share confidently.

## 🚨 Problem

Streamers and creators often **accidentally expose private information** during live sessions — things like:

- Personal contact details  
- API keys or credentials  
- Payment info or banking data  
- Faces of family or bystanders  

While platforms like YouTube offer **face blurring**, they don’t protect **text-based or other forms of sensitive data** — leaving creators vulnerable to serious privacy breaches.

---

## 💡 Solution — *Privision*

**Privision** continuously monitors your screen, intelligently detects private information using **OCR + NER + Computer Vision**, and applies **real-time blurring** *before* the content reaches your viewers.

It’s your **privacy shield**, built for live creators, coders, educators, and professionals who value safety.

---

## ✨ Key Features

### 🔍 Real-Time Privacy Protection
Detects and blurs:
- **Text-based sensitive data** using `pytesseract` + `Presidio Analyzer`
- **Faces** using OpenCV’s Haar Cascade and DNN models
- **API keys**, **emails**, **addresses**, and other personally identifiable information (PII)

🧠 Built with OCR, NER, and face detection — ensuring nothing private ever leaks.

---

### 📡 Seamless Live Streaming
Stream the **processed output** directly to:
- YouTube  
- Twitch  
- Facebook Live  
- or any RTMP-compatible platform  

Using a low-latency **FFmpeg** pipeline optimized for smooth video transmission.

---

### 🎬 Secure Pre-Recorded Video Processing
Not streaming? No problem.  
Privision can also **sanitize your recorded videos** — automatically scanning for and blurring private information before sharing or uploading.

---

### ⚙️ Customizable Settings
Choose your:
- Resolution (`720p`, `1080p`, or custom)
- Frame Rate (`30 FPS`, `60 FPS`)
- Blur strength and region control
- Privacy detection toggles (e.g., only text, only faces, both)

All directly configurable from the sleek **PyQt5-based interface**.

---

### 💡 Lightweight & Creator-Friendly
Optimized for performance — Privision runs smoothly even with multiple layers of detection enabled.

✅ Minimal CPU & GPU overhead  
✅ Runs in the background seamlessly  
✅ Minimal lag between capture and broadcast  

---

## 🧠 Tech Stack

| Category | Technology |
|-----------|-------------|
| **Language** | Python 3.11 |
| **UI Framework** | PyQt5 |
| **Screen Capture** | `mss`, `pygetwindow`, `screeninfo` |
| **Computer Vision** | `OpenCV`, `NumPy` |
| **Text Detection (OCR)** | `pytesseract` |
| **Sensitive Data Detection** | `Presidio Analyzer` (Microsoft’s NLP engine for PII detection) |
| **Streaming Engine** | `FFmpeg` (real-time encoding + RTMP output) |
| **Concurrency** | `threading`, `deque` (for frame buffering) |
| **Performance Optimization** | Dynamic ROI masking, multi-threaded pipeline |

---


