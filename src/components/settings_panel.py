"""
Settings Panel Component - Recording configuration
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from styles.modern_styles import (
    get_card_style, get_combobox_style, get_spinbox_style,
    get_checkbox_style, COLORS, SPACING, FONTS
)


class SettingsPanel(QFrame):
    blur_toggled = pyqtSignal(bool)
    sensitive_content_blur_toggled = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize settings panel UI"""
        self.setStyleSheet(get_card_style())
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Section title
        title = QLabel("⚙️  Recording Settings")
        title.setFont(QFont(FONTS['family_primary'], 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding-bottom: 8px;")
        layout.addWidget(title)
        
        # Resolution setting
        res_container = self.create_setting_row(
            "Resolution",
            "Select video output resolution"
        )
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768", "800x600"])
        self.resolution_combo.setCurrentText("1920x1080")
        self.resolution_combo.setStyleSheet(get_combobox_style())
        res_container.layout().addWidget(self.resolution_combo)
        layout.addWidget(res_container)
        
        # FPS setting
        fps_container = self.create_setting_row(
            "Frame Rate",
            "Higher FPS = smoother video (10-60)"
        )
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(10, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")
        self.fps_spinbox.setStyleSheet(get_spinbox_style())
        fps_container.layout().addWidget(self.fps_spinbox)
        layout.addWidget(fps_container)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['border_primary']}; border: none; max-height: 1px; margin: 8px 0;")
        layout.addWidget(divider)
        
        # Privacy section
        privacy_title = QLabel("🔐  Privacy Settings")
        privacy_title.setFont(QFont(FONTS['family_primary'], 16, QFont.Bold))
        privacy_title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; padding: 8px 0;")
        layout.addWidget(privacy_title)
        
        # Face blur option
        blur_frame = QFrame()
        blur_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        blur_layout = QVBoxLayout()
        blur_layout.setContentsMargins(0, 0, 0, 0)
        blur_layout.setSpacing(8)
        
        self.blur_checkbox = QCheckBox("Enable Face Blur Protection")
        self.blur_checkbox.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.blur_checkbox.setStyleSheet(get_checkbox_style())
        self.blur_checkbox.setChecked(False)
        self.blur_checkbox.stateChanged.connect(lambda: self.blur_toggled.emit(self.blur_checkbox.isChecked()))
        
        blur_desc = QLabel("Automatically detects and blurs faces for privacy")
        blur_desc.setFont(QFont(FONTS['family_primary'], 10))
        blur_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        blur_layout.addWidget(self.blur_checkbox)
        blur_layout.addWidget(blur_desc)
        blur_frame.setLayout(blur_layout)
        layout.addWidget(blur_frame)
        
        # Sensitive content blur option
        sensitive_frame = QFrame()
        sensitive_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        sensitive_layout = QVBoxLayout()
        sensitive_layout.setContentsMargins(0, 0, 0, 0)
        sensitive_layout.setSpacing(8)
        
        self.sensitive_blur_checkbox = QCheckBox("Blur Sensitive Content")
        self.sensitive_blur_checkbox.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.sensitive_blur_checkbox.setStyleSheet(get_checkbox_style())
        self.sensitive_blur_checkbox.setChecked(False)
        self.sensitive_blur_checkbox.stateChanged.connect(lambda: self.sensitive_content_blur_toggled.emit(self.sensitive_blur_checkbox.isChecked()))
        
        sensitive_desc = QLabel("Automatically detects and blurs email, phone, API keys, credit cards, and other sensitive information")
        sensitive_desc.setFont(QFont(FONTS['family_primary'], 10))
        sensitive_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        sensitive_desc.setWordWrap(True)
        
        sensitive_layout.addWidget(self.sensitive_blur_checkbox)
        sensitive_layout.addWidget(sensitive_desc)
        sensitive_frame.setLayout(sensitive_layout)
        layout.addWidget(sensitive_frame)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_setting_row(self, label_text, description):
        """Create a setting row with label and description"""
        container = QFrame()
        container.setStyleSheet("border: none;")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)
        
        label = QLabel(label_text)
        label.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        
        desc = QLabel(description)
        desc.setFont(QFont(FONTS['family_primary'], 10))
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        container_layout.addWidget(label)
        container_layout.addWidget(desc)
        container.setLayout(container_layout)
        
        return container
    
    def get_resolution(self):
        """Get selected resolution"""
        res = self.resolution_combo.currentText()
        width, height = map(int, res.split('x'))
        return width, height
    
    def get_fps(self):
        """Get selected FPS"""
        return self.fps_spinbox.value()
    
    def is_blur_enabled(self):
        """Check if blur is enabled"""
        return self.blur_checkbox.isChecked()
    
    def is_sensitive_content_blur_enabled(self):
        """Check if sensitive content blur is enabled"""
        return self.sensitive_blur_checkbox.isChecked()
    
    def set_enabled(self, enabled):
        """Enable/disable all controls"""
        self.resolution_combo.setEnabled(enabled)
        self.fps_spinbox.setEnabled(enabled)
        self.blur_checkbox.setEnabled(enabled)
        self.sensitive_blur_checkbox.setEnabled(enabled)
