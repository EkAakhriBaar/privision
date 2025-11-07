"""
Screen Recorder Pro - Modern UI with Component Architecture
Clean, professional design with proper spacing and separation of concerns
"""
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton, QLabel
)
from PyQt5.QtGui import QFont
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


class RecorderSignals(QObject):
    """Custom signals for recorder events"""
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    recording_error = pyqtSignal(str)


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
        
        # Setup recordings directory
        self.recordings_dir = Path(__file__).parent.parent / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        
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
        
        self.settings_window.exec_()
    
    def apply_settings(self):
        """Apply settings from settings window"""
        if self.settings_window:
            self.current_resolution = self.settings_window.get_resolution()
            self.current_fps = self.settings_window.get_fps()
            self.blur_enabled = self.settings_window.is_blur_enabled()
            self.statusBar().showMessage("✅ Settings saved successfully!")
    
    def apply_face_blur(self, frame):
        """Detect faces and blur them"""
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
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, self.BLUR_KSIZE, self.BLUR_SIGMA)
        
        return frame
    
    def start_recording(self):
        """Start screen recording"""
        self.recording = True
        self.frame_count = 0
        self.detect_frame_idx = 0
        self.start_time = datetime.now()
        
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
            
            # Screen capture
            import mss
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            frame_time = time.time()
            
            while self.recording:
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                if (frame.shape[1], frame.shape[0]) != (width, height):
                    frame = cv2.resize(frame, (width, height))
                
                frame = self.apply_face_blur(frame)
                
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                
                self.out.write(frame)
                self.frame_count += 1
                
                # Control frame rate
                elapsed = time.time() - frame_time
                sleep_time = frame_duration - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                frame_time = time.time()
            
            self.out.release()
            sct.close()
            
        except Exception as e:
            self.recorder_signals.recording_error.emit(f"Recording error: {str(e)}")
    
    def stop_recording(self):
        """Stop screen recording"""
        self.recording = False
        self.timer.stop()
        self.preview_timer.stop()
        self.preview_signal_timer.stop()
        
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
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.recording:
            self.stop_recording()
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
