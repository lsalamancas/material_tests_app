"""
Widget de análisis de flexión (3 puntos).

Muestra barras comparativas de: Esfuerzo máximo, Fuerza máxima,
Deformación máxima y Módulo de flexión por espécimen.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.parsers import flexion_parser
from app.parsers.flexion_parser import FlexionData
from app.analysis import flexion_analysis
from app.analysis.flexion_analysis import FlexionProperties

PLOT_OPTIONS = {
    "Esfuerzo máximo (MPa)": "flexural_strength_MPa",
    "Fuerza máxima (N)":     "max_force_N",
    "Desplazamiento máx. (mm)": "max_disp_mm",
    "Deformación máx. (%)":  "max_strain_pct",
    "Módulo de flexión (MPa)": "flexural_modulus_MPa",
}

BAR_COLOR = "#388E3C"
BAR_HOVER = "#81C784"


class FlexionWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: FlexionData | None = None
        self._props: list[FlexionProperties] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Barra superior
        top = QHBoxLayout()
        self._load_btn = QPushButton("Cargar archivo")
        self._load_btn.setFont(QFont("Segoe UI", 10))
        self._load_btn.setFixedHeight(36)
        self._load_btn.setStyleSheet(
            "QPushButton { background:#388E3C; color:white; border:none; border-radius:6px; padding:0 18px; }"
            "QPushButton:hover { background:#2E7D32; }"
        )
        self._load_btn.clicked.connect(self._on_load)

        self._file_label = QLabel("Sin archivo cargado")
        self._file_label.setFont(QFont("Segoe UI", 9))
        self._file_label.setStyleSheet("color: #757575;")

        top.addWidget(self._load_btn)
        top.addWidget(self._file_label)
        top.addStretch()

        # Selector de variable a graficar
        plot_lbl = QLabel("Graficar:")
        plot_lbl.setFont(QFont("Segoe UI", 9))
        self._plot_combo = QComboBox()
        self._plot_combo.setFont(QFont("Segoe UI", 9))
        self._plot_combo.setFixedHeight(32)
        for label in PLOT_OPTIONS:
            self._plot_combo.addItem(label)
        self._plot_combo.currentIndexChanged.connect(self._refresh_plot)

        top.addWidget(plot_lbl)
        top.addWidget(self._plot_combo)
        root.addLayout(top)

        # Área central
        center = QHBoxLayout()
        center.setSpacing(12)

        self._figure = Figure(figsize=(7, 5), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center.addWidget(self._canvas, stretch=3)

        # Tabla de resultados
        right = QVBoxLayout()
        props_title = QLabel("Propiedades mecánicas")
        props_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        props_title.setStyleSheet("color: #212121;")
        right.addWidget(props_title)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Espécimen", "σ_máx (MPa)", "E_flex (MPa)", "ε_máx (%)"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont("Segoe UI", 9))
        self._table.setMinimumWidth(300)
        right.addWidget(self._table, stretch=1)

        center.addLayout(right, stretch=2)
        root.addLayout(center, stretch=1)

        # Barra inferior
        bottom = QHBoxLayout()
        bottom.addStretch()
        self._download_btn = QPushButton("Descargar gráfico")
        self._download_btn.setFont(QFont("Segoe UI", 10))
        self._download_btn.setFixedHeight(36)
        self._download_btn.setEnabled(False)
        self._download_btn.setStyleSheet(
            "QPushButton { background:#424242; color:white; border:none; border-radius:6px; padding:0 18px; }"
            "QPushButton:hover { background:#212121; }"
            "QPushButton:disabled { background:#BDBDBD; color:#757575; }"
        )
        self._download_btn.clicked.connect(self._on_download)
        bottom.addWidget(self._download_btn)
        root.addLayout(bottom)

        self._draw_placeholder()

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo de flexión",
            "", "Archivos soportados (*.xlsx *.xls *.csv *.txt);;Todos (*)"
        )
        if not path:
            return
        try:
            self._data = flexion_parser.parse(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", str(exc))
            return

        self._props = flexion_analysis.calculate_all(self._data.specimens)
        n = len(self._data.specimens)
        self._file_label.setText(f"{n} especímenes cargados")
        self._refresh_plot()
        self._refresh_table()
        self._download_btn.setEnabled(True)

    def _on_download(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfico", "flexion.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if path:
            self._figure.savefig(path, dpi=150, bbox_inches="tight")

    def _refresh_plot(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)

        if not self._data or not self._props:
            self._draw_placeholder()
            return

        label = self._plot_combo.currentText()
        attr  = PLOT_OPTIONS[label]

        names  = [p.specimen_name for p in self._props]
        values = [getattr(p, attr) for p in self._props]
        valid  = [(n, v) for n, v in zip(names, values) if not np.isnan(v)]

        if not valid:
            ax.text(0.5, 0.5, "Sin datos disponibles para esta variable",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=12, color="#9E9E9E")
            self._canvas.draw()
            return

        names_v, vals_v = zip(*valid)
        x = np.arange(len(names_v))
        bars = ax.bar(x, vals_v, color=BAR_COLOR, edgecolor="white",
                      linewidth=0.5, width=0.6)

        # Etiquetas en las barras
        for bar, val in zip(bars, vals_v):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.01,
                f"{val:.1f}",
                ha="center", va="bottom", fontsize=8, color="#424242"
            )

        ax.set_xticks(x)
        ax.set_xticklabels(names_v, rotation=35, ha="right", fontsize=8)
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f"Flexión 3 puntos — {label}", fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)

        self._figure.tight_layout()
        self._canvas.draw()

    def _refresh_table(self) -> None:
        self._table.setRowCount(len(self._props))
        for r, p in enumerate(self._props):
            def fmt(v): return f"{v:.2f}" if not np.isnan(v) else "–"
            self._table.setItem(r, 0, QTableWidgetItem(p.specimen_name))
            for c, val in enumerate([p.flexural_strength_MPa,
                                      p.flexural_modulus_MPa,
                                      p.max_strain_pct], start=1):
                item = QTableWidgetItem(fmt(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(r, c, item)
        self._table.resizeColumnsToContents()

    def _draw_placeholder(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#F5F5F5")
        ax.text(0.5, 0.5, "Carga un archivo de flexión\npara ver la comparativa de especímenes",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=13, color="#9E9E9E")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self._canvas.draw()
