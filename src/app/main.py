"""
Punto de entrada de la aplicación.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que src/ esté en el path cuando se ejecuta directamente
_src = Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.styles import LIGHT_STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Material Testing Analyzer")
    app.setApplicationVersion("0.2.0")

    # Fuente base moderna
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Aplicar estilos modernos
    app.setStyleSheet(LIGHT_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
