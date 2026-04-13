"""
Ventana principal con navegación entre pantallas (QStackedWidget).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.home_screen import HomeScreen
from app.ui.tension_widget import TensionWidget
from app.ui.flexion_widget import FlexionWidget
from app.ui.impact_widget import ImpactWidget

PAGE_HOME    = 0
PAGE_TENSION = 1
PAGE_FLEXION = 2
PAGE_IMPACT  = 3

PAGE_FOR_ID = {
    "tension": PAGE_TENSION,
    "flexion": PAGE_FLEXION,
    "impact":  PAGE_IMPACT,
}

LABEL_FOR_ID = {
    "tension": "Tracción",
    "flexion": "Flexión",
    "impact":  "Impacto",
}

HEADER_COLOR = {
    "tension": "#1976D2",
    "flexion": "#388E3C",
    "impact":  "#F57C00",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Análisis de Ensayos de Materiales")
        self.setMinimumSize(960, 700)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # --- Barra de navegación superior ---
        self._nav_bar = QWidget()
        self._nav_bar.setFixedHeight(52)
        self._nav_bar.setStyleSheet("background-color: #1976D2;")
        nav_layout = QHBoxLayout(self._nav_bar)
        nav_layout.setContentsMargins(16, 0, 16, 0)
        nav_layout.setSpacing(12)

        self._back_btn = QPushButton("← Inicio")
        self._back_btn.setFont(QFont("Segoe UI", 10))
        self._back_btn.setStyleSheet("""
            QPushButton {
                color: white; background: transparent;
                border: 1px solid rgba(255,255,255,0.5);
                border-radius: 6px; padding: 4px 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.15); }
        """)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._go_home)

        self._nav_title = QLabel("")
        self._nav_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._nav_title.setStyleSheet("color: white;")

        nav_layout.addWidget(self._back_btn)
        nav_layout.addWidget(self._nav_title)
        nav_layout.addStretch()

        self._main_layout.addWidget(self._nav_bar)
        self._nav_bar.hide()

        # --- Stack de páginas ---
        self._stack = QStackedWidget()
        self._main_layout.addWidget(self._stack)

        self._home = HomeScreen()
        self._home.test_selected.connect(self._on_test_selected)

        self._tension_widget = TensionWidget()
        self._flexion_widget = FlexionWidget()
        self._impact_widget  = ImpactWidget()

        self._stack.addWidget(self._home)             # 0
        self._stack.addWidget(self._tension_widget)   # 1
        self._stack.addWidget(self._flexion_widget)   # 2
        self._stack.addWidget(self._impact_widget)    # 3

        self._stack.setCurrentIndex(PAGE_HOME)

    def _on_test_selected(self, test_id: str) -> None:
        page = PAGE_FOR_ID.get(test_id)
        if page is None:
            return
        color = HEADER_COLOR.get(test_id, "#1976D2")
        self._nav_bar.setStyleSheet(f"background-color: {color};")
        self._nav_title.setText(f"Ensayo de {LABEL_FOR_ID[test_id]}")
        self._nav_bar.show()
        self._stack.setCurrentIndex(page)

    def _go_home(self) -> None:
        self._nav_bar.hide()
        self._stack.setCurrentIndex(PAGE_HOME)
