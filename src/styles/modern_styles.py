"""
Modern Tailwind-inspired styles for Screen Recorder
Clean, professional design with proper spacing, padding, and margins
"""

# Color Palette - Modern Design System
COLORS = {
    # Primary Colors
    'primary': '#6366F1',        # Indigo-500
    'primary_dark': '#4F46E5',   # Indigo-600
    'primary_light': '#818CF8',  # Indigo-400
    
    # Secondary Colors
    'secondary': '#8B5CF6',      # Violet-500
    'secondary_dark': '#7C3AED', # Violet-600
    
    # Success
    'success': '#10B981',        # Emerald-500
    'success_dark': '#059669',   # Emerald-600
    
    # Danger
    'danger': '#EF4444',         # Red-500
    'danger_dark': '#DC2626',    # Red-600
    
    # Warning
    'warning': '#F59E0B',        # Amber-500
    'warning_dark': '#D97706',   # Amber-600
    
    # Neutrals
    'bg_primary': '#0F172A',     # Slate-900
    'bg_secondary': '#1E293B',   # Slate-800
    'bg_tertiary': '#334155',    # Slate-700
    'bg_card': '#1E293B',        # Slate-800
    
    # Text Colors
    'text_primary': '#F8FAFC',   # Slate-50
    'text_secondary': '#CBD5E1',  # Slate-300
    'text_muted': '#94A3B8',     # Slate-400
    
    # Border Colors
    'border_primary': '#334155',  # Slate-700
    'border_focus': '#6366F1',    # Indigo-500
}


# Spacing System (following Tailwind convention)
SPACING = {
    '0': '0px',
    '1': '4px',
    '2': '8px',
    '3': '12px',
    '4': '16px',
    '5': '20px',
    '6': '24px',
    '8': '32px',
    '10': '40px',
    '12': '48px',
    '16': '64px',
    '20': '80px',
}


# Typography
FONTS = {
    'family_primary': 'Segoe UI, Arial, sans-serif',
    'family_mono': 'Consolas, monospace',
    
    'size_xs': '11px',
    'size_sm': '13px',
    'size_base': '15px',
    'size_lg': '17px',
    'size_xl': '22px',
    'size_2xl': '26px',
    'size_3xl': '32px',
    'size_4xl': '40px',
}


# Border Radius
RADIUS = {
    'none': '0px',
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    'full': '9999px',
}


# Shadows (Tailwind-inspired)
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
}


def get_main_window_style():
    """Main window background"""
    return f"""
        QMainWindow {{
            background-color: {COLORS['bg_primary']};
        }}
        QWidget {{
            background-color: {COLORS['bg_primary']};
            font-family: {FONTS['family_primary']};
            font-size: {FONTS['size_base']};
        }}
        QStatusBar {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_secondary']};
            border-top: 1px solid {COLORS['border_primary']};
            padding: {SPACING['2']};
        }}
    """


def get_header_style():
    """Header with gradient"""
    return f"""
        QFrame {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['primary']},
                stop:1 {COLORS['secondary']}
            );
            border: none;
            border-bottom: 2px solid {COLORS['primary_dark']};
        }}
    """


def get_card_style():
    """Card/Panel style"""
    return f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['6']};
        }}
    """


def get_button_primary():
    """Primary action button"""
    return f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: {COLORS['text_primary']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['3']} {SPACING['6']};
            font-size: {FONTS['size_base']};
            font-weight: 600;
            min-height: 48px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['success_dark']};
        }}
        QPushButton:pressed {{
            background-color: #047857;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}
    """


def get_button_danger():
    """Danger/Stop button"""
    return f"""
        QPushButton {{
            background-color: {COLORS['danger']};
            color: {COLORS['text_primary']};
            border: none;
            border-radius: {RADIUS['md']};
            padding: {SPACING['3']} {SPACING['6']};
            font-size: {FONTS['size_base']};
            font-weight: 600;
            min-height: 48px;
        }}
        QPushButton:hover:enabled {{
            background-color: {COLORS['danger_dark']};
        }}
        QPushButton:pressed {{
            background-color: #B91C1C;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
        }}
    """


def get_combobox_style():
    """Dropdown/Select style"""
    return f"""
        QComboBox {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['2']} {SPACING['4']};
            font-size: {FONTS['size_base']};
            min-height: 40px;
        }}
        QComboBox:hover {{
            border-color: {COLORS['primary_light']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['border_focus']};
            outline: none;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            selection-background-color: {COLORS['primary']};
            selection-color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['1']};
        }}
    """


def get_spinbox_style():
    """Number input style"""
    return f"""
        QSpinBox {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['2']} {SPACING['4']};
            font-size: {FONTS['size_base']};
            min-height: 40px;
        }}
        QSpinBox:hover {{
            border-color: {COLORS['primary_light']};
        }}
        QSpinBox:focus {{
            border-color: {COLORS['border_focus']};
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {COLORS['bg_tertiary']};
            border: none;
            width: 20px;
            border-radius: {RADIUS['sm']};
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {COLORS['primary']};
        }}
    """


def get_checkbox_style():
    """Checkbox style"""
    return f"""
        QCheckBox {{
            color: {COLORS['text_primary']};
            spacing: {SPACING['3']};
            font-size: {FONTS['size_base']};
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: {RADIUS['sm']};
            border: 2px solid {COLORS['border_primary']};
            background-color: {COLORS['bg_secondary']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {COLORS['primary_light']};
            background-color: {COLORS['bg_tertiary']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {COLORS['primary_dark']};
        }}
    """


def get_label_style(variant='default'):
    """Label styles"""
    styles = {
        'default': f"color: {COLORS['text_primary']}; font-size: {FONTS['size_base']};",
        'title': f"color: {COLORS['text_primary']}; font-size: {FONTS['size_2xl']}; font-weight: 700;",
        'heading': f"color: {COLORS['text_primary']}; font-size: {FONTS['size_lg']}; font-weight: 600;",
        'muted': f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};",
        'secondary': f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_base']};",
    }
    return styles.get(variant, styles['default'])


def get_status_badge(status='ready'):
    """Status badge styles"""
    status_colors = {
        'ready': (COLORS['success'], COLORS['success']),
        'recording': (COLORS['danger'], COLORS['danger']),
        'stopped': (COLORS['warning'], COLORS['warning']),
        'error': (COLORS['danger'], COLORS['danger']),
    }
    
    bg_color, border_color = status_colors.get(status, status_colors['ready'])
    
    return f"""
        QLabel {{
            background-color: {bg_color};
            color: {COLORS['text_primary']};
            border: 2px solid {border_color};
            border-radius: {RADIUS['md']};
            padding: {SPACING['3']} {SPACING['5']};
            font-size: {FONTS['size_base']};
            font-weight: 600;
        }}
    """


def get_preview_frame():
    """Preview frame style"""
    return f"""
        QLabel {{
            background-color: #000000;
            border: 2px solid {COLORS['border_primary']};
            border-radius: {RADIUS['lg']};
        }}
    """


def get_info_card():
    """Info card with subtle background"""
    return f"""
        QFrame {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['4']};
        }}
    """


def get_section_divider():
    """Section divider"""
    return f"""
        QFrame {{
            background-color: {COLORS['border_primary']};
            max-height: 1px;
            border: none;
        }}
    """


def get_stat_label():
    """Statistics label"""
    return f"""
        QLabel {{
            color: {COLORS['text_primary']};
            background-color: {COLORS['bg_secondary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['3']} {SPACING['4']};
            font-size: {FONTS['size_base']};
            font-weight: 500;
        }}
    """
