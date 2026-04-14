"""
Widget de análisis de impacto (ASTM D256).

Muestra:
- Gráfico de barras: Energía absorbida por espécimen
- Líneas de media ± 1σ superpuestas
- Panel de estadísticas (N, media, std, CV, min, max)
- Pestaña alternativa con gráfico de Tenacidad
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

from app.parsers import impact_parser
from app.parsers.impact_parser import ImpactData
from app.analysis import impact_analysis
from app.analysis.impact_analysis import ImpactSummary

PLOT_OPTIONS = {
    "Energía absorbida (J)":    "energy",
    "Tenacidad (J/mm²)":        "toughness",
}

COLORS = [
    "#1976D2", "#D32F2F", "#388E3C", "#F57C00", "#7B1FA2",
    "#0097A7", "#C62828", "#558B2F", "#4527A0", "#00838F",
    "#AD1457",
]

BAR_COLOR   = "#F57C00"
MEAN_COLOR  = "#B71C1C"
SIGMA_COLOR = "#EF9A9A"


class ImpactWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: ImpactData | None = None
        self._summary: ImpactSummary | None = None
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
            "QPushButton { background:#F57C00; color:white; border:none; border-radius:6px; padding:0 18px; }"
            "QPushButton:hover { background:#E65100; }"
        )
        self._load_btn.clicked.connect(self._on_load)

        self._file_label = QLabel("Sin archivo cargado")
        self._file_label.setFont(QFont("Segoe UI", 9))
        self._file_label.setStyleSheet("color: #757575;")

        top.addWidget(self._load_btn)
        top.addWidget(self._file_label)
        top.addStretch()

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

        # Panel derecho: estadísticas
        right = QVBoxLayout()
        right.setSpacing(8)

        meta_title = QLabel("Información del ensayo")
        meta_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        meta_title.setStyleSheet("color: #212121;")
        right.addWidget(meta_title)

        self._meta_table = QTableWidget()
        self._meta_table.setColumnCount(2)
        self._meta_table.setHorizontalHeaderLabels(["Campo", "Valor"])
        self._meta_table.horizontalHeader().setStretchLastSection(True)
        self._meta_table.verticalHeader().setVisible(False)
        self._meta_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._meta_table.setAlternatingRowColors(True)
        self._meta_table.setFont(QFont("Segoe UI", 9))
        self._meta_table.setFixedHeight(120)
        right.addWidget(self._meta_table)

        stats_title = QLabel("Estadísticas")
        stats_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        stats_title.setStyleSheet("color: #212121; margin-top: 8px;")
        right.addWidget(stats_title)

        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(3)
        self._stats_table.setHorizontalHeaderLabels(["Estadístico", "Energía (J)", "Tenacidad (J/mm²)"])
        self._stats_table.horizontalHeader().setStretchLastSection(True)
        self._stats_table.verticalHeader().setVisible(False)
        self._stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._stats_table.setAlternatingRowColors(True)
        self._stats_table.setFont(QFont("Segoe UI", 9))
        self._stats_table.setMinimumWidth(300)
        right.addWidget(self._stats_table, stretch=1)

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
            self, "Abrir archivo de impacto",
            "", "Archivos soportados (*.xlsx *.xls *.csv *.txt);;Todos (*)"
        )
        if not path:
            return
        try:
            self._data = impact_parser.parse(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", str(exc))
            return

        self._summary = impact_analysis.summarize(self._data)
        n = len(self._data.specimens)
        self._file_label.setText(
            f"{n} especímenes · Norma: {self._data.standard}"
        )
        self._build_specimen_checkboxes()
        self._refresh_plot()
        self._refresh_tables()
        self._download_btn.setEnabled(True)

    def _on_download(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfico", "impacto.png",
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
            cb = QCheckBox(f"#{sp.number}")
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

        if not self._data or not self._summary:
            self._draw_placeholder()
            return

        var_key = PLOT_OPTIONS[self._plot_combo.currentText()]

        if var_key == "energy":
            values = [s.energy_J for s in self._data.specimens]
            ylabel = "Energía absorbida (J)"
            mean   = self._summary.mean_energy_J
            std    = self._summary.std_energy_J
        else:
            values = [s.toughness_J_mm2 for s in self._data.specimens]
            ylabel = "Tenacidad (J/mm²)"
            mean   = self._summary.mean_toughness
            std    = self._summary.std_toughness

        indices = self._selected_indices()
        labels = [f"#{self._data.specimens[i].number}" for i in indices]
        selected_values = [values[i] for i in indices]
        valid_mask = [not np.isnan(v) for v in selected_values]
        x = np.arange(len(indices))[valid_mask]
        vals = np.array([v for v, m in zip(selected_values, valid_mask) if m])

        bars = ax.bar(x, vals, color=BAR_COLOR, edgecolor="white",
                      linewidth=0.5, width=0.7, zorder=3)

        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.01,
                f"{val:.3f}",
                ha="center", va="bottom", fontsize=8, color="#424242"
            )

        # Línea de media y banda ±σ (calculadas solo con especímenes seleccionados)
        if len(vals) > 0 and not np.all(np.isnan(vals)):
            selected_mean = np.nanmean(vals)
            selected_std = np.nanstd(vals, ddof=1) if len(vals) > 1 else np.nan
            if len(x):
                ax.axhline(selected_mean, color=MEAN_COLOR, linewidth=1.5,
                           linestyle="--", label=f"Media = {selected_mean:.3f}", zorder=4)
                if not np.isnan(selected_std):
                    ax.axhspan(selected_mean - selected_std, selected_mean + selected_std,
                               alpha=0.15, color=SIGMA_COLOR,
                               label=f"±σ = {selected_std:.3f}", zorder=2)

        ax.set_xticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_xlabel("Espécimen", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(f"Impacto ({self._data.standard}) — {ylabel}",
                     fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.3, zorder=0)
        ax.set_axisbelow(True)
        if x.size > 0:
            ax.legend(fontsize=9)

        self._figure.tight_layout()
        self._canvas.draw()

    def _refresh_tables(self) -> None:
        if not self._data or not self._summary:
            return

        # Metadatos
        meta_rows = [
            ("Norma",         self._data.standard),
            ("Tipo de muesca", self._data.notch_type),
            ("Prof. muesca",  f"{self._data.notch_depth_mm} mm"),
            ("Lote",          self._data.batch_name or "—"),
            ("N especímenes", str(self._summary.n)),
        ]
        self._meta_table.setRowCount(len(meta_rows))
        for r, (k, v) in enumerate(meta_rows):
            self._meta_table.setItem(r, 0, QTableWidgetItem(k))
            item = QTableWidgetItem(v)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._meta_table.setItem(r, 1, item)
        self._meta_table.resizeColumnsToContents()

        # Estadísticas
        def f(v): return f"{v:.4f}" if not np.isnan(v) else "–"
        s = self._summary
        stats_rows = [
            ("Mínimo",              f(s.min_energy_J),  f(s.min_toughness)),
            ("Máximo",              f(s.max_energy_J),  f(s.max_toughness)),
            ("Media",               f(s.mean_energy_J), f(s.mean_toughness)),
            ("Desv. estándar",      f(s.std_energy_J),  f(s.std_toughness)),
            ("Coef. variación (%)", f(s.cv_energy_pct), f(s.cv_toughness_pct)),
        ]
        self._stats_table.setRowCount(len(stats_rows))
        for r, (stat, e_val, t_val) in enumerate(stats_rows):
            self._stats_table.setItem(r, 0, QTableWidgetItem(stat))
            for c, v in enumerate([e_val, t_val], start=1):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._stats_table.setItem(r, c, item)
        self._stats_table.resizeColumnsToContents()

    def _draw_placeholder(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#F5F5F5")
        ax.text(0.5, 0.5, "Carga un archivo de impacto\npara ver la energía absorbida por espécimen",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=13, color="#9E9E9E")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self._canvas.draw()
