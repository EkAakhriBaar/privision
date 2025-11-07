import sys
import threading
import os
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QComboBox, QSpinBox, QCheckBox,
    QGridLayout, QScrollArea
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
import numpy as np
import cv2
import time


class RecorderSignals(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    recording_progress = pyqtSignal(int)
    recording_error = pyqtSignal(str)


class LivePreviewWindow(QMainWindow):
    """Separate window showing live preview of recording"""
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
    def __init__(self):
        super().__init__()
        self.recorder_signals = RecorderSignals()
        self.recording = False
        self.recording_thread = None
        self.out = None
        self.frame_count = 0
        self.start_time = None
        
        self.recordings_dir = Path(__file__).parent.parent / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        
        # Face detection variables
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
        self.preview_signal_timer = QTimer()
        self.preview_signal_timer.timeout.connect(self.signal_preview_update)
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        self.init_ui()
        self.setup_signals()
        
    def init_ui(self):
        """Initialize the user interface with modern design"""
        self.setWindowTitle("Screen Recorder Pro - Professional Screen Sharing")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Set application style
        self.setStyleSheet(self.get_main_stylesheet())
        
        # Create central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Left panel - Settings and controls
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Right panel - Preview and status
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 1)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)
        
        central_widget.setLayout(main_layout)
        
        # Setup timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
    
    def create_header(self):
        """Create the header section"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-bottom: 2px solid #764ba2;
            }
        """)
        header.setMinimumHeight(80)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        title = QLabel("📹 SCREEN RECORDER PRO")
        title_font = QFont("Arial", 28, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("color: #FFFFFF;")
        
        subtitle = QLabel("Professional Screen Sharing & Recording")
        subtitle_font = QFont("Arial", 11)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setStyleSheet("color: #E8E8FF;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        header.setLayout(layout)
        return header
    
    def create_left_panel(self):
        """Create the left panel with settings"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border: 2px solid #1a1a1a;
                border-radius: 10px;
            }
        """)
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Recording Settings Section
        layout.addWidget(self.create_section_title("⚙️ RECORDING SETTINGS"))
        
        # Resolution setting
        res_layout = QHBoxLayout()
        res_label = QLabel("Resolution:")
        res_label.setFont(QFont("Arial", 11, QFont.Bold))
        res_label.setStyleSheet("color: #FFFFFF;")
        res_label.setMinimumWidth(120)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768", "800x600"])
        self.resolution_combo.setCurrentText("1920x1080")
        self.resolution_combo.setStyleSheet(self.get_combo_stylesheet())
        self.resolution_combo.setMinimumHeight(45)
        
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.resolution_combo)
        layout.addLayout(res_layout)
        
        # FPS setting
        fps_layout = QHBoxLayout()
        fps_label = QLabel("Frame Rate:")
        fps_label.setFont(QFont("Arial", 11, QFont.Bold))
        fps_label.setStyleSheet("color: #FFFFFF;")
        fps_label.setMinimumWidth(120)
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(10, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")
        self.fps_spinbox.setStyleSheet(self.get_spinbox_stylesheet())
        self.fps_spinbox.setMinimumHeight(45)
        
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_spinbox)
        layout.addLayout(fps_layout)
        
        # Privacy Settings Section
        layout.addWidget(self.create_section_title("🔐 PRIVACY SETTINGS"))
        
        # Face blur checkbox with description
        blur_frame = QFrame()
        blur_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        blur_layout = QVBoxLayout()
        blur_layout.setContentsMargins(0, 0, 0, 0)
        blur_layout.setSpacing(10)
        
        self.blur_checkbox = QCheckBox("Enable Face Blur Protection")
        self.blur_checkbox.setFont(QFont("Arial", 12, QFont.Bold))
        self.blur_checkbox.setStyleSheet(self.get_checkbox_stylesheet())
        self.blur_checkbox.setMinimumHeight(40)
        self.blur_checkbox.setChecked(False)
        self.blur_checkbox.stateChanged.connect(self.on_blur_toggled)
        
        blur_desc = QLabel("Automatically blur faces for privacy protection")
        blur_desc.setFont(QFont("Arial", 9))
        blur_desc.setStyleSheet("color: #999999;")
        
        blur_layout.addWidget(self.blur_checkbox)
        blur_layout.addWidget(blur_desc)
        blur_frame.setLayout(blur_layout)
        layout.addWidget(blur_frame)
        
        # Statistics Section
        layout.addWidget(self.create_section_title("📊 STATISTICS"))
        
        # Frame counter
        self.frame_label = QLabel("Frames Captured: 0")
        self.frame_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.frame_label.setStyleSheet("color: #87CEEB;")
        layout.addWidget(self.frame_label)
        
        # Recording time
        self.time_label = QLabel("Recording Time: 00:00:00")
        self.time_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.time_label.setStyleSheet("color: #90EE90;")
        layout.addWidget(self.time_label)
        
        # File info
        self.file_label = QLabel("File Size: 0 MB")
        self.file_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.file_label.setStyleSheet("color: #FFD700;")
        layout.addWidget(self.file_label)
        
        # Status display
        layout.addWidget(self.create_section_title("📡 STATUS"))
        
        self.status_label = QLabel("Ready to Record")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border: 2px solid #4CAF50;")
        self.status_label.setMinimumHeight(50)
        layout.addWidget(self.status_label)
        
        # Control buttons
        layout.addWidget(self.create_section_title("🎮 CONTROLS"))
        
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Start button
        self.start_button = QPushButton("▶ START RECORDING")
        self.start_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_button.setMinimumHeight(55)
        self.start_button.setStyleSheet(self.get_start_button_stylesheet())
        self.start_button.clicked.connect(self.start_recording)
        buttons_layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("⏹ STOP RECORDING")
        self.stop_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_button.setMinimumHeight(55)
        self.stop_button.setStyleSheet(self.get_stop_button_stylesheet())
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        buttons_layout.addWidget(self.stop_button)
        
        layout.addLayout(buttons_layout)
        
        # Output directory
        layout.addWidget(self.create_section_title("💾 OUTPUT"))
        
        output_info = QLabel(f"📁 {self.recordings_dir}")
        output_info.setFont(QFont("Arial", 9))
        output_info.setStyleSheet("color: #90EE90;")
        output_info.setWordWrap(True)
        layout.addWidget(output_info)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """Create the right panel with preview"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #0d0d0d;
                border: 2px solid #1a1a1a;
                border-radius: 10px;
            }
        """)
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Preview title
        preview_title = QLabel("👁️ LIVE PREVIEW")
        preview_title.setFont(QFont("Arial", 14, QFont.Bold))
        preview_title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(preview_title)
        
        # Live preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(400)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border-radius: 8px;
                border: 3px solid #667eea;
            }
        """)
        self.preview_label.setText("Live Preview\n(When recording)")
        self.preview_label.setFont(QFont("Arial", 13))
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: #000000;
                border-radius: 8px;
                border: 3px solid #667eea;
                padding: 20px;
            }
        """)
        layout.addWidget(self.preview_label, 1)
        
        # Info box
        info_box = QFrame()
        info_box.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #764ba2;
                border-radius: 8px;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(5)
        
        info_title = QLabel("ℹ️ INFORMATION")
        info_title.setFont(QFont("Arial", 11, QFont.Bold))
        info_title.setStyleSheet("color: #FFFFFF;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "• Click START to begin recording\n"
            "• Configure settings before recording\n"
            "• Live preview shows in this window\n"
            "• Full preview opens in separate window\n"
            "• Videos saved with timestamp\n"
            "• Face blur runs automatically"
        )
        info_text.setFont(QFont("Arial", 9))
        info_text.setStyleSheet("color: #CCCCCC;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        panel.setLayout(layout)
        return panel
    
    def create_section_title(self, text):
        """Create a section title label"""
        title = QLabel(text)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #667eea; padding: 10px 0px 5px 0px;")
        return title
    
    def get_main_stylesheet(self):
        """Main application stylesheet"""
        return """
        QMainWindow {
            background-color: #0d0d0d;
        }
        QWidget {
            background-color: #0d0d0d;
        }
        """
    
    def get_combo_stylesheet(self):
        """Stylesheet for combo boxes"""
        return """
        QComboBox {
            background-color: #1a1a1a;
            color: #FFFFFF;
            border: 2px solid #667eea;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
        }
        QComboBox:hover {
            background-color: #252525;
            border: 2px solid #764ba2;
        }
        QComboBox:focus {
            border: 2px solid #764ba2;
            outline: none;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #667eea;
        }
        QComboBox QAbstractItemView {
            background-color: #1a1a1a;
            color: #FFFFFF;
            selection-background-color: #667eea;
            border: 1px solid #667eea;
        }
        """
    
    def get_spinbox_stylesheet(self):
        """Stylesheet for spinboxes"""
        return """
        QSpinBox {
            background-color: #1a1a1a;
            color: #FFFFFF;
            border: 2px solid #667eea;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
        }
        QSpinBox:hover {
            background-color: #252525;
            border: 2px solid #764ba2;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #667eea;
            border: 1px solid #667eea;
            width: 15px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background-color: #764ba2;
        }
        """
    
    def get_checkbox_stylesheet(self):
        """Stylesheet for checkboxes"""
        return """
        QCheckBox {
            color: #FFFFFF;
            spacing: 10px;
            padding: 5px;
        }
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border-radius: 5px;
            border: 2px solid #667eea;
            background-color: #1a1a1a;
        }
        QCheckBox::indicator:hover {
            border: 2px solid #764ba2;
            background-color: #252525;
        }
        QCheckBox::indicator:checked {
            background-color: #667eea;
            border: 2px solid #764ba2;
        }
        QCheckBox::indicator:checked:hover {
            background-color: #764ba2;
        }
        """
    
    def get_start_button_stylesheet(self):
        """Stylesheet for start button"""
        return """
        QPushButton {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: #FFFFFF;
            border: 2px solid #3d8b40;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
            border: 2px solid #2e7d35;
        }
        QPushButton:pressed {
            background: linear-gradient(135deg, #3d8b40 0%, #2e7d35 100%);
        }
        QPushButton:disabled {
            background: #555555;
            color: #888888;
            border: 2px solid #444444;
        }
        """
    
    def get_stop_button_stylesheet(self):
        """Stylesheet for stop button"""
        return """
        QPushButton {
            background: linear-gradient(135deg, #FF6B6B 0%, #ff5555 100%);
            color: #FFFFFF;
            border: 2px solid #e63946;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover:enabled {
            background: linear-gradient(135deg, #ff5555 0%, #e63946 100%);
            border: 2px solid #d62828;
        }
        QPushButton:pressed {
            background: linear-gradient(135deg, #e63946 0%, #d62828 100%);
        }
        QPushButton:disabled {
            background: #555555;
            color: #888888;
            border: 2px solid #444444;
        }
        """
    
    def setup_signals(self):
        """Setup signal connections"""
        self.recorder_signals.recording_started.connect(self.on_recording_started)
        self.recorder_signals.recording_stopped.connect(self.on_recording_stopped)
        self.recorder_signals.recording_error.connect(self.on_recording_error)
        self.recorder_signals.recording_progress.connect(self.on_recording_progress)
    
    def on_blur_toggled(self, state):
        """Handle blur checkbox toggle"""
        self.blur_enabled = self.blur_checkbox.isChecked()
        status = "✅ Enabled" if self.blur_enabled else "⭕ Disabled"
        self.statusBar().showMessage(f"Face blur {status}")
    
    def apply_face_blur(self, frame):
        """Detect faces and blur them in the frame"""
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
    
    def get_screen_resolution(self):
        """Get the selected screen resolution"""
        res = self.resolution_combo.currentText()
        width, height = map(int, res.split('x'))
        return width, height
    
    def start_recording(self):
        """Start screen recording"""
        self.recording = True
        self.frame_count = 0
        self.detect_frame_idx = 0
        self.start_time = datetime.now()
        
        # Disable/enable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resolution_combo.setEnabled(False)
        self.fps_spinbox.setEnabled(False)
        self.blur_checkbox.setEnabled(False)
        
        # Update UI
        self.status_label.setText("🔴 RECORDING")
        self.status_label.setStyleSheet("color: #FF6B6B; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border: 2px solid #FF6B6B;")
        
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
            width, height = self.get_screen_resolution()
            fps = self.fps_spinbox.value()
            frame_duration = 1.0 / fps
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.recordings_dir / f"recording_{timestamp}.mp4"
            
            self.out = cv2.VideoWriter(str(output_file), fourcc, fps, (width, height))
            
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
                self.recorder_signals.recording_progress.emit(self.frame_count)
                
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
        
        self.preview_window.hide()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resolution_combo.setEnabled(True)
        self.fps_spinbox.setEnabled(True)
        self.blur_checkbox.setEnabled(True)
        
        self.status_label.setText("✅ STOPPED")
        self.status_label.setStyleSheet("color: #FFA500; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border: 2px solid #FFA500;")
        self.preview_label.setText("Live Preview\n(When recording)")
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: #000000;
                border-radius: 8px;
                border: 3px solid #667eea;
                padding: 20px;
            }
        """)
        
        self.recorder_signals.recording_stopped.emit()
    
    def update_timer(self):
        """Update the timer display"""
        if self.recording and self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.setText(f"Recording Time: {time_str}")
            self.frame_label.setText(f"Frames Captured: {self.frame_count}")
            
            # Update file size if available
            try:
                # Estimate file size (rough calculation)
                width, height = self.get_screen_resolution()
                estimated_size = (self.frame_count * width * height * 3) / (1024 * 1024)
                self.file_label.setText(f"Estimated Size: {estimated_size:.1f} MB")
            except:
                pass
    
    def on_recording_started(self):
        """Handle recording started signal"""
        self.statusBar().showMessage("📹 Recording started...")
    
    def on_recording_stopped(self):
        """Handle recording stopped signal"""
        self.statusBar().showMessage(f"✅ Recording completed. {self.frame_count} frames saved.")
    
    def on_recording_progress(self, frame_count):
        """Handle recording progress signal"""
        pass
    
    def on_recording_error(self, error_msg):
        """Handle recording error signal"""
        self.status_label.setText(f"❌ ERROR")
        self.status_label.setStyleSheet("color: #FF0000; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border: 2px solid #FF0000;")
        self.stop_recording()
    
    def signal_preview_update(self):
        """Update live preview window with latest frame"""
        try:
            with self.frame_lock:
                if self.latest_frame is not None:
                    frame = self.latest_frame.copy()
                    self.preview_window.update_frame(frame)
        except Exception as e:
            pass
    
    def update_preview(self):
        """Update live preview during recording"""
        try:
            import mss
            sct = mss.mss()
            monitor = sct.monitors[1]
            
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            preview_width = 480
            preview_height = 270
            if (frame.shape[1], frame.shape[0]) != (preview_width, preview_height):
                frame = cv2.resize(frame, (preview_width, preview_height))
            
            frame = self.apply_face_blur(frame)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            self.preview_label.setPixmap(pixmap)
            
            sct.close()
        except Exception as e:
            pass
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.recording:
            self.stop_recording()
        self.timer.stop()
        self.preview_timer.stop()
        self.preview_signal_timer.stop()
        self.preview_window.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    recorder = ScreenRecorder()
    recorder.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
