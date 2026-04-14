"""
Pantalla inicial: selección del tipo de ensayo.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

TEST_TYPES = [
    {
        "id": "tension",
        "label": "Tracción",
        "subtitle": "Curva esfuerzo–deformación\nMódulo de Young · UTS · Límite elástico",
        "icon": "↗",
        "color": "#1976D2",
        "hover": "#1565C0",
    },
    {
        "id": "flexion",
        "label": "Flexión",
        "subtitle": "Ensayo 3 puntos\nMódulo de flexión · Resistencia máxima",
        "icon": "⌒",
        "color": "#388E3C",
        "hover": "#2E7D32",
    },
    {
        "id": "impact",
        "label": "Impacto",
        "subtitle": "ASTM D256 (Charpy / Izod)\nEnergía absorbida · Tenacidad",
        "icon": "⚡",
        "color": "#F57C00",
        "hover": "#E65100",
    },
]

CARD_STYLE = """
QPushButton {{
    background-color: {color};
    color: white;
    border: none;
    border-radius: 12px;
    padding: 24px 32px;
    text-align: left;
}}
QPushButton:hover {{
    background-color: {hover};
}}
QPushButton:pressed {{
    background-color: {hover};
    padding-top: 26px;
    padding-bottom: 22px;
}}
"""


class TestCard(QPushButton):
    def __init__(self, test_info: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info = test_info
        self.setFixedHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(CARD_STYLE.format(**test_info))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        # Icono + título
        top = QHBoxLayout()
        icon_lbl = QLabel(test_info["icon"])
        icon_lbl.setFont(QFont("Segoe UI", 28))
        icon_lbl.setStyleSheet("background-color: transparent; color: rgba(255,255,255,0.9);")

        title_lbl = QLabel(test_info["label"])
        title_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title_lbl.setStyleSheet("background-color: transparent; color: white;")

        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        sub_lbl = QLabel(test_info["subtitle"])
        sub_lbl.setFont(QFont("Segoe UI", 10))
        sub_lbl.setStyleSheet("background-color: transparent;color: rgba(255,255,255,0.85);")
        sub_lbl.setWordWrap(True)
        layout.addWidget(sub_lbl)

        # Impedir que el layout interno capture los clics del botón
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        


class HomeScreen(QWidget):
    """
    Pantalla de bienvenida con tres tarjetas de selección de ensayo.
    Emite `test_selected(str)` con el id del ensayo elegido.
    """

    test_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 48, 48, 48)
        root.setSpacing(0)

        # Encabezado
        title = QLabel("Análisis de Ensayos de Materiales")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("color: #212121; margin-bottom: 8px;")
        root.addWidget(title)

        subtitle = QLabel("Selecciona el tipo de ensayo para comenzar")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet("color: #757575; margin-bottom: 40px;")
        root.addWidget(subtitle)

        # Tarjetas
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(16)
        for test in TEST_TYPES:
            card = TestCard(test)
            card.clicked.connect(lambda _checked, tid=test["id"]: self.test_selected.emit(tid))
            cards_layout.addWidget(card)

        root.addLayout(cards_layout)
        root.addStretch()

        # Pie
        footer = QLabel("Carga archivos .xlsx · .csv · .txt")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet("color: #BDBDBD; margin-top: 32px;")
        root.addWidget(footer)
