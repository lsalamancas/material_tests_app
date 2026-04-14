"""
Estilos CSS modernos de la aplicación.
Tema claro y oscuro.
"""

# ============================================================================
# TEMA CLARO (Light Mode)
# ============================================================================

LIGHT_STYLESHEET = """
/* Ventana principal */
QMainWindow {
    background-color: #F8FAFB;
    color: #1A1A1A;
}

/* Widget general */
QWidget {
    background-color: #F8FAFB;
    color: #1A1A1A;
}

/* Botones */
QPushButton {
    background-color: #2563EB;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #D1D5DB;
    color: #9CA3AF;
}

/* Botones secundarios */
QPushButton#secondary {
    background-color: #E5E7EB;
    color: #1F2937;
}

QPushButton#secondary:hover {
    background-color: #D1D5DB;
}

/* Tablas */
QTableWidget {
    background-color: white;
    color: #1A1A1A;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    gridline-color: #F3F4F6;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #DBEAFE;
    color: #1A1A1A;
}

QHeaderView::section {
    background-color: #F3F4F6;
    color: #374151;
    padding: 8px;
    border: none;
    border-right: 1px solid #E5E7EB;
    border-bottom: 1px solid #E5E7EB;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    width: 12px;
    background-color: #F3F4F6;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #D1D5DB;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9CA3AF;
}

QScrollBar:horizontal {
    height: 12px;
    background-color: #F3F4F6;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #D1D5DB;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #9CA3AF;
}

/* Labels */
QLabel {
    color: #1A1A1A;
}

/* Input */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: white;
    color: #1A1A1A;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #DBEAFE;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2563EB;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #E5E7EB;
    height: 8px;
    background: #E5E7EB;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #2563EB;
    border: 2px solid white;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #1D4ED8;
}

/* Checkboxes */
QCheckBox {
    color: #1A1A1A;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #D1D5DB;
    border-radius: 4px;
    background-color: white;
}

QCheckBox::indicator:hover {
    border: 2px solid #2563EB;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border: 2px solid #2563EB;
}

/* Sidebar */
#sidebar {
    background-color: white;
    border-right: 1px solid #E5E7EB;
}

#sidebar_btn {
    background-color: transparent;
    color: #6B7280;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 8px;
    text-align: left;
    font-weight: 500;
}

#sidebar_btn:hover {
    background-color: #F3F4F6;
    color: #1F2937;
}

#sidebar_btn:pressed, #sidebar_btn:checked {
    background-color: #DBEAFE;
    color: #2563EB;
    border-left: 3px solid #2563EB;
    padding-left: 13px;
}

/* Header */
#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2563EB, stop:1 #1D4ED8);
}

#header_title {
    color: white;
    font-weight: bold;
    font-size: 14pt;
}

#header_subtitle {
    color: rgba(255, 255, 255, 0.85);
    font-size: 9pt;
}
"""

# ============================================================================
# TEMA OSCURO (Dark Mode)
# ============================================================================

DARK_STYLESHEET = """
/* Ventana principal */
QMainWindow {
    background-color: #0F172A;
    color: #E2E8F0;
}

/* Widget general */
QWidget {
    background-color: #0F172A;
    color: #E2E8F0;
}

/* Botones */
QPushButton {
    background-color: #3B82F6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #2563EB;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #475569;
    color: #94A3B8;
}

/* Botones secundarios */
QPushButton#secondary {
    background-color: #334155;
    color: #E2E8F0;
}

QPushButton#secondary:hover {
    background-color: #475569;
}

/* Tablas */
QTableWidget {
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
}

QTableWidget::item {
    padding: 8px;
    background-color: #1E293B;
}

QTableWidget::item:selected {
    background-color: #1E40AF;
    color: #E2E8F0;
}

QHeaderView::section {
    background-color: #334155;
    color: #CBD5E1;
    padding: 8px;
    border: none;
    border-right: 1px solid #475569;
    border-bottom: 1px solid #475569;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    width: 12px;
    background-color: #1E293B;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #475569;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #64748B;
}

QScrollBar:horizontal {
    height: 12px;
    background-color: #1E293B;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #475569;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #64748B;
}

/* Labels */
QLabel {
    color: #E2E8F0;
}

/* Input */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #1E40AF;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #3B82F6;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #334155;
    height: 8px;
    background: #334155;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #3B82F6;
    border: 2px solid #0F172A;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #2563EB;
}

/* Checkboxes */
QCheckBox {
    color: #E2E8F0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #475569;
    border-radius: 4px;
    background-color: #1E293B;
}

QCheckBox::indicator:hover {
    border: 2px solid #3B82F6;
}

QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border: 2px solid #3B82F6;
}

/* Sidebar */
#sidebar {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}

#sidebar_btn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 8px;
    text-align: left;
    font-weight: 500;
}

#sidebar_btn:hover {
    background-color: #334155;
    color: #E2E8F0;
}

#sidebar_btn:pressed, #sidebar_btn:checked {
    background-color: #1E40AF;
    color: #3B82F6;
    border-left: 3px solid #3B82F6;
    padding-left: 13px;
}

/* Header */
#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #3B82F6, stop:1 #2563EB);
}

#header_title {
    color: white;
    font-weight: bold;
    font-size: 14pt;
}

#header_subtitle {
    color: rgba(255, 255, 255, 0.75);
    font-size: 9pt;
}
"""
