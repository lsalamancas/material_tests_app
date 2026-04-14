#!/usr/bin/env python
"""
Script de entrada para la aplicación Material Testing Analyzer.
"""

import sys
from pathlib import Path

# Asegurar que el paquete src está disponible
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.app.main import main

if __name__ == "__main__":
    main()
