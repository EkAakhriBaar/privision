"""
Settings Window Component - Separate window for advanced settings
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QCheckBox, QPushButton,
    QFrame, QTabWidget, QWidget, QSlider, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from styles.modern_styles import (
    get_card_style, get_combobox_style, get_spinbox_style,
    get_checkbox_style, get_button_primary, get_button_danger,
    COLORS, SPACING, FONTS, RADIUS
)


class SettingsWindow(QDialog):
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize settings window UI"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("⚙️ Application Settings")
        header.setFont(QFont(FONTS['family_primary'], 22, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 12px 0;")
        layout.addWidget(header)
        
        # Tab widget for organized settings
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                background-color: {COLORS['bg_card']};
                padding: 16px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_secondary']};
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: {RADIUS['md']};
                border-top-right-radius: {RADIUS['md']};
                font-size: 14px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        
        # Video Settings Tab
        video_tab = self.create_video_settings_tab()
        tabs.addTab(video_tab, "🎥 Video")
        
        # Privacy Settings Tab
        privacy_tab = self.create_privacy_settings_tab()
        tabs.addTab(privacy_tab, "🔐 Privacy")
        
        # Advanced Settings Tab
        advanced_tab = self.create_advanced_settings_tab()
        tabs.addTab(advanced_tab, "⚡ Advanced")
        
        layout.addWidget(tabs)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        cancel_btn.setFixedHeight(48)
        cancel_btn.setFixedWidth(140)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_secondary']};
                border-color: {COLORS['primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        save_btn.setFixedHeight(48)
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet(get_button_primary())
        save_btn.clicked.connect(self.save_settings)
        save_btn.setCursor(Qt.PointingHandCursor)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_video_settings_tab(self):
        """Create video settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Resolution group
        res_group = QGroupBox("Video Resolution")
        res_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        res_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
                font-size: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        res_layout = QVBoxLayout()
        res_layout.setSpacing(12)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["3840x2160 (4K)", "1920x1080 (Full HD)", "1280x720 (HD)", "1024x768", "800x600"])
        self.resolution_combo.setCurrentText("1920x1080 (Full HD)")
        self.resolution_combo.setStyleSheet(get_combobox_style())
        self.resolution_combo.setFont(QFont(FONTS['family_primary'], 13))
        self.resolution_combo.setMinimumHeight(48)
        
        res_desc = QLabel("Higher resolution = better quality but larger file size")
        res_desc.setFont(QFont(FONTS['family_primary'], 11))
        res_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        res_layout.addWidget(self.resolution_combo)
        res_layout.addWidget(res_desc)
        res_group.setLayout(res_layout)
        layout.addWidget(res_group)
        
        # FPS group
        fps_group = QGroupBox("Frame Rate (FPS)")
        fps_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        fps_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        fps_layout = QVBoxLayout()
        fps_layout.setSpacing(12)
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(10, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")
        self.fps_spinbox.setStyleSheet(get_spinbox_style())
        self.fps_spinbox.setFont(QFont(FONTS['family_primary'], 13))
        self.fps_spinbox.setMinimumHeight(48)
        
        fps_desc = QLabel("Higher FPS = smoother video (30 FPS recommended)")
        fps_desc.setFont(QFont(FONTS['family_primary'], 11))
        fps_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        fps_layout.addWidget(self.fps_spinbox)
        fps_layout.addWidget(fps_desc)
        fps_group.setLayout(fps_layout)
        layout.addWidget(fps_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_privacy_settings_tab(self):
        """Create privacy settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Face blur group
        blur_group = QGroupBox("Face Blur Protection")
        blur_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        blur_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        blur_layout = QVBoxLayout()
        blur_layout.setSpacing(16)
        
        self.blur_checkbox = QCheckBox("Enable automatic face blurring")
        self.blur_checkbox.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.blur_checkbox.setStyleSheet(get_checkbox_style())
        self.blur_checkbox.setChecked(False)
        
        blur_desc = QLabel("Automatically detects and blurs faces in recordings for privacy protection")
        blur_desc.setFont(QFont(FONTS['family_primary'], 11))
        blur_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        blur_desc.setWordWrap(True)
        
        # Blur intensity slider
        intensity_label = QLabel("Blur Intensity: Medium")
        intensity_label.setFont(QFont(FONTS['family_primary'], 12))
        intensity_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(1, 5)
        self.blur_slider.setValue(3)
        self.blur_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 8px;
                background: {COLORS['bg_secondary']};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['primary_light']};
            }}
        """)
        
        blur_layout.addWidget(self.blur_checkbox)
        blur_layout.addWidget(blur_desc)
        blur_layout.addWidget(intensity_label)
        blur_layout.addWidget(self.blur_slider)
        blur_group.setLayout(blur_layout)
        layout.addWidget(blur_group)
        
        # Sensitive content blur group
        sensitive_group = QGroupBox("Sensitive Content Protection")
        sensitive_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        sensitive_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        sensitive_layout = QVBoxLayout()
        sensitive_layout.setSpacing(16)
        
        self.sensitive_blur_checkbox = QCheckBox("Enable sensitive content blurring")
        self.sensitive_blur_checkbox.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        self.sensitive_blur_checkbox.setStyleSheet(get_checkbox_style())
        self.sensitive_blur_checkbox.setChecked(False)
        
        sensitive_desc = QLabel("Automatically detects and blurs email addresses, phone numbers, API keys, credit cards, and other sensitive information")
        sensitive_desc.setFont(QFont(FONTS['family_primary'], 11))
        sensitive_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        sensitive_desc.setWordWrap(True)
        
        sensitive_layout.addWidget(self.sensitive_blur_checkbox)
        sensitive_layout.addWidget(sensitive_desc)
        sensitive_group.setLayout(sensitive_layout)
        layout.addWidget(sensitive_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_settings_tab(self):
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Audio settings
        audio_group = QGroupBox("Audio Settings")
        audio_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        audio_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(12)
        
        self.audio_checkbox = QCheckBox("Record system audio (Coming Soon)")
        self.audio_checkbox.setFont(QFont(FONTS['family_primary'], 13))
        self.audio_checkbox.setStyleSheet(get_checkbox_style())
        self.audio_checkbox.setEnabled(False)
        
        audio_desc = QLabel("Capture system audio along with screen recording")
        audio_desc.setFont(QFont(FONTS['family_primary'], 11))
        audio_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        audio_layout.addWidget(self.audio_checkbox)
        audio_layout.addWidget(audio_desc)
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Performance settings
        perf_group = QGroupBox("Performance")
        perf_group.setFont(QFont(FONTS['family_primary'], 14, QFont.Bold))
        perf_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        perf_layout = QVBoxLayout()
        perf_layout.setSpacing(12)
        
        self.hardware_checkbox = QCheckBox("Use hardware acceleration (Recommended)")
        self.hardware_checkbox.setFont(QFont(FONTS['family_primary'], 13))
        self.hardware_checkbox.setStyleSheet(get_checkbox_style())
        self.hardware_checkbox.setChecked(True)
        
        perf_desc = QLabel("Use GPU for better performance and lower CPU usage")
        perf_desc.setFont(QFont(FONTS['family_primary'], 11))
        perf_desc.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
        
        perf_layout.addWidget(self.hardware_checkbox)
        perf_layout.addWidget(perf_desc)
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def save_settings(self):
        """Save settings and close"""
        self.settings_saved.emit()
        self.accept()
    
    def get_resolution(self):
        """Get selected resolution"""
        res_text = self.resolution_combo.currentText()
        res = res_text.split(' ')[0]  # Extract resolution part
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
