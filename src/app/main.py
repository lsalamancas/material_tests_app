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


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Material Testing Analyzer")
    app.setApplicationVersion("0.1.0")

    # Fuente base
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Estilo global minimalista
    app.setStyleSheet("""
        QWidget {
            background-color: #FAFAFA;
            color: #212121;
        }
        QScrollBar:vertical {
            width: 8px; background: #F0F0F0; border: none;
        }
        QScrollBar::handle:vertical {
            background: #BDBDBD; border-radius: 4px; min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            height: 8px; background: #F0F0F0; border: none;
        }
        QScrollBar::handle:horizontal {
            background: #BDBDBD; border-radius: 4px; min-width: 20px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QTableWidget {
            gridline-color: #E0E0E0;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
        QHeaderView::section {
            background-color: #EEEEEE;
            border: none;
            border-bottom: 1px solid #BDBDBD;
            padding: 4px 8px;
            font-weight: bold;
        }
        QComboBox {
            border: 1px solid #BDBDBD;
            border-radius: 4px;
            padding: 4px 8px;
            background: white;
        }
        QComboBox::drop-down { border: none; }
        QComboBox:hover { border-color: #1976D2; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
