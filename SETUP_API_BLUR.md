# API Key Blur Detection Setup Guide

## Prerequisites Installed ✅
- opencv-python
- numpy
- mss
- pytesseract
- pygetwindow
- presidio-analyzer
- spacy
- screeninfo

## Additional Steps Required

### 1. Install Tesseract OCR

**Download from:** https://github.com/UB-Mannheim/tesseract/wiki

**Or use this direct link:**
```
https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0/tesseract-ocr-w64-setup-v5.3.0.exe
```

**Installation Steps:**
1. Download and run the installer
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. Add to PATH (add this line to the script or set environment variable):
   ```python
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### 2. Download Spacy Language Model

Run this command in PowerShell:
```powershell
python -m spacy download en_core_web_lg
```

This will download the large English model (~560 MB).

### 3. Run the Script

Once everything is installed:

```powershell
cd D:\Desktop\screenshare
python main.py
```

Press **ESC** to exit the application.

## Features
- ✅ Detects and blurs API keys
- ✅ Detects and blurs sensitive information (emails, phone numbers, SSN, etc.)
- ✅ Face detection and blurring
- ✅ Detects sensitive window titles (.env, secrets, config, etc.) and blurs entire screen
- ✅ Shows real-time FPS counter
- ✅ OCR-based detection using pytesseract

## Troubleshooting

### "Tesseract not found" error
Add this to the top of main.py after imports:
```python
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### "en_core_web_lg not found" error
Run: `python -m spacy download en_core_web_lg`

### Script runs but shows blank window
- Make sure your screen resolution is detected correctly
- Check MONITOR_INDEX (usually 1 for primary monitor)
