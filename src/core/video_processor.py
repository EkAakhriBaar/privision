"""
Video Processor - Process recorded videos with face blur and sensitive data detection
Handles frame-by-frame processing and exports to processed_recordings folder
"""
import cv2
import numpy as np
import time
import re
from pathlib import Path
from datetime import datetime
try:
    import pytesseract
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from screeninfo import get_monitors
    ADVANCED_OCR_AVAILABLE = True
except ImportError:
    ADVANCED_OCR_AVAILABLE = False
    print("⚠️  Advanced OCR not available. Install: pip install pytesseract presidio-analyzer screeninfo")


class VideoProcessor:
    """Process videos with face blur and sensitive data blur"""
    
    def __init__(self):
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if self.face_cascade.empty():
            raise RuntimeError("Could not load Haar cascade for face detection")
        
        # DPI and pixel scaling for text detection
        try:
            if ADVANCED_OCR_AVAILABLE:
                width_mm = get_monitors()[0].width_mm
                width_px = get_monitors()[0].width
                DPI = width_px / (width_mm / 25.4)
                self.PX_PER_CM = DPI / 2.54
            else:
                self.PX_PER_CM = 37.8  # Default ~96 DPI
        except:
            self.PX_PER_CM = 37.8
        
        # Blur settings
        self.BLUR_KSIZE = (51, 51)
        self.BLUR_SIGMA = 30
        self.FACE_DETECT_EVERY = 5
        self.OCR_EVERY = 10
        self.SCALE = 0.5
        
        # API key detection settings
        self.MAX_HORIZONTAL_GAP = int(7 * self.PX_PER_CM)
        self.MAX_VERTICAL_GAP = int(2 * self.PX_PER_CM)
        self.API_KEY_PADDING = int(0.4 * self.PX_PER_CM)
        self.API_KEY_MIN_LEN = 16
        
        # Presidio setup for sensitive data
        if ADVANCED_OCR_AVAILABLE:
            try:
                config = {
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
                }
                provider = NlpEngineProvider(nlp_configuration=config)
                nlp_engine = provider.create_engine()
                self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
                
                self.SENSITIVE_TYPES = {
                    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IP_ADDRESS",
                    "US_SSN", "IBAN_CODE", "LOCATION", "GPE", "FAC"
                }
                print("✅ Presidio analyzer initialized successfully")
            except Exception as e:
                print(f"⚠️  Presidio initialization failed: {e}")
                self.analyzer = None
                self.SENSITIVE_TYPES = set()
        else:
            self.analyzer = None
            self.SENSITIVE_TYPES = set()
        
        # Regex patterns
        self.api_label_re = re.compile(r'(api[_\-\s]?key|[a-z0-9\-_]*secret\b)', re.I)
        self.key_candidate_re = re.compile(r'^[A-Za-z0-9_\-]{16,}$')
        
        # Cache
        self.faces_cache = []
        self.sensitive_boxes = []
        self.api_blur_boxes = []
        
        # Processing state
        self.is_processing = False
        self.progress_callback = None
        self.status_callback = None
    
    def set_callbacks(self, progress_callback=None, status_callback=None):
        """Set callbacks for progress updates"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
    
    def _update_progress(self, current_frame, total_frames):
        """Update progress callback"""
        if self.progress_callback:
            progress = int((current_frame / total_frames) * 100)
            self.progress_callback(progress)
    
    def _update_status(self, status_text):
        """Update status callback"""
        if self.status_callback:
            self.status_callback(status_text)
    
    def detect_faces(self, frame, frame_idx):
        """Detect faces in frame and update cache"""
        if frame_idx % self.FACE_DETECT_EVERY == 0:
            small = cv2.resize(frame, None, fx=self.SCALE, fy=self.SCALE)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            det = self.face_cascade.detectMultiScale(gray_small, 1.1, 5, minSize=(24, 24))
            self.faces_cache = [
                (int(x / self.SCALE), int(y / self.SCALE), 
                 int(w / self.SCALE), int(h / self.SCALE))
                for (x, y, w, h) in det
            ]
    
    def apply_face_blur(self, frame):
        """Apply blur to detected faces"""
        for (x, y, w, h) in self.faces_cache:
            roi = frame[y:y + h, x:x + w]
            if roi.size:
                frame[y:y + h, x:x + w] = cv2.GaussianBlur(roi, self.BLUR_KSIZE, self.BLUR_SIGMA)
        return frame
    
    def detect_sensitive_data(self, frame, frame_idx):
        """Detect sensitive data using OCR and Presidio"""
        if not ADVANCED_OCR_AVAILABLE or self.analyzer is None:
            return
        
        if frame_idx % self.OCR_EVERY == 0:
            self.api_blur_boxes.clear()
            self.sensitive_boxes.clear()
            
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
                n = len(data["text"])
                
                # Extract words with bounding boxes
                words = [
                    (data["text"][i].strip(),
                     (data["left"][i], data["top"][i], data["width"][i], data["height"][i]))
                    for i in range(n) if data["text"][i].strip()
                ]
                
                # Detect sensitive data with Presidio
                for i, (label, lb) in enumerate(words):
                    results = self.analyzer.analyze(text=label, language="en")
                    results = [r for r in results if r.entity_type in self.SENSITIVE_TYPES]
                    if results:
                        self.sensitive_boxes.append(lb)
                    
                    # API key detection
                    if not self.api_label_re.search(label):
                        continue
                    
                    lx, ly, lw, lh = lb
                    lcx = lx + lw // 2
                    lcy = ly + lh // 2
                    
                    # Look for potential API key value nearby
                    for j, (cand, cb) in enumerate(words):
                        if i == j or not self.key_candidate_re.match(cand):
                            continue
                        
                        cx, cy, cw, ch = cb
                        ccx = cx + cw // 2
                        ccy = cy + ch // 2
                        
                        horiz_gap = cx - (lx + lw)
                        vert_gap = cy - (ly + lh)
                        
                        # Check if key is horizontally or vertically near label
                        if (0 < horiz_gap < self.MAX_HORIZONTAL_GAP and abs(ccy - lcy) < lh) or \
                           (0 < vert_gap < self.MAX_VERTICAL_GAP and abs(ccx - lcx) < lw):
                            x1 = max(0, min(lx, cx) - self.API_KEY_PADDING)
                            y1 = max(0, min(ly, cy) - self.API_KEY_PADDING)
                            x2 = min(frame.shape[1], max(lx + lw, cx + cw) + self.API_KEY_PADDING)
                            y2 = min(frame.shape[0], max(ly + lh, cy + ch) + self.API_KEY_PADDING)
                            self.api_blur_boxes.append((x1, y1, x2 - x1, y2 - y1))
                            break
            
            except Exception as e:
                print(f"⚠️  OCR error: {e}")
    
    def apply_sensitive_blur(self, frame):
        """Apply blur to sensitive data regions"""
        for (x, y, w, h) in self.api_blur_boxes + self.sensitive_boxes:
            roi = frame[y:y + h, x:x + w]
            if roi.size:
                frame[y:y + h, x:x + w] = cv2.GaussianBlur(roi, self.BLUR_KSIZE, self.BLUR_SIGMA)
        return frame
    
    def process_video(self, input_video_path, output_dir, 
                     enable_face_blur=True, enable_sensitive_blur=True):
        """
        Process video frame by frame with blur effects
        
        Args:
            input_video_path: Path to input video file
            output_dir: Directory to save processed video
            enable_face_blur: Enable face detection and blur
            enable_sensitive_blur: Enable sensitive data detection and blur
        
        Returns:
            Path to processed video file or None if failed
        """
        self.is_processing = True
        self.faces_cache = []
        self.sensitive_boxes = []
        self.api_blur_boxes = []
        
        input_path = Path(input_video_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"processed_{input_path.stem}_{timestamp}.mp4"
        
        cap = None
        out = None
        
        try:
            self._update_status("🎬 Opening video file...")
            
            # Open input video
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception(f"Failed to open video: {input_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self._update_status(f"📹 Video: {width}x{height} @ {fps:.1f}fps | {total_frames} frames")
            print(f"📹 Input: {input_path.name}")
            print(f"📹 Resolution: {width}x{height} @ {fps:.1f}fps")
            print(f"📹 Total frames: {total_frames}")
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_file), fourcc, fps, (width, height))
            
            if not out.isOpened():
                raise Exception("Failed to create output video file")
            
            # Process frames
            frame_idx = 0
            t_start = time.time()
            last_log_time = t_start
            
            self._update_status("⚙️ Processing video frames...")
            
            while self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                frame_start = time.time()
                
                # Face detection
                if enable_face_blur:
                    self.detect_faces(frame, frame_idx)
                    frame = self.apply_face_blur(frame)
                
                # Sensitive data detection
                if enable_sensitive_blur:
                    self.detect_sensitive_data(frame, frame_idx)
                    frame = self.apply_sensitive_blur(frame)
                
                # Write processed frame
                out.write(frame)
                
                # Update progress
                self._update_progress(frame_idx, total_frames)
                
                # Log progress every 2 seconds
                current_time = time.time()
                if current_time - last_log_time >= 2.0:
                    elapsed = current_time - t_start
                    fps_actual = frame_idx / elapsed if elapsed > 0 else 0
                    remaining_frames = total_frames - frame_idx
                    eta_seconds = remaining_frames / fps_actual if fps_actual > 0 else 0
                    
                    status_msg = (f"⚙️ Processing: {frame_idx}/{total_frames} frames | "
                                f"Speed: {fps_actual:.1f} fps | ETA: {eta_seconds:.0f}s")
                    self._update_status(status_msg)
                    last_log_time = current_time
                    
                    print(f"📹 [{frame_idx}/{total_frames}] "
                          f"({(frame_idx/total_frames)*100:.1f}%) | "
                          f"Speed: {fps_actual:.1f} fps | "
                          f"Frame time: {time.time() - frame_start:.3f}s")
            
            # Release resources
            cap.release()
            out.release()
            
            # Final statistics
            total_time = time.time() - t_start
            avg_fps = frame_idx / total_time if total_time > 0 else 0
            
            if frame_idx == total_frames:
                self._update_status(f"✅ Completed! Processed {frame_idx} frames in {total_time:.1f}s")
                print(f"\n📊 ═══════════════════════════════════════")
                print(f"✅ Video Processing Complete!")
                print(f"   • Input: {input_path.name}")
                print(f"   • Output: {output_file.name}")
                print(f"   • Total frames: {frame_idx}")
                print(f"   • Processing time: {total_time:.1f}s")
                print(f"   • Average speed: {avg_fps:.2f} fps")
                print(f"   • Face blur: {'✅ Enabled' if enable_face_blur else '❌ Disabled'}")
                print(f"   • Sensitive blur: {'✅ Enabled' if enable_sensitive_blur else '❌ Disabled'}")
                print(f"📊 ═══════════════════════════════════════\n")
                
                return str(output_file)
            else:
                self._update_status("⚠️ Processing cancelled")
                # Delete incomplete file
                if output_file.exists():
                    output_file.unlink()
                return None
        
        except Exception as e:
            self._update_status(f"❌ Error: {str(e)}")
            print(f"❌ Video processing error: {e}")
            import traceback
            traceback.print_exc()
            
            # Delete incomplete file
            if output_file.exists():
                output_file.unlink()
            
            return None
        
        finally:
            # Clean up
            if cap is not None:
                cap.release()
            if out is not None:
                out.release()
            
            self.is_processing = False
    
    def stop_processing(self):
        """Stop the video processing"""
        self.is_processing = False
