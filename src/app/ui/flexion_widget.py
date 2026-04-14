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
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
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

COLORS = [
    "#1976D2", "#D32F2F", "#388E3C", "#F57C00", "#7B1FA2",
    "#0097A7", "#C62828", "#558B2F", "#4527A0", "#00838F",
    "#AD1457",
]

BAR_COLOR = "#388E3C"
BAR_HOVER = "#81C784"


class FlexionWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: FlexionData | None = None
        self._props: list[FlexionProperties] = []
        self._checkboxes: list[QCheckBox] = []
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

        # Selección de especímenes
        self._spec_bar = QWidget()
        spec_bar_layout = QHBoxLayout(self._spec_bar)
        spec_bar_layout.setContentsMargins(0, 0, 0, 0)
        spec_bar_layout.setSpacing(8)

        self._all_cb = QCheckBox("Todos")
        self._all_cb.setChecked(True)
        self._all_cb.setFont(QFont("Segoe UI", 9))
        self._all_cb.stateChanged.connect(self._on_all_toggled)
        spec_bar_layout.addWidget(self._all_cb)

        self._spec_scroll = QScrollArea()
        self._spec_scroll.setWidgetResizable(True)
        self._spec_scroll.setFixedHeight(38)
        self._spec_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._spec_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._spec_scroll.setStyleSheet("QScrollArea { border: none; }")

        self._spec_container = QWidget()
        self._spec_inner = QHBoxLayout(self._spec_container)
        self._spec_inner.setContentsMargins(0, 0, 0, 0)
        self._spec_inner.setSpacing(6)
        self._spec_scroll.setWidget(self._spec_container)

        spec_bar_layout.addWidget(self._spec_scroll)
        self._spec_bar.setVisible(False)
        root.addWidget(self._spec_bar)
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
        self._build_specimen_checkboxes()
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

    def _on_all_toggled(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
        self._refresh_plot()

    def _on_specimen_toggled(self) -> None:
        all_checked = all(cb.isChecked() for cb in self._checkboxes)
        self._all_cb.blockSignals(True)
        self._all_cb.setChecked(all_checked)
        self._all_cb.blockSignals(False)
        self._refresh_plot()

    def _build_specimen_checkboxes(self) -> None:
        # Limpiar
        for cb in self._checkboxes:
            cb.deleteLater()
        self._checkboxes.clear()

        if not self._data:
            return

        for i, sp in enumerate(self._data.specimens):
            cb = QCheckBox(sp.name)
            cb.setChecked(True)
            cb.setFont(QFont("Segoe UI", 9))
            color = COLORS[i % len(COLORS)]
            cb.setStyleSheet(f"QCheckBox {{ color: {color}; font-weight: bold; }}")
            cb.stateChanged.connect(self._on_specimen_toggled)
            self._spec_inner.addWidget(cb)
            self._checkboxes.append(cb)

        self._spec_bar.setVisible(True)

    def _selected_indices(self) -> list[int]:
        return [i for i, cb in enumerate(self._checkboxes) if cb.isChecked()]

    def _refresh_plot(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)

        if not self._data or not self._props:
            self._draw_placeholder()
            return

        label = self._plot_combo.currentText()
        attr  = PLOT_OPTIONS[label]

        indices = self._selected_indices()
        names  = [self._props[i].specimen_name for i in indices]
        values = [getattr(self._props[i], attr) for i in indices]
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
        indices = self._selected_indices()
        selected_props = [self._props[i] for i in indices]
        self._table.setRowCount(len(selected_props))
        for r, p in enumerate(selected_props):
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
