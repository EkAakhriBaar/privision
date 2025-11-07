"""
Status Panel Component - Display recording status and statistics
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from styles.modern_styles import (
    get_card_style, get_status_badge, get_stat_label,
    COLORS, SPACING, FONTS
)


class StatusPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize status panel UI"""
        self.setStyleSheet(get_card_style())
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Section title
        title = QLabel("📊  Statistics & Status")
        title.setFont(QFont(FONTS['family_primary'], 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-bottom: 8px;")
        layout.addWidget(title)
        
        # Status badge
        self.status_label = QLabel("Ready to Record")
        self.status_label.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(get_status_badge('ready'))
        self.status_label.setFixedHeight(50)
        layout.addWidget(self.status_label)
        
        # Statistics
        stats_container = QFrame()
        stats_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-radius: 8px;
                padding: 16px;
                border: none;
            }}
        """)
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)
        
        # Recording time
        self.time_label = QLabel("Recording Time: 00:00:00")
        self.time_label.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.time_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        stats_layout.addWidget(self.time_label)
        
        # Frame count
        self.frame_label = QLabel("Frames Captured: 0")
        self.frame_label.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.frame_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        stats_layout.addWidget(self.frame_label)
        
        # File size
        self.size_label = QLabel("Estimated Size: 0 MB")
        self.size_label.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        self.size_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        stats_layout.addWidget(self.size_label)
        
        stats_container.setLayout(stats_layout)
        layout.addWidget(stats_container)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_status(self, status_text, status_type='ready'):
        """Update status badge"""
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(get_status_badge(status_type))
    
    def update_time(self, time_str):
        """Update recording time"""
        self.time_label.setText(f"Recording Time: {time_str}")
    
    def update_frames(self, frame_count):
        """Update frame count"""
        self.frame_label.setText(f"Frames Captured: {frame_count:,}")
    
    def update_size(self, size_mb):
        """Update file size"""
        self.size_label.setText(f"Estimated Size: {size_mb:.1f} MB")
