"""
Screen Recorder Pro - Modern UI with Component Architecture
Clean, professional design with proper spacing and separation of concerns
"""
import sys
import threading
import time
import subprocess
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton, QLabel, QInputDialog, QDialog, QLineEdit
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import numpy as np
import cv2

# Import custom components
from components import (
    HeaderComponent, SettingsPanel, StatusPanel,
    PreviewPanel, ControlButtons
)
from components.settings_window import SettingsWindow
from components.video_gallery import VideoGallery
from styles.modern_styles import get_main_window_style, COLORS, SPACING, FONTS
from core.confidential_detector import ConfidentialDataDetector


class StyledStreamKeyDialog(QDialog):
    """Custom styled dialog for stream key input"""
    def __init__(self, parent, title, platform_icon, platform_name):
        super().__init__(parent)
        self.stream_key = None
        self.setWindowTitle(title)
        self.setFixedSize(600, 350)
        self.setModal(True)
        
        # Set dark theme with better styling
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['bg_primary']}, 
                    stop:1 #0f1419);
                border-radius: 12px;
            }}
            QLabel {{
                color: white;
                font-size: 14px;
                padding: 5px;
            }}
            QLineEdit {{
                background-color: #1a2332;
                color: white;
                border: 2px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
                selection-background-color: {COLORS['primary']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: #1f2937;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 36px;
                font-size: 15px;
                font-weight: bold;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background-color: #4338ca;
            }}
            QPushButton#cancelButton {{
                background-color: #374151;
            }}
            QPushButton#cancelButton:hover {{
                background-color: #4b5563;
            }}
            QPushButton#cancelButton:pressed {{
                background-color: #1f2937;
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # Title with icon
        title_label = QLabel(f"{platform_icon}  {platform_name} Stream Key")
        title_label.setFont(QFont(FONTS['family_primary'], 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white; font-size: 26px; padding: 15px;")
        layout.addWidget(title_label)
        
        # Instruction label
        instruction_label = QLabel("Enter your stream key below:")
        instruction_label.setFont(QFont(FONTS['family_primary'], 14))
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("color: #9ca3af; font-size: 15px; padding: 5px;")
        layout.addWidget(instruction_label)
        
        # Stream key input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Paste your stream key here...")
        self.key_input.setFont(QFont(FONTS['family_primary'], 13))
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setMinimumHeight(50)
        layout.addWidget(self.key_input)
        
        # Show/Hide key toggle
        show_key_label = QLabel("💡 Tip: Your stream key will be hidden for security")
        show_key_label.setFont(QFont(FONTS['family_primary'], 11))
        show_key_label.setStyleSheet("color: #6b7280; font-size: 12px; padding: 5px;")
        show_key_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(show_key_label)
        
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        
        ok_btn = QPushButton("🚀 Start Stream")
        ok_btn.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        ok_btn.setMinimumHeight(50)
        ok_btn.setMinimumWidth(140)
        ok_btn.clicked.connect(self.accept_key)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Focus on input
        self.key_input.setFocus()
    
    def accept_key(self):
        """Accept the stream key if not empty"""
        key = self.key_input.text().strip()
        if key:
            self.stream_key = key
            self.accept()
        else:
            self.key_input.setStyleSheet("""
                QLineEdit {
                    background-color: #1a2332;
                    color: white;
                    border: 2px solid #ef4444;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 14px;
                }
            """)
            self.key_input.setPlaceholderText("⚠️ Stream key is required!")
    
    def get_key(self):
        """Return the entered stream key"""
        return self.stream_key


class RecorderSignals(QObject):
    """Custom signals for recorder events"""
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    recording_error = pyqtSignal(str)
    streaming_started = pyqtSignal()
    streaming_stopped = pyqtSignal()
    streaming_error = pyqtSignal(str)


class LivePreviewWindow(QMainWindow):
    """Separate fullscreen window for live preview"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📹 Live Preview - Screen Recording")
        self.setGeometry(100, 100, 960, 540)
        self.setStyleSheet("background-color: #000000;")
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview label
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtGui import QImage, QPixmap
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000000;")
        self.preview_label.setText("Waiting for recording to start...")
        self.preview_label.setFont(QFont("Arial", 16))
        self.preview_label.setStyleSheet("color: #888888; background-color: #000000;")
        layout.addWidget(self.preview_label)
        
        central.setLayout(layout)
    
    def update_frame(self, frame):
        """Update preview with new frame"""
        try:
            from PyQt5.QtGui import QImage, QPixmap
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaledToWidth(960, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            pass


class ScreenRecorder(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Recording state
        self.recording = False
        self.recording_thread = None
        self.out = None
        self.frame_count = 0
        self.start_time = None
        
        # Streaming state
        self.streaming = False
        self.streaming_thread = None
        self.ffmpeg_process = None
        self.stream_key = None
        self.streaming_platform = None
        
        # Platform RTMP URLs
        self.rtmp_urls = {
            'youtube': 'rtmp://a.rtmp.youtube.com/live2/',
            'facebook': 'rtmps://live-api-s.facebook.com:443/rtmp/',
            'twitch': 'rtmp://live.twitch.tv/app/'
        }
        
        # Setup recordings directory
        self.recordings_dir = Path(__file__).parent.parent / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        
        # Webcam setup
        self.webcam = None
        self.webcam_enabled = True
        self.webcam_size = (320, 240)  # Width, Height for webcam overlay
        
        # Face detection setup
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.faces_cache = []
        self.detect_frame_idx = 0
        self.blur_enabled = False
        
        # Blur configuration
        self.BLUR_KSIZE = (51, 51)
        self.BLUR_SIGMA = 30
        self.DETECT_EVERY = 2
        
        # Confidential data detection setup
        self.confidential_detector = ConfidentialDataDetector(padding_px=20)
        self.sensitive_blur_enabled = False
        self.confidential_blur_regions = []
        self.ocr_frame_idx = 0
        self.OCR_DETECT_EVERY = 45  # Run OCR every 45 frames (~1.5 seconds at 30fps) for performance
        self.ocr_lock = threading.Lock()
        self.ocr_thread_running = False
        self.pending_ocr_frame = None
        
        # Live preview window
        self.preview_window = LivePreviewWindow()
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Signals
        self.recorder_signals = RecorderSignals()
        self.setup_signals()
        
        # Settings window (create but don't show)
        self.settings_window = None
        self.current_resolution = (1920, 1080)
        self.current_fps = 30
        
        # Initialize UI
        self.init_ui()
        
        # Setup timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.preview_signal_timer = QTimer()
        self.preview_signal_timer.timeout.connect(self.signal_preview_update)
    
    def init_ui(self):
        """Initialize the modern UI with components"""
        self.setWindowTitle("Screen Recorder Pro - Professional Screen Sharing")
        self.setGeometry(100, 100, 1700, 1000)
        self.setMinimumSize(1500, 900)
        
        # Apply main window style
        self.setStyleSheet(get_main_window_style())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.header = HeaderComponent()
        main_layout.addWidget(self.header)
        
        # Content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_primary']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_secondary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['bg_tertiary']};
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        # Scroll content
        scroll_content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)
        
        # Top row - Settings and Status
        top_row = QHBoxLayout()
        top_row.setSpacing(24)
        
        # Settings button (opens settings window)
        settings_btn_container = QFrame()
        settings_btn_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        settings_btn_layout = QVBoxLayout()
        settings_btn_layout.setSpacing(16)
        
        settings_title = QLabel("⚙️  Settings")
        settings_title.setFont(QFont(FONTS['family_primary'], 18, QFont.Bold))
        settings_title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        settings_btn_layout.addWidget(settings_title)
        
        self.settings_button = QPushButton("Open Settings Panel")
        self.settings_button.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        self.settings_button.setFixedHeight(56)
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: {8};
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        settings_btn_layout.addWidget(self.settings_button)
        
        settings_desc = QLabel("Configure recording settings,\nprivacy options, and more")
        settings_desc.setFont(QFont(FONTS['family_primary'], 12))
        settings_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        settings_btn_layout.addWidget(settings_desc)
        
        settings_btn_container.setLayout(settings_btn_layout)
        top_row.addWidget(settings_btn_container)
        
        self.status_panel = StatusPanel()
        top_row.addWidget(self.status_panel)
        
        content_layout.addLayout(top_row)
        
        # Middle row - Preview and Controls
        middle_row = QHBoxLayout()
        middle_row.setSpacing(24)
        
        self.preview_panel = PreviewPanel()
        middle_row.addWidget(self.preview_panel, 2)
        
        self.control_buttons = ControlButtons(self.recordings_dir)
        self.control_buttons.start_clicked.connect(self.start_recording)
        self.control_buttons.stop_clicked.connect(self.stop_recording)
        self.control_buttons.stream_clicked.connect(self.start_streaming)  # Now receives platform parameter
        self.control_buttons.stop_stream_clicked.connect(self.stop_streaming)
        middle_row.addWidget(self.control_buttons, 1)
        
        content_layout.addLayout(middle_row)
        
        # Bottom row - Video Gallery
        self.video_gallery = VideoGallery(self.recordings_dir)
        content_layout.addWidget(self.video_gallery)
        
        scroll_content.setLayout(content_layout)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area, 1)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_secondary']};
                border-top: 1px solid {COLORS['border_primary']};
                padding: 8px 16px;
                font-size: 12px;
            }}
        """)
        self.statusBar().showMessage("Ready to record")
    
    def setup_signals(self):
        """Setup signal connections"""
        self.recorder_signals.recording_started.connect(self.on_recording_started)
        self.recorder_signals.recording_stopped.connect(self.on_recording_stopped)
        self.recorder_signals.recording_error.connect(self.on_recording_error)
    
    def on_blur_toggled(self, enabled):
        """Handle blur checkbox toggle"""
        self.blur_enabled = enabled
        status = "✅ Enabled" if enabled else "⭕ Disabled"
        self.statusBar().showMessage(f"Face blur {status}")
    
    def open_settings(self):
        """Open settings window"""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
            self.settings_window.settings_saved.connect(self.apply_settings)
            # Set current values
            self.settings_window.resolution_combo.setCurrentText(f"{self.current_resolution[0]}x{self.current_resolution[1]} (Full HD)")
            self.settings_window.fps_spinbox.setValue(self.current_fps)
            self.settings_window.blur_checkbox.setChecked(self.blur_enabled)
            self.settings_window.sensitive_blur_checkbox.setChecked(self.sensitive_blur_enabled)
        
        self.settings_window.exec_()
    
    def apply_settings(self):
        """Apply settings from settings window"""
        if self.settings_window:
            self.current_resolution = self.settings_window.get_resolution()
            self.current_fps = self.settings_window.get_fps()
            self.blur_enabled = self.settings_window.is_blur_enabled()
            self.sensitive_blur_enabled = self.settings_window.is_sensitive_content_blur_enabled()
            
            status_msg = "✅ Settings saved successfully!"
            if self.sensitive_blur_enabled:
                status_msg += " | 🔒 Sensitive data blur enabled"
            self.statusBar().showMessage(status_msg)
    
    def apply_face_blur(self, frame, webcam_rect=None):
        """Detect faces and blur them (excluding webcam area)"""
        if not self.blur_enabled or self.face_cascade.empty():
            return frame
        
        self.detect_frame_idx += 1
        
        if self.detect_frame_idx % self.DETECT_EVERY == 0:
            scale = 0.5
            small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            detected = self.face_cascade.detectMultiScale(
                gray_small, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24)
            )
            self.faces_cache = [
                (int(x/scale), int(y/scale), int(w/scale), int(h/scale))
                for (x, y, w, h) in detected
            ]
        
        for (x, y, w, h) in self.faces_cache:
            # Skip blurring if face is in webcam area
            if webcam_rect:
                wx, wy, ww, wh = webcam_rect
                # Check if face overlaps with webcam area
                if not (x + w < wx or x > wx + ww or y + h < wy or y > wy + wh):
                    continue  # Skip this face as it's in the webcam area
            
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, self.BLUR_KSIZE, self.BLUR_SIGMA)
        
        return frame
    
    def _ocr_worker_thread(self, frame_copy):
        """Background OCR processing thread - non-blocking"""
        try:
            detected_regions = self.confidential_detector.detect_confidential_data(frame_copy)
            with self.ocr_lock:
                self.confidential_blur_regions = detected_regions
                self.ocr_thread_running = False
        except Exception as e:
            print(f"[OCR Error] {e}")
            with self.ocr_lock:
                self.ocr_thread_running = False
    
    def apply_confidential_data_blur(self, frame):
        """Detect and blur confidential data like API keys, passwords, emails, etc. (Async OCR)"""
        if not self.sensitive_blur_enabled:
            return frame
        
        self.ocr_frame_idx += 1
        
        # Start OCR detection in background thread (non-blocking, only if not already running)
        if self.ocr_frame_idx % self.OCR_DETECT_EVERY == 0:
            with self.ocr_lock:
                if not self.ocr_thread_running:
                    self.ocr_thread_running = True
                    # Run OCR in background thread to avoid blocking
                    ocr_thread = threading.Thread(
                        target=self._ocr_worker_thread,
                        args=(frame.copy(),),
                        daemon=True
                    )
                    ocr_thread.start()
        
        # Apply blur to cached regions (instant, non-blocking)
        with self.ocr_lock:
            current_regions = self.confidential_blur_regions.copy() if self.confidential_blur_regions else []
        
        if current_regions:
            frame = self.confidential_detector.apply_blur_to_frame(
                frame, 
                current_regions,
                blur_ksize=(35, 35),
                blur_sigma=25
            )
        
        return frame
    
    def start_recording(self):
        """Start screen recording"""
        self.recording = True
        self.frame_count = 0
        self.detect_frame_idx = 0
        self.start_time = datetime.now()
        
        # Initialize webcam (optional - continue if it fails)
        if self.webcam_enabled:
            try:
                # Try to initialize webcam with proper settings
                self.webcam = cv2.VideoCapture(0)
                
                # Give webcam time to initialize
                time.sleep(0.5)
                
                if self.webcam and self.webcam.isOpened():
                    self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.webcam.set(cv2.CAP_PROP_FPS, 30)
                    self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for live feed
                    
                    # Test if webcam actually works
                    ret, test_frame = self.webcam.read()
                    if ret and test_frame is not None:
                        print("✅ Webcam initialized successfully")
                    else:
                        print("⚠️  Webcam opened but not reading frames")
                        self.webcam = None
                else:
                    print("⚠️  Webcam not available - recording without webcam")
                    self.webcam = None
            except Exception as e:
                print(f"⚠️  Failed to initialize webcam: {e}")
                self.webcam = None
        
        # Update UI
        self.control_buttons.set_recording_state(True)
        self.status_panel.update_status("🔴 Recording", 'recording')
        self.settings_button.setEnabled(False)
        
        # Show preview window
        self.preview_window.show()
        
        # Start timers
        self.timer.start(100)
        self.preview_timer.start(100)
        self.preview_signal_timer.start(50)
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
        self.recording_thread.start()
        
        self.recorder_signals.recording_started.emit()
    
    def overlay_webcam(self, frame):
        """Overlay webcam feed on the bottom-right corner"""
        try:
            if not self.webcam:
                return frame, None
            
            # Check if webcam is opened
            if not self.webcam.isOpened():
                print("Webcam not opened, trying to reconnect...")
                try:
                    self.webcam.open(0)
                except:
                    pass
                
                if not self.webcam or not self.webcam.isOpened():
                    return frame, None
            
            ret, webcam_frame = self.webcam.read()
            if not ret or webcam_frame is None:
                return frame, None
            
            # Flip webcam frame horizontally (mirror effect)
            webcam_frame = cv2.flip(webcam_frame, 1)
            
            # Resize webcam frame to specified size
            webcam_frame = cv2.resize(webcam_frame, self.webcam_size)
            
            # Calculate position (bottom-right corner with padding)
            padding = 20
            frame_height, frame_width = frame.shape[:2]
            x_offset = max(0, frame_width - self.webcam_size[0] - padding)
            y_offset = max(0, frame_height - self.webcam_size[1] - padding)
            
            # Ensure we don't go out of bounds
            x_end = min(frame_width, x_offset + self.webcam_size[0])
            y_end = min(frame_height, y_offset + self.webcam_size[1])
            
            actual_width = x_end - x_offset
            actual_height = y_end - y_offset
            
            if actual_width <= 0 or actual_height <= 0:
                return frame, None
            
            # Only resize if needed
            if (actual_width, actual_height) != self.webcam_size:
                webcam_frame = cv2.resize(webcam_frame, (actual_width, actual_height))
            
            # Add border (red rectangle)
            border_thickness = 3
            border_color = (0, 0, 255)  # Red in BGR
            cv2.rectangle(frame, 
                         (x_offset - border_thickness, y_offset - border_thickness),
                         (x_end + border_thickness, y_end + border_thickness),
                         border_color, border_thickness)
            
            # Add "LIVE" text above webcam with background
            live_text = "LIVE"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_thickness = 2
            text_color = (255, 255, 255)  # White text
            bg_color = (0, 0, 255)  # Red background
            
            text_size = cv2.getTextSize(live_text, font, font_scale, font_thickness)[0]
            text_x = x_offset + (actual_width - text_size[0]) // 2
            text_y = y_offset - 15
            
            if text_y > text_size[1]:
                # Text background box
                cv2.rectangle(frame,
                             (text_x - 8, text_y - text_size[1] - 8),
                             (text_x + text_size[0] + 8, text_y + 5),
                             bg_color, -1)
                # Text
                cv2.putText(frame, live_text, (text_x, text_y), font, font_scale, text_color, font_thickness)
            
            # Overlay webcam frame onto the main frame
            try:
                frame[y_offset:y_end, x_offset:x_end] = webcam_frame
            except ValueError as ve:
                return frame, None
            
            # Return frame and webcam rectangle for blur exclusion
            return frame, (x_offset, y_offset, actual_width, actual_height)
            
        except Exception as e:
            print(f"Webcam overlay error: {e}")
            return frame, None
    
    def record_screen(self):
        """Record the screen in a separate thread"""
        try:
            width, height = self.current_resolution
            fps = self.current_fps
            frame_duration = 1.0 / fps
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.recordings_dir / f"recording_{timestamp}.mp4"
            
            self.out = cv2.VideoWriter(str(output_file), fourcc, fps, (width, height))
            
            if not self.out.isOpened():
                raise Exception("Failed to initialize video writer")
            
            # Screen capture
            import mss
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            frame_time = time.time()
            consecutive_errors = 0
            
            while self.recording:
                try:
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    if (frame.shape[1], frame.shape[0]) != (width, height):
                        frame = cv2.resize(frame, (width, height))
                    
                    # Overlay webcam first (safe - returns original frame if webcam fails)
                    frame, webcam_rect = self.overlay_webcam(frame)
                    
                    # Apply face blur (excluding webcam area)
                    frame = self.apply_face_blur(frame, webcam_rect)
                    
                    # Apply confidential data blur if enabled
                    frame = self.apply_confidential_data_blur(frame)
                    
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                    
                    self.out.write(frame)
                    self.frame_count += 1
                    consecutive_errors = 0
                    
                    # Control frame rate
                    elapsed = time.time() - frame_time
                    sleep_time = frame_duration - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    frame_time = time.time()
                
                except Exception as frame_error:
                    consecutive_errors += 1
                    print(f"Frame capture error {consecutive_errors}: {frame_error}")
                    if consecutive_errors > 10:
                        raise Exception(f"Too many consecutive frame errors: {frame_error}")
                    time.sleep(0.1)
            
            self.out.release()
            sct.close()
            print("✅ Recording completed successfully")
            
        except Exception as e:
            print(f"❌ Recording error: {str(e)}")
            self.recorder_signals.recording_error.emit(f"Recording error: {str(e)}")
    
    def stop_recording(self):
        """Stop screen recording"""
        self.recording = False
        self.timer.stop()
        self.preview_timer.stop()
        self.preview_signal_timer.stop()
        
        # Release webcam
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None
        
        # Hide preview window
        self.preview_window.hide()
        
        # Update UI
        self.control_buttons.set_recording_state(False)
        self.status_panel.update_status("✅ Stopped", 'stopped')
        self.preview_panel.clear_preview()
        self.settings_button.setEnabled(True)
        
        # Refresh video gallery
        self.video_gallery.load_videos()
        
        self.recorder_signals.recording_stopped.emit()
    
    def update_timer(self):
        """Update timer and statistics"""
        if self.recording and self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.status_panel.update_time(time_str)
            self.status_panel.update_frames(self.frame_count)
            
            # Estimate file size
            try:
                width, height = self.current_resolution
                estimated_size = (self.frame_count * width * height * 3) / (1024 * 1024)
                self.status_panel.update_size(estimated_size)
            except:
                pass
    
    def update_preview(self):
        """Update preview panel"""
        try:
            import mss
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Overlay webcam if recording or streaming
            if self.recording or self.streaming:
                frame, webcam_rect = self.overlay_webcam(frame)
                frame = self.apply_face_blur(frame, webcam_rect)
            else:
                frame = self.apply_face_blur(frame)
            
            self.preview_panel.update_preview(frame)
            
            sct.close()
        except Exception as e:
            pass
    
    def signal_preview_update(self):
        """Update live preview window"""
        try:
            with self.frame_lock:
                if self.latest_frame is not None:
                    frame = self.latest_frame.copy()
                    self.preview_window.update_frame(frame)
        except Exception as e:
            pass
    
    def on_recording_started(self):
        """Handle recording started"""
        self.statusBar().showMessage("📹 Recording started...")
    
    def on_recording_stopped(self):
        """Handle recording stopped"""
        self.statusBar().showMessage(f"✅ Recording completed. {self.frame_count:,} frames saved.")
    
    def on_recording_error(self, error_msg):
        """Handle recording error"""
        self.status_panel.update_status(f"❌ Error", 'error')
        self.stop_recording()
        self.statusBar().showMessage(f"Error: {error_msg}")
    
    def start_streaming(self, platform='youtube'):
        """Start live streaming to RTMP server"""
        # Store the platform
        self.streaming_platform = platform
        
        # Platform-specific info
        platform_info = {
            'youtube': {
                'title': 'YouTube Live',
                'icon': '📺',
                'name': 'YouTube'
            },
            'facebook': {
                'title': 'Facebook Live',
                'icon': '📘',
                'name': 'Facebook'
            },
            'twitch': {
                'title': 'Twitch',
                'icon': '🎮',
                'name': 'Twitch'
            }
        }
        
        info = platform_info.get(platform, platform_info['youtube'])
        
        # Show custom styled dialog
        dialog = StyledStreamKeyDialog(
            self, 
            info['title'],
            info['icon'],
            info['name']
        )
        
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            stream_key = dialog.get_key()
            if stream_key:
                self.stream_key = stream_key
            else:
                self.statusBar().showMessage(f"❌ {platform.capitalize()} stream key not provided")
                return
        else:
            self.statusBar().showMessage(f"❌ Streaming cancelled")
            return
        self.streaming = True
        self.frame_count = 0
        
        # Initialize webcam (optional - continue if it fails)
        if self.webcam_enabled:
            try:
                # Try to initialize webcam with proper settings
                self.webcam = cv2.VideoCapture(0)
                
                # Give webcam time to initialize
                time.sleep(0.5)
                
                if self.webcam and self.webcam.isOpened():
                    self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.webcam.set(cv2.CAP_PROP_FPS, 30)
                    self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Test if webcam actually works
                    ret, test_frame = self.webcam.read()
                    if ret and test_frame is not None:
                        print("✅ Webcam initialized successfully")
                    else:
                        print("⚠️  Webcam opened but not reading frames")
                        self.webcam = None
                else:
                    print("⚠️  Webcam not available - streaming without webcam")
                    self.webcam = None
            except Exception as e:
                print(f"⚠️  Failed to initialize webcam: {e}")
                self.webcam = None
        
        # Update UI with platform-specific icon
        platform_icons = {
            'youtube': '📺',
            'facebook': '📘',
            'twitch': '🎮'
        }
        icon = platform_icons.get(platform, '📡')
        
        self.control_buttons.set_streaming_state(True)
        self.status_panel.update_status(f"{icon} Streaming to {platform.capitalize()}", 'recording')
        self.settings_button.setEnabled(False)
        
        # Show preview window
        self.preview_window.show()
        
        # Start timers
        self.timer.start(100)
        self.preview_timer.start(100)
        self.preview_signal_timer.start(50)
        
        # Start streaming thread
        self.streaming_thread = threading.Thread(target=self.stream_screen, daemon=True)
        self.streaming_thread.start()
        
        # Platform-specific status messages
        platform_icons = {
            'youtube': '📺',
            'facebook': '📘',
            'twitch': '🎮'
        }
        icon = platform_icons.get(platform, '📡')
        
        self.recorder_signals.streaming_started.emit()
        self.statusBar().showMessage(f"{icon} Streaming to {platform.capitalize()}!")
    
    def stream_screen(self):
        """Stream the screen to RTMP server"""
        try:
            width, height = self.current_resolution
            fps = self.current_fps
            
            # Get RTMP URL for the selected platform
            rtmp_url = self.rtmp_urls.get(self.streaming_platform, self.rtmp_urls['youtube'])
            
            # Use full path to FFmpeg
            ffmpeg_path = r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe"
            
            # Platform-specific encoding settings
            if self.streaming_platform == 'facebook':
                # Facebook Live requires specific settings
                output_format = "flv"
                video_bitrate = "4500k"
                preset = "veryfast"
            elif self.streaming_platform == 'twitch':
                # Twitch optimized settings
                output_format = "flv"
                video_bitrate = "6000k"
                preset = "veryfast"
            else:  # YouTube
                output_format = "flv"
                video_bitrate = "4500k"
                preset = "veryfast"
            
            # FFmpeg command for streaming
            ffmpeg_cmd = [
                "ffmpeg",
                "-loglevel", "error",
                "-y",
                
                # Input 0: raw video from stdin
                "-thread_queue_size", "512",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{width}x{height}",
                "-r", str(fps),
                "-i", "-",  # stdin video stream
                
                # Input 1: silent audio
                "-thread_queue_size", "512",
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                
                # Output encoding
                "-vf", "scale=1280:720",  # downscale to 720p
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", preset,
                "-b:v", video_bitrate,
                "-maxrate", video_bitrate,
                "-bufsize", "9000k",
                "-g", str(fps * 2),
                "-keyint_min", str(fps),
                "-c:a", "aac",
                "-ar", "44100",
                "-b:a", "128k",
                "-f", output_format,
                f"{rtmp_url}{self.stream_key}"
            ]
            
            # Start FFmpeg process
            print(f"🚀 Starting stream to {self.streaming_platform}...")
            print(f"📡 RTMP URL: {rtmp_url}")
            
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
            
            # Start a thread to monitor FFmpeg errors
            def monitor_ffmpeg_errors():
                while self.streaming and self.ffmpeg_process:
                    try:
                        line = self.ffmpeg_process.stderr.readline()
                        if line:
                            error_msg = line.decode('utf-8', errors='ignore').strip()
                            if error_msg:
                                print(f"[FFmpeg] {error_msg}")
                    except:
                        break
            
            error_thread = threading.Thread(target=monitor_ffmpeg_errors, daemon=True)
            error_thread.start()
            
            print("🚀 Streaming started...")
            
            # Screen capture for streaming
            import mss
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            frame_duration = 1.0 / fps
            frame_time = time.time()
            consecutive_errors = 0
            
            while self.streaming:
                try:
                    # Capture screen
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    if (frame.shape[1], frame.shape[0]) != (width, height):
                        frame = cv2.resize(frame, (width, height))
                    
                    # Overlay webcam
                    frame, webcam_rect = self.overlay_webcam(frame)
                    
                    # Apply face blur (excluding webcam area)
                    frame = self.apply_face_blur(frame, webcam_rect)
                    
                    # Apply confidential data blur if enabled
                    frame = self.apply_confidential_data_blur(frame)
                    
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                    
                    # Send to FFmpeg
                    self.ffmpeg_process.stdin.write(frame.tobytes())
                    self.ffmpeg_process.stdin.flush()
                    
                    self.frame_count += 1
                    consecutive_errors = 0
                    
                    # Control frame rate
                    elapsed = time.time() - frame_time
                    sleep_time = frame_duration - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    frame_time = time.time()
                
                except BrokenPipeError:
                    print("❌ FFmpeg pipe broken - connection lost")
                    raise Exception("Stream connection lost")
                except Exception as frame_error:
                    consecutive_errors += 1
                    print(f"Frame streaming error {consecutive_errors}: {frame_error}")
                    if consecutive_errors > 10:
                        raise Exception(f"Too many consecutive streaming errors: {frame_error}")
                    time.sleep(0.1)
            
            sct.close()
            if self.ffmpeg_process and self.ffmpeg_process.stdin:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait()
            
            print("✅ Streaming completed successfully")
            
        except Exception as e:
            print(f"❌ Streaming error: {str(e)}")
            self.recorder_signals.streaming_error.emit(f"Streaming error: {str(e)}")
    
    def stop_streaming(self):
        """Stop live streaming"""
        self.streaming = False
        self.timer.stop()
        self.preview_timer.stop()
        self.preview_signal_timer.stop()
        
        # Release webcam
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None
        
        # Stop FFmpeg process
        if self.ffmpeg_process:
            try:
                if self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
            self.ffmpeg_process = None
        
        # Hide preview window
        self.preview_window.hide()
        
        # Update UI
        self.control_buttons.set_streaming_state(False)
        self.status_panel.update_status("✅ Stopped", 'stopped')
        self.preview_panel.clear_preview()
        self.settings_button.setEnabled(True)
        
        self.recorder_signals.streaming_stopped.emit()
        self.statusBar().showMessage("📡 Live streaming stopped")
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop recording if active
        if self.recording:
            self.stop_recording()
        
        # Stop streaming if active
        if self.streaming:
            self.stop_streaming()
        
        # Release webcam if still active
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None
        
        self.timer.stop()
        self.preview_timer.stop()
        self.preview_signal_timer.stop()
        self.preview_window.close()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application font
    app.setFont(QFont("Segoe UI", 10))
    
    recorder = ScreenRecorder()
    recorder.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
