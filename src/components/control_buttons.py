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
