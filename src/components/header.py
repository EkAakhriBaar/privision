"""
Header Component - Top banner with branding
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from styles.modern_styles import get_header_style, COLORS, SPACING, FONTS


class HeaderComponent(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize header UI"""
        self.setStyleSheet(get_header_style())
        self.setFixedHeight(110)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(6)
        
        # Title
        title = QLabel("📹 SCREEN RECORDER PRO")
        title.setFont(QFont(FONTS['family_primary'], 28, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; letter-spacing: 1px;")
        
        # Subtitle
        subtitle = QLabel("Professional Screen Sharing & Recording Solution")
        subtitle.setFont(QFont(FONTS['family_primary'], 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_primary']}; opacity: 0.9; border: none;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.setLayout(layout)
