"""
Confidential Data Detector - OCR + Presidio-based sensitive information detection
Detects and provides blur coordinates for API keys, passwords, emails, phone numbers, etc.
"""
import cv2
import numpy as np
import re
import pytesseract
import time
from typing import List, Tuple, Set
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider


class ConfidentialDataDetector:
    """Detects confidential information using OCR, Presidio, and pattern matching"""
    
    def __init__(self, padding_px=20):
        self.padding_px = padding_px
        self.blur_regions_cache = []
        self.last_detect_time = 0.0
        self.cache_ttl_sec = 1.2  # Keep last boxes briefly to prevent flicker
        
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
        
        PERFORMANCE OPTIMIZATION: Downscales frame for OCR, then scales coordinates back
        """
        self.frame_count += 1
        
        try:
            # ===== DOWNSCALE FOR PERFORMANCE =====
            # OCR on full 1920x1080 is VERY slow (~300ms)
            # Downscaling to 640x360 makes it 10x faster (~30ms)
            orig_height, orig_width = frame.shape[:2]
            target_width = 640
            scale_factor = target_width / orig_width
            target_height = int(orig_height * scale_factor)
            
            # Downscale frame for OCR
            small_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
            
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            # Slight denoise to improve OCR accuracy on UI text
            gray = cv2.bilateralFilter(gray, d=7, sigmaColor=75, sigmaSpace=75)
            
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
            
            # Extract words with positions (with confidence filtering)
            words_list = []
            for i in range(n):
                text = data["text"][i].strip()
                # Confidence filtering: only accept text with conf >= 60
                try:
                    conf = float(data.get("conf", ["-1"])[i])
                except (ValueError, IndexError, TypeError):
                    conf = -1.0
                
                if text and len(text) > 1 and conf >= 60.0:
                    box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                    words_list.append((text, box, i, conf))
            
            # ===== PASS 1: Detect API/secret labels and values =====
            for i, (text, box, idx, conf) in enumerate(words_list):
                if idx in blurred_words:
                    continue
                
                # Check for API/secret labels
                if self.api_label_re.search(text):
                    lx, ly, lw, lh = box
                    
                    # Look ahead for value (next 1-5 words)
                    for j in range(i + 1, min(i + 6, len(words_list))):
                        if j >= len(words_list):
                            break
                        next_text, next_box, next_idx, next_conf = words_list[j]
                        if next_idx in blurred_words:
                            continue
                        
                        # Value should be substantial and confident
                        if len(next_text) >= 6 and next_conf >= 60.0:
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
                for text, box, idx, conf in words_list:
                    if idx in blurred_words or len(text) < 3 or conf < 60.0:
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
            
            # Merge overlapping/nearby boxes to reduce jitter and cover full tokens
            all_regions = self._merge_overlapping_boxes(all_regions, iou_threshold=0.2, expand_px=6)
            
            # ===== SCALE COORDINATES BACK TO ORIGINAL RESOLUTION =====
            # Since we downscaled the frame for OCR, we MUST scale coordinates back
            # This ensures blur is applied at the CORRECT LOCATION on the full-res frame
            scaled_regions = []
            for (x, y, w, h) in all_regions:
                # Scale coordinates back to original frame size
                scaled_x = int(x / scale_factor)
                scaled_y = int(y / scale_factor)
                scaled_w = int(w / scale_factor)
                scaled_h = int(h / scale_factor)
                scaled_regions.append((scaled_x, scaled_y, scaled_w, scaled_h))
            
            # Merge again after scaling to ensure clean boxes
            scaled_regions = self._merge_overlapping_boxes(scaled_regions, iou_threshold=0.2, expand_px=8)
            
            self.blur_regions_cache = scaled_regions
            self.last_detect_time = time.time()
            print(f"🔍 [OCR] Regions: {len(scaled_regions)} | scale {1/scale_factor:.2f}x")
            return scaled_regions
            
        except Exception as e:
            print(f"[OCR Error] {e}")
            # Return cached if still fresh to avoid flicker
            if time.time() - self.last_detect_time <= self.cache_ttl_sec:
                return self.blur_regions_cache
            return []
    
    def apply_blur_to_frame(self, frame: np.ndarray, blur_regions: List[Tuple[int, int, int, int]], 
                           blur_ksize=(35, 35), blur_sigma=25) -> np.ndarray:
        """Apply Gaussian blur to specified regions
        
        Args:
            frame: Full resolution frame (e.g., 1920x1080)
            blur_regions: List of (x, y, width, height) tuples in FULL RESOLUTION coordinates
            blur_ksize: Gaussian blur kernel size
            blur_sigma: Gaussian blur sigma
        
        Returns:
            Frame with blur applied at correct locations
        """
        frame_h, frame_w = frame.shape[:2]
        
        for (x, y, w, h) in blur_regions:
            # Clamp coordinates to frame boundaries
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame_w, x + w), min(frame_h, y + h)
            
            # Apply blur if region is valid
            if x2 > x1 and y2 > y1:
                roi = frame[y1:y2, x1:x2]
                if roi.size > 0:
                    frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, blur_ksize, blur_sigma)
        
        return frame
    
    @staticmethod
    def _iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union for two boxes"""
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        ax2, ay2 = ax + aw, ay + ah
        bx2, by2 = bx + bw, by + bh
        inter_x1, inter_y1 = max(ax, bx), max(ay, by)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        inter_w, inter_h = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        if inter_area == 0:
            return 0.0
        area_a = aw * ah
        area_b = bw * bh
        union = area_a + area_b - inter_area
        return inter_area / max(union, 1)
    
    @staticmethod
    def _expand_box(box: Tuple[int, int, int, int], px: int, max_w: int = None, max_h: int = None) -> Tuple[int, int, int, int]:
        """Expand box by px pixels"""
        x, y, w, h = box
        x1 = max(0, x - px)
        y1 = max(0, y - px)
        x2 = x + w + px
        y2 = y + h + px
        if max_w is not None:
            x2 = min(max_w, x2)
        if max_h is not None:
            y2 = min(max_h, y2)
        return (x1, y1, max(0, x2 - x1), max(0, y2 - y1))
    
    def _merge_overlapping_boxes(self, boxes: List[Tuple[int, int, int, int]], iou_threshold: float = 0.2, expand_px: int = 6) -> List[Tuple[int, int, int, int]]:
        """Merge overlapping boxes to reduce jitter and cover complete text regions"""
        if not boxes:
            return []
        
        # Expand boxes slightly to fuse near neighbors
        expanded = []
        for b in boxes:
            expanded.append(self._expand_box(b, expand_px))
        boxes = expanded
        
        # Simple greedy merge by IoU
        boxes = sorted(boxes, key=lambda b: (b[0], b[1]))
        result: List[Tuple[int, int, int, int]] = []
        
        for b in boxes:
            merged_flag = False
            for i, r in enumerate(result):
                if self._iou(b, r) >= iou_threshold:
                    # Merge into r (union)
                    x1 = min(b[0], r[0])
                    y1 = min(b[1], r[1])
                    x2 = max(b[0] + b[2], r[0] + r[2])
                    y2 = max(b[1] + b[3], r[1] + r[3])
                    result[i] = (x1, y1, x2 - x1, y2 - y1)
                    merged_flag = True
                    break
            if not merged_flag:
                result.append(b)
        
        return result
