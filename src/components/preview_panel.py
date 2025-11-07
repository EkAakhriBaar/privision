"""
Preview Panel Component - Live video preview
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt
import cv2
from styles.modern_styles import (
    get_card_style, get_preview_frame,
    COLORS, SPACING, FONTS
)


class PreviewPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize preview panel UI"""
        self.setStyleSheet(get_card_style())
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("👁️  Live Preview")
        title.setFont(QFont(FONTS['family_primary'], 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-bottom: 8px;")
        layout.addWidget(title)
        
        # Preview frame
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(350)
        self.preview_label.setStyleSheet(get_preview_frame())
        self.preview_label.setText("Live Preview\n\nWill appear when recording starts")
        self.preview_label.setFont(QFont(FONTS['family_primary'], 12))
        preview_text_style = f"""
            QLabel {{
                color: {COLORS['text_muted']};
                background-color: #000000;
                border: 2px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 20px;
            }}
        """
        self.preview_label.setStyleSheet(preview_text_style)
        layout.addWidget(self.preview_label, 1)
        
        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['primary']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        info_title = QLabel("ℹ️  Quick Guide")
        info_title.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        info_title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        
        info_text = QLabel(
            "• Configure settings before starting\n"
            "• Click START to begin recording\n"
            "• Preview shows in this window\n"
            "• Full preview opens separately\n"
            "• Videos auto-saved with timestamp"
        )
        info_text.setFont(QFont(FONTS['family_primary'], 10))
        info_text.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)
        
        self.setLayout(layout)
    
    def update_preview(self, frame):
        """Update preview with new frame"""
        try:
            # Resize frame for preview
            preview_height = 350
            h, w = frame.shape[:2]
            preview_width = int(w * (preview_height / h))
            frame_resized = cv2.resize(frame, (preview_width, preview_height))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Display
            pixmap = QPixmap.fromImage(qt_image)
            self.preview_label.setPixmap(pixmap)
        except Exception as e:
            pass
    
    def clear_preview(self):
        """Clear preview and show placeholder text"""
        self.preview_label.clear()
        self.preview_label.setText("Live Preview\n\nWill appear when recording starts")
        preview_text_style = f"""
            QLabel {{
                color: {COLORS['text_muted']};
                background-color: #000000;
                border: 2px solid {COLORS['border_primary']};
                border-radius: 8px;
                padding: 20px;
            }}
        """
        self.preview_label.setStyleSheet(preview_text_style)
