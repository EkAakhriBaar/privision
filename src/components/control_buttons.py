"""
Control Buttons Component - Start/Stop recording controls
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from styles.modern_styles import (
    get_button_primary, get_button_danger,
    COLORS, SPACING, FONTS
)

class ControlButtons(QFrame):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    stream_clicked = pyqtSignal(str)  # Pass platform name
    stop_stream_clicked = pyqtSignal()
    
    def __init__(self, recordings_dir):
        super().__init__()
        self.recordings_dir = recordings_dir
        self.init_ui()
    
    def init_ui(self):
        """Initialize control buttons UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_primary']};
                border-radius: 12px;
                padding: 24px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("🎮  Controls")
        title.setFont(QFont(FONTS['family_primary'], 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-bottom: 8px;")
        layout.addWidget(title)
        
        # Start button
        self.start_button = QPushButton("▶  START RECORDING")
        self.start_button.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.start_button.setFixedHeight(56)
        self.start_button.setStyleSheet(get_button_primary())
        self.start_button.clicked.connect(self.start_clicked.emit)
        self.start_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("⏹  STOP RECORDING")
        self.stop_button.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.stop_button.setFixedHeight(56)
        self.stop_button.setStyleSheet(get_button_danger())
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.stop_button)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['border_primary']}; border: none; max-height: 1px; margin: 8px 0;")
        layout.addWidget(divider)
        
        # Streaming section title
        stream_title = QLabel("📡  Live Streaming")
        stream_title.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        stream_title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-top: 8px;")
        layout.addWidget(stream_title)
        
        # YouTube Stream button
        self.stream_youtube_button = QPushButton("�  STREAM TO YOUTUBE")
        self.stream_youtube_button.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.stream_youtube_button.setFixedHeight(50)
        self.stream_youtube_button.setStyleSheet(get_button_primary())
        self.stream_youtube_button.clicked.connect(lambda: self.stream_clicked.emit("youtube"))
        self.stream_youtube_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.stream_youtube_button)
        
        # Facebook Stream button
        self.stream_facebook_button = QPushButton("📘  STREAM TO FACEBOOK")
        self.stream_facebook_button.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.stream_facebook_button.setFixedHeight(50)
        self.stream_facebook_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1877f2, stop:1 #0d5ac9);
                color: white;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #166fe5, stop:1 #0b4fb8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1567d3, stop:1 #0a4ca7);
            }
            QPushButton:disabled {
                background: #4a5568;
                color: #9ca3af;
            }
        """)
        self.stream_facebook_button.clicked.connect(lambda: self.stream_clicked.emit("facebook"))
        self.stream_facebook_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.stream_facebook_button)
        
        # Twitch Stream button
        self.stream_twitch_button = QPushButton("🎮  STREAM TO TWITCH")
        self.stream_twitch_button.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.stream_twitch_button.setFixedHeight(50)
        self.stream_twitch_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9146ff, stop:1 #7728d8);
                color: white;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8839f2, stop:1 #6d1fd1);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7f2de5, stop:1 #6316ca);
            }
            QPushButton:disabled {
                background: #4a5568;
                color: #9ca3af;
            }
        """)
        self.stream_twitch_button.clicked.connect(lambda: self.stream_clicked.emit("twitch"))
        self.stream_twitch_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.stream_twitch_button)
        
        # Stop stream button
        self.stop_stream_button = QPushButton("⏹  STOP LIVE STREAM")
        self.stop_stream_button.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.stop_stream_button.setFixedHeight(56)
        self.stop_stream_button.setStyleSheet(get_button_danger())
        self.stop_stream_button.setEnabled(False)
        self.stop_stream_button.clicked.connect(self.stop_stream_clicked.emit)
        self.stop_stream_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.stop_stream_button)
        
        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background-color: {COLORS['border_primary']}; border: none; max-height: 1px; margin: 8px 0;")
        layout.addWidget(divider2)
        
        # Output directory info
        output_title = QLabel("💾  Output Location")
        output_title.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        output_title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        layout.addWidget(output_title)
        
        output_path = QLabel(f"📁 {self.recordings_dir}")
        output_path.setFont(QFont(FONTS['family_primary'], 10))
        output_path.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        output_path.setWordWrap(True)
        layout.addWidget(output_path)
        
        self.setLayout(layout)
    
    def set_recording_state(self, is_recording):
        """Update button states based on recording status"""
        self.start_button.setEnabled(not is_recording)
        self.stop_button.setEnabled(is_recording)
    
    def set_streaming_state(self, is_streaming):
        """Update button states based on streaming status"""
        self.stream_youtube_button.setEnabled(not is_streaming)
        self.stream_facebook_button.setEnabled(not is_streaming)
        self.stream_twitch_button.setEnabled(not is_streaming)
        self.stop_stream_button.setEnabled(is_streaming)
