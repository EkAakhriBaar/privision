"""
Video Gallery Component - Display and manage recorded videos
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFileDialog
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
import os
from datetime import datetime
from styles.modern_styles import (
    get_card_style, COLORS, SPACING, FONTS, RADIUS
)


class VideoCard(QFrame):
    """Individual video card"""
    play_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.init_ui()
    
    def init_ui(self):
        """Initialize video card UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['bg_tertiary']};
            }}
        """)
        self.setMinimumHeight(140)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Video info
        video_name = Path(self.video_path).name
        name_label = QLabel(f"📹 {video_name}")
        name_label.setFont(QFont(FONTS['family_primary'], 13, QFont.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # File size and date
        try:
            size_mb = os.path.getsize(self.video_path) / (1024 * 1024)
            mod_time = datetime.fromtimestamp(os.path.getmtime(self.video_path))
            
            info_label = QLabel(f"Size: {size_mb:.1f} MB  |  {mod_time.strftime('%Y-%m-%d %H:%M')}")
            info_label.setFont(QFont(FONTS['family_primary'], 11))
            info_label.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
            layout.addWidget(info_label)
        except:
            pass
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        play_btn = QPushButton("▶ Play")
        play_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        play_btn.setFixedHeight(40)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: {RADIUS['sm']};
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self.video_path))
        play_btn.setCursor(Qt.PointingHandCursor)
        
        open_folder_btn = QPushButton("📁 Folder")
        open_folder_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        open_folder_btn.setFixedHeight(40)
        open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border_primary']};
                border-radius: {RADIUS['sm']};
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['bg_secondary']};
            }}
        """)
        open_folder_btn.clicked.connect(self.open_folder)
        open_folder_btn.setCursor(Qt.PointingHandCursor)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        delete_btn.setFixedHeight(40)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: {RADIUS['sm']};
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger_dark']};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.video_path))
        delete_btn.setCursor(Qt.PointingHandCursor)
        
        button_layout.addWidget(play_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def open_folder(self):
        """Open file location"""
        import subprocess
        folder_path = str(Path(self.video_path).parent)
        if os.name == 'nt':  # Windows
            subprocess.Popen(f'explorer /select,"{self.video_path}"')
        else:
            subprocess.Popen(['xdg-open', folder_path])


class VideoGallery(QFrame):
    """Video gallery panel"""
    
    def __init__(self, recordings_dir):
        super().__init__()
        self.recordings_dir = recordings_dir
        self.init_ui()
    
    def init_ui(self):
        """Initialize gallery UI"""
        self.setStyleSheet(get_card_style())
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🎬 Recorded Videos")
        title.setFont(QFont(FONTS['family_primary'], 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont(FONTS['family_primary'], 12, QFont.Bold))
        refresh_btn.setFixedHeight(42)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: {RADIUS['md']};
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        refresh_btn.clicked.connect(self.load_videos)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for videos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
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
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout()
        self.video_layout.setSpacing(12)
        self.video_layout.setContentsMargins(12, 12, 12, 12)
        self.video_container.setLayout(self.video_layout)
        
        scroll.setWidget(self.video_container)
        layout.addWidget(scroll, 1)
        
        self.setLayout(layout)
        self.load_videos()
    
    def load_videos(self):
        """Load videos from recordings directory"""
        # Clear existing videos
        while self.video_layout.count():
            item = self.video_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get all video files
        video_files = []
        if self.recordings_dir.exists():
            video_files = list(self.recordings_dir.glob("*.mp4"))
            video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if video_files:
            for video_file in video_files:
                card = VideoCard(str(video_file))
                card.play_clicked.connect(self.play_video)
                card.delete_clicked.connect(self.delete_video)
                self.video_layout.addWidget(card)
        else:
            # No videos message
            no_videos = QLabel("No recordings yet.\nStart recording to see your videos here!")
            no_videos.setAlignment(Qt.AlignCenter)
            no_videos.setFont(QFont(FONTS['family_primary'], 13))
            no_videos.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                padding: 40px;
                border: 2px dashed {COLORS['border_primary']};
                border-radius: {RADIUS['md']};
                background-color: {COLORS['bg_secondary']};
            """)
            self.video_layout.addWidget(no_videos)
        
        self.video_layout.addStretch()
    
    def play_video(self, video_path):
        """Play video in default player"""
        import subprocess
        if os.name == 'nt':  # Windows
            os.startfile(video_path)
        elif os.name == 'posix':  # macOS/Linux
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', video_path])
    
    def delete_video(self, video_path):
        """Delete video file"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Delete Video',
            f'Are you sure you want to delete this video?\n\n{Path(video_path).name}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(video_path)
                self.load_videos()  # Refresh list
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Could not delete video:\n{str(e)}')
