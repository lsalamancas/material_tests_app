"""
Parser para archivos de ensayo de tracción.

Estructura del archivo:
- Filas 1-2:  parámetros del ensayo
- Filas 8-9:  Shape, Batch Size, SubBatch Size
- Filas 10-20: definición de especímenes (Name, Thickness, Width, Gauge Length)
- Filas 23-36: tabla resumen de resultados (Max_Force, Max_Disp, Max_Stress, Max_Strain,
                Break_Force, Break_Disp, Break_Stress, Break_Strain, Elastic)
- Fila 37+:  series temporales por espécimen, separadas por cabeceras "1-N"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class TensionSpecimen:
    name: str
    thickness_mm: float
    width_mm: float
    gauge_length_mm: float

    # Resultados resumen
    max_force_N: float = float("nan")
    max_disp_mm: float = float("nan")
    max_stress_MPa: float = float("nan")
    max_strain_pct: float = float("nan")
    break_force_N: float = float("nan")
    break_disp_mm: float = float("nan")
    break_stress_MPa: float = float("nan")
    break_strain_pct: float = float("nan")
    elastic_modulus_MPa: float = float("nan")

    # Series temporales
    time_s: np.ndarray = field(default_factory=lambda: np.array([]))
    force_N: np.ndarray = field(default_factory=lambda: np.array([]))
    stroke_mm: np.ndarray = field(default_factory=lambda: np.array([]))

    @property
    def cross_section_mm2(self) -> float:
        return self.thickness_mm * self.width_mm

    @property
    def stress_MPa(self) -> np.ndarray:
        if self.cross_section_mm2 > 0 and len(self.force_N):
            return self.force_N / self.cross_section_mm2
        return np.array([])

    @property
    def strain_pct(self) -> np.ndarray:
        if self.gauge_length_mm > 0 and len(self.stroke_mm):
            return (self.stroke_mm / self.gauge_length_mm) * 100
        return np.array([])


@dataclass
class TensionData:
    specimens: list[TensionSpecimen] = field(default_factory=list)
    test_speed_mm_per_min: float = float("nan")

    @property
    def specimen_names(self) -> list[str]:
        return [s.name for s in self.specimens]


def _safe_float(value) -> float:
    try:
        f = float(value)
        return f if not np.isnan(f) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _parse_xlsx(path: Path) -> TensionData:
    raw = pd.read_excel(path, sheet_name=0, header=None)
    data = TensionData()

    # --- Velocidad de ensayo (fila 1, col 4 = Test Speed 1) ---
    try:
        data.test_speed_mm_per_min = float(raw.iloc[1, 4])
    except (ValueError, TypeError):
        pass

    # --- Especímenes: fila con "Name:" marca el inicio ---
    spec_header_row = None
    for i in range(len(raw)):
        cell = str(raw.iloc[i, 0]).strip()
        if cell.lower() in ("name:", "name"):
            spec_header_row = i
            break

    if spec_header_row is None:
        raise ValueError("No se encontró la sección de especímenes en el archivo.")

    # Determinar columnas de propiedades leyendo la fila de encabezado
    header_cells = [str(c).strip().lower() for c in raw.iloc[spec_header_row]]
    thickness_col = next((i for i, h in enumerate(header_cells) if "thick" in h), 1)
    width_col = next((i for i, h in enumerate(header_cells) if "width" in h), 2)
    gauge_col = next((i for i, h in enumerate(header_cells) if "gauge" in h or "length" in h), 3)

    # Skip la fila de unidades (Size Unit:) y leer especímenes hasta fila vacía
    i = spec_header_row + 2  # +1 = unidades, +2 = primer espécimen
    specimen_order: list[str] = []
    specimen_props: dict[str, TensionSpecimen] = {}

    while i < len(raw):
        name_raw = raw.iloc[i, 0]
        if pd.isna(name_raw) or str(name_raw).strip() == "":
            break
        name = str(name_raw).strip()
        spec = TensionSpecimen(
            name=name,
            thickness_mm=_safe_float(raw.iloc[i, thickness_col]),
            width_mm=_safe_float(raw.iloc[i, width_col]),
            gauge_length_mm=_safe_float(raw.iloc[i, gauge_col]),
        )
        specimen_order.append(name)
        specimen_props[name] = spec
        i += 1

    # --- Tabla resumen ---
    # Buscar fila con "Name" seguida de "Max_Force" / "Max Force"
    summary_header_row = None
    for i in range(len(raw)):
        row_vals = [str(v).strip().lower() for v in raw.iloc[i]]
        if row_vals[0] in ("name",) and any("force" in v for v in row_vals[1:]):
            summary_header_row = i
            break

    if summary_header_row is not None:
        # Fila de unidades es summary_header_row + 2
        data_start = summary_header_row + 3  # header, parameter, units, datos
        col_names = [str(raw.iloc[summary_header_row, c]).strip() for c in range(raw.shape[1])]

        def find_col(keywords: list[str]) -> int | None:
            for kw in keywords:
                for ci, cn in enumerate(col_names):
                    if kw.lower() in cn.lower():
                        return ci
            return None

        c_mf  = find_col(["Max_Force", "Max Force"])
        c_md  = find_col(["Max_Disp", "Max Disp"])
        c_ms  = find_col(["Max_Stress", "Max Stress"])
        c_mst = find_col(["Max_Strain", "Max Strain"])
        c_bf  = find_col(["Break_Force", "Break Force"])
        c_bd  = find_col(["Break_Disp", "Break Disp"])
        c_bs  = find_col(["Break_Stress", "Break Stress"])
        c_bst = find_col(["Break_Strain", "Break Strain"])
        c_el  = find_col(["Elastic"])

        for i in range(data_start, len(raw)):
            name_raw = raw.iloc[i, 0]
            if pd.isna(name_raw):
                break
            name = str(name_raw).strip()
            if name not in specimen_props:
                continue
            sp = specimen_props[name]
            if c_mf  is not None: sp.max_force_N       = _safe_float(raw.iloc[i, c_mf])
            if c_md  is not None: sp.max_disp_mm        = _safe_float(raw.iloc[i, c_md])
            if c_ms  is not None: sp.max_stress_MPa     = _safe_float(raw.iloc[i, c_ms])
            if c_mst is not None: sp.max_strain_pct     = _safe_float(raw.iloc[i, c_mst])
            if c_bf  is not None: sp.break_force_N      = _safe_float(raw.iloc[i, c_bf])
            if c_bd  is not None: sp.break_disp_mm      = _safe_float(raw.iloc[i, c_bd])
            if c_bs  is not None: sp.break_stress_MPa   = _safe_float(raw.iloc[i, c_bs])
            if c_bst is not None: sp.break_strain_pct   = _safe_float(raw.iloc[i, c_bst])
            if c_el  is not None: sp.elastic_modulus_MPa= _safe_float(raw.iloc[i, c_el])

    # --- Series temporales ---
    # Detectar filas de cabecera "1-N" (p. ej. " 1- 1", " 1- 2", ...)
    import re
    specimen_ts_starts: list[tuple[int, int]] = []  # (row_index, specimen_index 1-based)
    for i in range(len(raw)):
        val = str(raw.iloc[i, 0]).strip()
        m = re.match(r"1-\s*(\d+)$", val)
        if m:
            specimen_ts_starts.append((i, int(m.group(1))))

    for idx, (start_row, sp_num) in enumerate(specimen_ts_starts):
        if sp_num < 1 or sp_num > len(specimen_order):
            continue
        name = specimen_order[sp_num - 1]
        sp = specimen_props[name]

        # Saltar las 3 filas de cabecera (1-N, Time/Force/Stroke, sec/N/mm)
        data_row = start_row + 3
        end_row = (
            specimen_ts_starts[idx + 1][0]
            if idx + 1 < len(specimen_ts_starts)
            else len(raw)
        )

        chunk = raw.iloc[data_row:end_row, :3].copy()
        chunk.columns = ["time", "force", "stroke"]
        chunk = chunk.apply(pd.to_numeric, errors="coerce").dropna()

        sp.time_s   = chunk["time"].to_numpy()
        sp.force_N  = chunk["force"].to_numpy()
        sp.stroke_mm = chunk["stroke"].to_numpy()

    data.specimens = [specimen_props[n] for n in specimen_order]
    return data


def _parse_csv(path: Path) -> TensionData:
    """Fallback para CSV simple: columnas Time, Force, Stroke con especímenes en filas."""
    sep = "\t" if path.suffix.lower() == ".txt" else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip() for c in df.columns]

    data = TensionData()
    sp = TensionSpecimen(
        name=path.stem,
        thickness_mm=4.0,
        width_mm=7.0,
        gauge_length_mm=30.99,
    )
    force_col  = next((c for c in df.columns if "force" in c.lower() or c.upper() == "F"), None)
    stroke_col = next((c for c in df.columns if "stroke" in c.lower() or "disp" in c.lower()), None)
    time_col   = next((c for c in df.columns if "time" in c.lower()), None)

    if force_col:
        sp.force_N = pd.to_numeric(df[force_col], errors="coerce").dropna().to_numpy()
    if stroke_col:
        sp.stroke_mm = pd.to_numeric(df[stroke_col], errors="coerce").dropna().to_numpy()
    if time_col:
        sp.time_s = pd.to_numeric(df[time_col], errors="coerce").dropna().to_numpy()

    data.specimens = [sp]
    return data


def parse(path: str | Path) -> TensionData:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    suffix = p.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return _parse_xlsx(p)
    if suffix in (".csv", ".txt"):
        return _parse_csv(p)
    raise ValueError(f"Formato no soportado: {suffix}")
