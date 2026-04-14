"""
Widget de análisis de tracción.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  [Cargar archivo]  [☑ Todos]  especímenes...            │
  ├──────────────────────────────┬──────────────────────────┤
  │                              │  Propiedades mecánicas   │
  │      Gráfico σ–ε             │  (tabla por espécimen)   │
  │                              │                          │
  ├──────────────────────────────┴──────────────────────────┤
  │                    [Descargar gráfico]                   │
  └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
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

from app.parsers import tension_parser
from app.parsers.tension_parser import TensionData, TensionSpecimen
from app.analysis import tension_analysis
from app.analysis.tension_analysis import TensionProperties

COLORS = [
    "#1976D2", "#D32F2F", "#388E3C", "#F57C00", "#7B1FA2",
    "#0097A7", "#C62828", "#558B2F", "#4527A0", "#00838F",
    "#AD1457",
]


class _LoadWorker(QThread):
    finished = pyqtSignal(object)   # TensionData
    error    = pyqtSignal(str)

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def run(self) -> None:
        try:
            data = tension_parser.parse(self._path)
            self.finished.emit(data)
        except Exception as exc:
            self.error.emit(str(exc))


class TensionWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: TensionData | None = None
        self._props: list[TensionProperties] = []
        self._checkboxes: list[QCheckBox] = []
        self._worker: _LoadWorker | None = None
        self._build_ui()

    # ------------------------------------------------------------------ UI
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
            "QPushButton { background:#1976D2; color:white; border:none; border-radius:6px; padding:0 18px; }"
            "QPushButton:hover { background:#1565C0; }"
        )
        self._load_btn.clicked.connect(self._on_load)

        self._file_label = QLabel("Sin archivo cargado")
        self._file_label.setFont(QFont("Segoe UI", 9))
        self._file_label.setStyleSheet("color: #757575;")

        top.addWidget(self._load_btn)
        top.addWidget(self._file_label)
        top.addStretch()
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

        # Área central: gráfico + tabla
        center = QHBoxLayout()
        center.setSpacing(12)

        # Gráfico matplotlib
        self._figure = Figure(figsize=(7, 5), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center.addWidget(self._canvas, stretch=3)

        # Panel de propiedades
        right = QVBoxLayout()
        right.setSpacing(8)
        props_title = QLabel("Propiedades mecánicas")
        props_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        props_title.setStyleSheet("color: #212121;")
        right.addWidget(props_title)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Propiedad", "Valor"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont("Segoe UI", 9))
        self._table.setMinimumWidth(280)
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

    # ------------------------------------------------------------------ Slots
    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo de tracción",
            "", "Archivos soportados (*.xlsx *.xls *.csv *.txt);;Todos (*)"
        )
        if not path:
            return
        self._file_label.setText(f"Cargando {Path(path).name}…")
        self._load_btn.setEnabled(False)
        self._worker = _LoadWorker(path)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_loaded(self, data: TensionData) -> None:
        self._data = data
        self._load_btn.setEnabled(True)
        self._file_label.setText(
            f"{len(data.specimens)} especímenes cargados"
            + (f" · {data.test_speed_mm_per_min:.0f} mm/min" if not np.isnan(data.test_speed_mm_per_min) else "")
        )
        self._props = [tension_analysis.calculate(sp) for sp in data.specimens]
        self._build_specimen_checkboxes()
        self._refresh_plot()
        self._refresh_table()
        self._download_btn.setEnabled(True)

    def _on_load_error(self, msg: str) -> None:
        self._load_btn.setEnabled(True)
        self._file_label.setText("Error al cargar archivo")
        QMessageBox.critical(self, "Error al cargar", msg)

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

    def _on_download(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar gráfico", "traccion.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if path:
            self._figure.savefig(path, dpi=150, bbox_inches="tight")

    # ------------------------------------------------------------------ Helpers
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

        if not self._data:
            self._draw_placeholder()
            return

        indices = self._selected_indices()
        has_curve = False

        for i in indices:
            sp    = self._data.specimens[i]
            props = self._props[i]
            color = COLORS[i % len(COLORS)]

            stress = sp.stress_MPa
            strain = sp.strain_pct

            if len(stress) > 1 and len(strain) > 1:
                ax.plot(strain, stress, color=color, linewidth=1.5,
                        label=sp.name, alpha=0.85)
                has_curve = True

                # Módulo de Young (línea punteada)
                if props.elastic_strain_range is not None and len(props.elastic_strain_range) > 0:
                    ax.plot(props.elastic_strain_range,
                            props.elastic_stress_fit,
                            color=color, linestyle="--", linewidth=1.3, alpha=0.7,
                            label=f"{sp.name} (E)")

                # Línea offset 0.2%
                if props.offset_strain_range is not None and len(props.offset_strain_range) > 0:
                    ax.plot(props.offset_strain_range,
                            props.offset_stress_line,
                            color=color, linestyle=":", linewidth=1, alpha=0.5)

                # Punto UTS
                if not np.isnan(props.uts_MPa):
                    ax.scatter([props.uts_strain_pct], [props.uts_MPa],
                               color=color, s=50, zorder=5, marker="o")

                # Límite elástico 0.2%
                if not np.isnan(props.yield_stress_MPa):
                    ax.scatter([props.yield_strain_pct], [props.yield_stress_MPa],
                               color=color, s=60, zorder=5, marker="^")
            else:
                # Sin series — graficar solo puntos resumen
                if not np.isnan(sp.max_stress_MPa):
                    ax.scatter([sp.max_strain_pct], [sp.max_stress_MPa],
                               color=color, s=80, label=sp.name, zorder=5)
                    has_curve = True

        ax.set_xlabel("Deformación (%)", fontsize=11)
        ax.set_ylabel("Esfuerzo (MPa)", fontsize=11)
        ax.set_title("Curva Esfuerzo – Deformación (Tracción)", fontsize=13, fontweight="bold")
        ax.grid(True, alpha=0.3)

        if has_curve and indices:
            ax.legend(fontsize=8, loc="best")

        self._figure.tight_layout()
        self._canvas.draw()

    def _refresh_table(self) -> None:
        indices = self._selected_indices()
        if not indices or not self._props:
            return

        # Mostrar propiedades del primer espécimen seleccionado
        # (o promedio si hay varios)
        if len(indices) == 1:
            p = self._props[indices[0]]
            rows = [
                ("Espécimen",       p.specimen_name),
                ("Módulo de Young", f"{p.youngs_modulus_MPa:.0f} MPa" if not np.isnan(p.youngs_modulus_MPa) else "–"),
                ("Límite elástico (σy)", f"{p.yield_stress_MPa:.2f} MPa" if not np.isnan(p.yield_stress_MPa) else "–"),
                ("Deform. en σy",   f"{p.yield_strain_pct:.3f} %" if not np.isnan(p.yield_strain_pct) else "–"),
                ("UTS",             f"{p.uts_MPa:.2f} MPa" if not np.isnan(p.uts_MPa) else "–"),
                ("Deform. en UTS",  f"{p.uts_strain_pct:.3f} %" if not np.isnan(p.uts_strain_pct) else "–"),
                ("Esfuerzo de rotura", f"{p.break_stress_MPa:.2f} MPa" if not np.isnan(p.break_stress_MPa) else "–"),
                ("Deform. de rotura", f"{p.break_strain_pct:.3f} %" if not np.isnan(p.break_strain_pct) else "–"),
                ("Tenacidad",       f"{p.toughness_MJ_m3:.3f} MJ/m³" if not np.isnan(p.toughness_MJ_m3) else "–"),
            ]
        else:
            # Estadísticas de múltiples especímenes
            valid_E   = [self._props[i].youngs_modulus_MPa for i in indices
                         if not np.isnan(self._props[i].youngs_modulus_MPa)]
            valid_uts = [self._props[i].uts_MPa for i in indices
                         if not np.isnan(self._props[i].uts_MPa)]
            valid_sy  = [self._props[i].yield_stress_MPa for i in indices
                         if not np.isnan(self._props[i].yield_stress_MPa)]
            rows = [
                ("Especímenes", str(len(indices))),
                ("E (promedio)",    f"{np.mean(valid_E):.0f} MPa"  if valid_E  else "–"),
                ("E (desv. std)",   f"{np.std(valid_E, ddof=1):.0f} MPa" if len(valid_E) > 1 else "–"),
                ("UTS (promedio)",  f"{np.mean(valid_uts):.2f} MPa" if valid_uts else "–"),
                ("UTS (desv. std)", f"{np.std(valid_uts, ddof=1):.2f} MPa" if len(valid_uts) > 1 else "–"),
                ("σy (promedio)",   f"{np.mean(valid_sy):.2f} MPa"  if valid_sy  else "–"),
                ("σy (desv. std)",  f"{np.std(valid_sy, ddof=1):.2f} MPa" if len(valid_sy) > 1 else "–"),
            ]

        self._table.setRowCount(len(rows))
        for r, (prop, val) in enumerate(rows):
            self._table.setItem(r, 0, QTableWidgetItem(prop))
            item_val = QTableWidgetItem(val)
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(r, 1, item_val)
        self._table.resizeColumnsToContents()

    def _draw_placeholder(self) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#F5F5F5")
        ax.text(0.5, 0.5, "Carga un archivo de tracción\npara visualizar la curva σ–ε",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=13, color="#9E9E9E")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self._canvas.draw()
