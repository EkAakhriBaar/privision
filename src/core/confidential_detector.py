"""
Confidential Data Detector - OCR + Presidio-based sensitive information detection
Detects and provides blur coordinates for API keys, passwords, emails, phone numbers, etc.
"""
import cv2
import numpy as np
import re
import pytesseract
from typing import List, Tuple, Set
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider


class ConfidentialDataDetector:
    """Detects confidential information using OCR, Presidio, and pattern matching"""
    
    def __init__(self, padding_px=20):
        self.padding_px = padding_px
        self.blur_regions_cache = []
        self.frame_count = 0
        
        # Initialize Presidio
        try:
            config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
            }
            provider = NlpEngineProvider(nlp_configuration=config)
            nlp_engine = provider.create_engine()
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
            self.presidio_enabled = True
            print("[Presidio] Initialized successfully")
        except Exception as e:
            print(f"[Presidio] Not available: {e}. Using pattern matching only.")
            self.analyzer = None
            self.presidio_enabled = False
        
        # Presidio entity types to detect
        self.SENSITIVE_TYPES = {
            "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS",
            "US_SSN", "IBAN_CODE", "LOCATION", "PERSON", "US_PASSPORT"
        }
        
        # ==================== ENHANCED DETECTION PATTERNS ====================
        # API/Secret label detection
        self.api_label_re = re.compile(r'\b(api[_\-\s]?key|[A-Za-z0-9\-_]*secret|password|token|auth|bearer|credentials)\b', re.I)
        self.key_candidate_re = re.compile(r'^[A-Za-z0-9_\-]{16,}$')
        
        # Common words to skip
        self.COMMON_WORDS = {
            'the', 'and', 'for', 'from', 'with', 'this', 'that', 'your', 
            'have', 'been', 'are', 'was', 'were', 'will', 'can', 'could',
            'would', 'should', 'file', 'line', 'code', 'text', 'name'
        }
        
        # Filenames to IGNORE
        self.IGNORE_PATTERNS = re.compile(
            r'\.(txt|pdf|docx|xlsx|jpg|png|exe|py|java|js|html|css|json|xml|log|csv|sql|db|sh|bat|'
            r'mp4|avi|mkv|mov|zip|rar|7z|tar|gz|dll|so|o|app|dmg)$|'
            r'(C:\\|D:\\|E:\\|F:\\|G:\\|H:\\|:\\\\|/|file|folder|directory|downloads|documents|desktop|'
            r'\.git|\.env|\.json|\.xml|\.log|\.txt|__pycache__|node_modules|/home/user|/usr/)',
            re.IGNORECASE
        )
    
    def detect_confidential_data(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect confidential data using OCR + Presidio
        Returns list of (x, y, width, height) tuples for regions to blur
        """
        self.frame_count += 1
        
        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Fast OCR
            data = pytesseract.image_to_data(
                gray, 
                output_type=pytesseract.Output.DICT, 
                config='--psm 6'
            )
            n = len(data["text"])
            
            temp_sensitive = []
            temp_api_blur = []
            blurred_words = set()
            
            # Extract words with positions
            words_list = []
            for i in range(n):
                text = data["text"][i].strip()
                if text and len(text) > 1:
                    box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                    words_list.append((text, box, i))
            
            # ===== PASS 1: Detect API/secret labels and values =====
            for i, (text, box, idx) in enumerate(words_list):
                if idx in blurred_words:
                    continue
                
                # Check for API/secret labels
                if self.api_label_re.search(text):
                    lx, ly, lw, lh = box
                    
                    # Look ahead for value (next 1-5 words)
                    for j in range(i + 1, min(i + 6, len(words_list))):
                        if j >= len(words_list):
                            break
                        next_text, next_box, next_idx = words_list[j]
                        if next_idx in blurred_words:
                            continue
                        
                        # Value should be substantial
                        if len(next_text) >= 6:
                            cx, cy, cw, ch = next_box
                            vert_dist = cy - (ly + lh)
                            
                            # Check if on same line or next line
                            if -lh < vert_dist < lh * 2.5:
                                # Blur both label and value
                                x1 = max(0, min(lx, cx) - self.padding_px * 3)
                                y1 = max(0, min(ly, cy) - self.padding_px * 2)
                                x2 = min(gray.shape[1], max(lx + lw, cx + cw) + self.padding_px * 3)
                                y2 = min(gray.shape[0], max(ly + lh, cy + ch) + self.padding_px * 2)
                                temp_api_blur.append((x1, y1, x2 - x1, y2 - y1))
                                blurred_words.add(idx)
                                blurred_words.add(next_idx)
                                break
            
            # ===== PASS 2: Presidio for sensitive data =====
            if self.presidio_enabled and self.analyzer:
                for text, box, idx in words_list:
                    if idx in blurred_words or len(text) < 3:
                        continue
                    
                    # Skip common words
                    if text.lower() in self.COMMON_WORDS:
                        continue
                    
                    try:
                        results = self.analyzer.analyze(text=text, language="en")
                        sensitive_results = [r for r in results if r.entity_type in self.SENSITIVE_TYPES]
                        if sensitive_results:
                            lx, ly, lw, lh = box
                            x1 = max(0, lx - self.padding_px)
                            y1 = max(0, ly - self.padding_px)
                            x2 = min(gray.shape[1], lx + lw + self.padding_px)
                            y2 = min(gray.shape[0], ly + lh + self.padding_px)
                            temp_sensitive.append((x1, y1, x2 - x1, y2 - y1))
                            blurred_words.add(idx)
                    except Exception:
                        pass
            
            # Combine all blur regions
            all_regions = temp_api_blur + temp_sensitive
            self.blur_regions_cache = all_regions
            return all_regions
            
        except Exception as e:
            print(f"[OCR Error] {e}")
            return self.blur_regions_cache
    
    def apply_blur_to_frame(self, frame: np.ndarray, blur_regions: List[Tuple[int, int, int, int]], 
                           blur_ksize=(35, 35), blur_sigma=25) -> np.ndarray:
        """Apply Gaussian blur to specified regions"""
        for (x, y, w, h) in blur_regions:
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            if x2 > x1 and y2 > y1:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(
                    frame[y1:y2, x1:x2], blur_ksize, blur_sigma
                )
        return frame
