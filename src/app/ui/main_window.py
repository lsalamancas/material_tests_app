"""
Ventana principal con navegación entre pantallas (QStackedWidget).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
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
from app.ui.styles import LIGHT_STYLESHEET, DARK_STYLESHEET

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
        self.setMinimumSize(1200, 700)
        self._dark_mode = False
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # --- Barra de navegación superior con toggle dark mode ---
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

        # Botón de dark mode toggle
        self._dark_mode_btn = QPushButton("🌙")
        self._dark_mode_btn.setFixedSize(40, 40)
        self._dark_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
        """)
        self._dark_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dark_mode_btn.clicked.connect(self._toggle_dark_mode)
        nav_layout.addWidget(self._dark_mode_btn)

        self._main_layout.addWidget(self._nav_bar)
        self._nav_bar.hide()

        # --- Contenedor horizontal: Sidebar + Stack ---
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- Sidebar de navegación ---
        self._sidebar = QWidget()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet("""
            QWidget {
                background-color: #F3F4F6;
                border-right: 1px solid #E5E7EB;
            }
        """)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(8)

        # Botones de navegación
        self._home_btn = self._create_sidebar_btn("🏠 Inicio", PAGE_HOME)
        self._tension_btn = self._create_sidebar_btn("📈 Tracción", PAGE_TENSION)
        self._flexion_btn = self._create_sidebar_btn("↔️ Flexión", PAGE_FLEXION)
        self._impact_btn = self._create_sidebar_btn("💥 Impacto", PAGE_IMPACT)

        sidebar_layout.addWidget(self._home_btn)
        sidebar_layout.addWidget(self._tension_btn)
        sidebar_layout.addWidget(self._flexion_btn)
        sidebar_layout.addWidget(self._impact_btn)
        sidebar_layout.addStretch()

        content_layout.addWidget(self._sidebar)

        # --- Stack de páginas ---
        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack, 1)

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
        self._home_btn.setChecked(True)

        self._main_layout.addWidget(content_container, 1)

    def _create_sidebar_btn(self, text: str, page: int) -> QPushButton:
        """Crea un botón de sidebar con estilo moderno."""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6B7280;
                border: none;
                text-align: left;
                padding-left: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton:checked {
                background-color: #DBEAFE;
                color: #2563EB;
                border-left: 3px solid #2563EB;
                padding-left: 13px;
            }
        """)
        btn.clicked.connect(lambda: self._navigate_to_page(page))
        return btn

    def _on_test_selected(self, test_id: str) -> None:
        page = PAGE_FOR_ID.get(test_id)
        if page is None:
            return
        color = HEADER_COLOR.get(test_id, "#1976D2")
        self._nav_bar.setStyleSheet(f"background-color: {color};")
        self._nav_title.setText(f"Ensayo de {LABEL_FOR_ID[test_id]}")
        self._nav_bar.show()
        self._stack.setCurrentIndex(page)
        self._uncheck_all_sidebar_buttons()

    def _go_home(self) -> None:
        self._nav_bar.hide()
        self._stack.setCurrentIndex(PAGE_HOME)
        self._home_btn.setChecked(True)
        self._uncheck_all_sidebar_buttons()
        self._home_btn.setChecked(True)

    def _navigate_to_page(self, page: int) -> None:
        """Navega a una página del stack."""
        if page == PAGE_HOME:
            self._go_home()
        else:
            # Encontrar el test_id correspondiente
            for test_id, page_num in PAGE_FOR_ID.items():
                if page_num == page:
                    self._on_test_selected(test_id)
                    break

    def _uncheck_all_sidebar_buttons(self) -> None:
        """Desmarca todos los botones del sidebar."""
        self._home_btn.setChecked(False)
        self._tension_btn.setChecked(False)
        self._flexion_btn.setChecked(False)
        self._impact_btn.setChecked(False)

    def _toggle_dark_mode(self) -> None:
        """Alterna entre modo claro y oscuro."""
        self._dark_mode = not self._dark_mode
        app = QApplication.instance()
        
        if self._dark_mode:
            app.setStyleSheet(DARK_STYLESHEET)
            self._dark_mode_btn.setText("☀️")
            self._sidebar.setStyleSheet("""
                QWidget {
                    background-color: #1E293B;
                    border-right: 1px solid #0F172A;
                }
            """)
        else:
            app.setStyleSheet(LIGHT_STYLESHEET)
            self._dark_mode_btn.setText("🌙")
            self._sidebar.setStyleSheet("""
                QWidget {
                    background-color: #F3F4F6;
                    border-right: 1px solid #E5E7EB;
                }
            """)
