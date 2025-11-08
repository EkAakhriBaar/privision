"""
Video Processing Panel - UI for selecting and processing videos with blur effects
"""
import os
import threading
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QProgressBar, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from styles.modern_styles import COLORS, SPACING, FONTS


class ProcessorSignals(QObject):
    """Signals for video processing events"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    processing_completed = pyqtSignal(str)
    processing_failed = pyqtSignal(str)


class VideoProcessingPanel(QFrame):
    """Panel for video processing with blur settings"""
    
    def __init__(self, recordings_dir, processed_dir):
        super().__init__()
        self.recordings_dir = Path(recordings_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.video_processor = None
        self.processing_thread = None
        self.selected_video = None
        
        # Signals
        self.signals = ProcessorSignals()
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.status_updated.connect(self.update_status)
        self.signals.processing_completed.connect(self.on_processing_completed)
        self.signals.processing_failed.connect(self.on_processing_failed)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: 12px;
                padding: 24px;
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                border: none;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_muted']};
            }}
            QComboBox {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QCheckBox {{
                color: {COLORS['text_primary']};
                spacing: 10px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {COLORS['border_primary']};
                background-color: {COLORS['bg_secondary']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
            QProgressBar {{
                border: 2px solid {COLORS['border_primary']};
                border-radius: 8px;
                background-color: {COLORS['bg_secondary']};
                text-align: center;
                color: {COLORS['text_primary']};
                font-weight: bold;
                font-size: 13px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🎬  Video Processing Center")
        title.setFont(QFont(FONTS['family_primary'], 18, QFont.Bold))
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Select a video and apply face blur or sensitive data blur")
        desc.setFont(QFont(FONTS['family_primary'], 12))
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # Video selection
        video_layout = QHBoxLayout()
        video_layout.setSpacing(15)
        
        video_label = QLabel("Select Video:")
        video_label.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        video_layout.addWidget(video_label)
        
        self.video_combo = QComboBox()
        self.video_combo.setFont(QFont(FONTS['family_primary'], 12))
        self.video_combo.setMinimumHeight(45)
        self.video_combo.currentTextChanged.connect(self.on_video_selected)
        video_layout.addWidget(self.video_combo, 1)
        
        self.browse_btn = QPushButton("� Browse...")
        self.browse_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.browse_btn.setFixedHeight(45)
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.clicked.connect(self.browse_video)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        video_layout.addWidget(self.browse_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.refresh_btn.setFixedHeight(45)
        self.refresh_btn.setFixedWidth(60)
        self.refresh_btn.clicked.connect(self.load_videos)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        video_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(video_layout)
        
        # Processing settings
        settings_label = QLabel("⚙️ Processing Settings:")
        settings_label.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        layout.addWidget(settings_label)
        
        # Checkboxes
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(12)
        
        self.face_blur_checkbox = QCheckBox("🔒 Enable Face Blur")
        self.face_blur_checkbox.setFont(QFont(FONTS['family_primary'], 13))
        self.face_blur_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.face_blur_checkbox)
        
        self.sensitive_blur_checkbox = QCheckBox("🔐 Enable Sensitive Data Blur (OCR)")
        self.sensitive_blur_checkbox.setFont(QFont(FONTS['family_primary'], 13))
        self.sensitive_blur_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.sensitive_blur_checkbox)
        
        layout.addLayout(checkbox_layout)
        
        layout.addSpacing(10)
        
        # Process button
        self.process_btn = QPushButton("🚀 Process Video")
        self.process_btn.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        self.process_btn.setMinimumHeight(55)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setCursor(Qt.PointingHandCursor)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("❌ Cancel Processing")
        self.cancel_btn.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #dc2626;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
        """)
        self.cancel_btn.setVisible(False)
        layout.addWidget(self.cancel_btn)
        
        # Progress bar
        progress_label = QLabel("📊 Processing Progress:")
        progress_label.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(35)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("ℹ️ Ready to process")
        self.status_label.setFont(QFont(FONTS['family_primary'], 12))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Open processed folder button
        self.open_folder_btn = QPushButton("📁 Open Processed Videos Folder")
        self.open_folder_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.open_folder_btn.setMinimumHeight(45)
        self.open_folder_btn.clicked.connect(self.open_processed_folder)
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_primary']};
            }}
        """)
        layout.addWidget(self.open_folder_btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Load videos
        self.load_videos()
    
    def load_videos(self):
        """Load available videos from recordings directory"""
        self.video_combo.clear()
        
        if not self.recordings_dir.exists():
            self.video_combo.addItem("No recordings found")
            return
        
        # Get all MP4 files
        video_files = sorted(self.recordings_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True)
        
        if not video_files:
            self.video_combo.addItem("No recordings found")
            self.process_btn.setEnabled(False)
        else:
            self.video_combo.addItem("-- Select a video --")
            for video_file in video_files:
                self.video_combo.addItem(video_file.name)
            self.process_btn.setEnabled(False)
    
    def browse_video(self):
        """Browse for a video file from anywhere on the device"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            str(Path.home()),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;All Files (*.*)"
        )
        
        if file_path:
            self.selected_video = Path(file_path)
            # Add to combo box if not already there
            video_name = f"📂 {self.selected_video.name}"
            
            # Check if already in combo
            found = False
            for i in range(self.video_combo.count()):
                if self.video_combo.itemText(i) == video_name:
                    found = True
                    self.video_combo.setCurrentIndex(i)
                    break
            
            if not found:
                self.video_combo.addItem(video_name)
                self.video_combo.setCurrentText(video_name)
            
            self.process_btn.setEnabled(True)
            self.status_label.setText(f"✅ Selected: {self.selected_video.name}")
    
    def on_video_selected(self, video_name):
        """Handle video selection"""
        if video_name and video_name != "-- Select a video --" and video_name != "No recordings found":
            # Check if it's a browsed file
            if video_name.startswith("📂 "):
                # Keep current selected_video (already set by browse_video)
                pass
            else:
                self.selected_video = self.recordings_dir / video_name
            
            self.process_btn.setEnabled(True)
            self.status_label.setText(f"✅ Selected: {video_name}")
        else:
            self.selected_video = None
            self.process_btn.setEnabled(False)
            self.status_label.setText("ℹ️ Ready to process")
    
    def start_processing(self):
        """Start video processing in a separate thread"""
        if not self.selected_video or not self.selected_video.exists():
            QMessageBox.warning(self, "No Video", "Please select a video to process.")
            return
        
        # Get settings
        enable_face_blur = self.face_blur_checkbox.isChecked()
        enable_sensitive_blur = self.sensitive_blur_checkbox.isChecked()
        
        if not enable_face_blur and not enable_sensitive_blur:
            QMessageBox.warning(self, "No Effects", "Please enable at least one blur effect.")
            return
        
        # Disable UI during processing
        self.video_combo.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.face_blur_checkbox.setEnabled(False)
        self.sensitive_blur_checkbox.setEnabled(False)
        self.process_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Import video processor
        from core.video_processor import VideoProcessor
        self.video_processor = VideoProcessor()
        self.video_processor.set_callbacks(
            progress_callback=lambda p: self.signals.progress_updated.emit(p),
            status_callback=lambda s: self.signals.status_updated.emit(s)
        )
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_video_thread,
            args=(enable_face_blur, enable_sensitive_blur),
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_video_thread(self, enable_face_blur, enable_sensitive_blur):
        """Processing thread function"""
        try:
            output_file = self.video_processor.process_video(
                input_video_path=str(self.selected_video),
                output_dir=str(self.processed_dir),
                enable_face_blur=enable_face_blur,
                enable_sensitive_blur=enable_sensitive_blur
            )
            
            if output_file:
                self.signals.processing_completed.emit(output_file)
            else:
                self.signals.processing_failed.emit("Processing was cancelled or failed")
        
        except Exception as e:
            self.signals.processing_failed.emit(str(e))
    
    def cancel_processing(self):
        """Cancel ongoing video processing"""
        if self.video_processor:
            self.video_processor.stop_processing()
            self.status_label.setText("⚠️ Cancelling processing...")
    
    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar.setValue(progress)
    
    def update_status(self, status_text):
        """Update status label"""
        self.status_label.setText(status_text)
    
    def on_processing_completed(self, output_file):
        """Handle successful processing completion"""
        # Re-enable UI
        self.video_combo.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.face_blur_checkbox.setEnabled(True)
        self.sensitive_blur_checkbox.setEnabled(True)
        self.process_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setValue(100)
        
        # Show success message
        output_path = Path(output_file)
        QMessageBox.information(
            self,
            "✅ Processing Complete",
            f"Video processed successfully!\n\nOutput: {output_path.name}\n\nLocation: {self.processed_dir}"
        )
        
        self.status_label.setText(f"✅ Completed: {output_path.name}")
    
    def on_processing_failed(self, error_msg):
        """Handle processing failure"""
        # Re-enable UI
        self.video_combo.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.face_blur_checkbox.setEnabled(True)
        self.sensitive_blur_checkbox.setEnabled(True)
        self.process_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        
        # Show error message
        QMessageBox.critical(
            self,
            "❌ Processing Failed",
            f"Failed to process video:\n\n{error_msg}"
        )
        
        self.status_label.setText(f"❌ Error: {error_msg}")
    
    def open_processed_folder(self):
        """Open the processed recordings folder in file explorer"""
        import subprocess
        import platform
        
        if platform.system() == 'Windows':
            os.startfile(str(self.processed_dir))
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', str(self.processed_dir)])
        else:  # Linux
            subprocess.Popen(['xdg-open', str(self.processed_dir)])
