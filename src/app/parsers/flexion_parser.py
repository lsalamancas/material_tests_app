"""
Parser para archivos de ensayo de flexión (3 puntos).

Estructura del archivo:
- Filas 1-2:  parámetros del ensayo (F.tai, Single, 3 Point, Stroke, velocidad...)
- Filas 7-8:  Shape, Batch Size, SubBatch Size
- Filas 9-19: definición de especímenes (Name, Thickness, Width, Lower Support)
- Filas 22-33: tabla resumen (Name, Max_Force, Max_Disp, Max_Stress, Max_Strain)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class FlexionSpecimen:
    name: str
    thickness_mm: float
    width_mm: float
    span_mm: float  # Lower Support distance

    max_force_N: float = float("nan")
    max_disp_mm: float = float("nan")
    max_stress_MPa: float = float("nan")
    max_strain_pct: float = float("nan")


@dataclass
class FlexionData:
    specimens: list[FlexionSpecimen] = field(default_factory=list)
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


def _parse_xlsx(path: Path) -> FlexionData:
    raw = pd.read_excel(path, sheet_name=0, header=None)
    data = FlexionData()

    # Velocidad de ensayo
    try:
        data.test_speed_mm_per_min = float(raw.iloc[1, 4])
    except (TypeError, ValueError):
        pass

    # --- Especímenes ---
    spec_header_row = None
    for i in range(len(raw)):
        cell = str(raw.iloc[i, 0]).strip()
        if cell.lower() in ("name:", "name"):
            spec_header_row = i
            break

    if spec_header_row is None:
        raise ValueError("No se encontró la sección de especímenes.")

    header_cells = [str(c).strip().lower() for c in raw.iloc[spec_header_row]]
    thickness_col = next((i for i, h in enumerate(header_cells) if "thick" in h), 1)
    width_col     = next((i for i, h in enumerate(header_cells) if "width" in h), 2)
    span_col      = next((i for i, h in enumerate(header_cells) if "support" in h or "span" in h or "lower" in h), 3)

    i = spec_header_row + 2
    specimen_order: list[str] = []
    specimen_props: dict[str, FlexionSpecimen] = {}

    while i < len(raw):
        name_raw = raw.iloc[i, 0]
        if pd.isna(name_raw) or str(name_raw).strip() == "":
            break
        name = str(name_raw).strip()
        sp = FlexionSpecimen(
            name=name,
            thickness_mm=_safe_float(raw.iloc[i, thickness_col]),
            width_mm=_safe_float(raw.iloc[i, width_col]),
            span_mm=_safe_float(raw.iloc[i, span_col]),
        )
        specimen_order.append(name)
        specimen_props[name] = sp
        i += 1

    # --- Tabla resumen ---
    summary_header_row = None
    for i in range(len(raw)):
        row_vals = [str(v).strip().lower() for v in raw.iloc[i]]
        if row_vals[0] == "name" and any("force" in v for v in row_vals[1:]):
            summary_header_row = i
            break

    if summary_header_row is not None:
        data_start = summary_header_row + 3
        col_names = [str(raw.iloc[summary_header_row, c]).strip() for c in range(raw.shape[1])]

        def find_col(keywords: list[str]) -> int | None:
            for kw in keywords:
                for ci, cn in enumerate(col_names):
                    if kw.lower() in cn.lower():
                        return ci
            return None

        c_mf  = find_col(["Max_Force", "Max Force"])
        c_md  = find_col(["Max_Disp",  "Max Disp"])
        c_ms  = find_col(["Max_Stress","Max Stress"])
        c_mst = find_col(["Max_Strain","Max Strain"])

        for i in range(data_start, len(raw)):
            name_raw = raw.iloc[i, 0]
            if pd.isna(name_raw):
                break
            name = str(name_raw).strip()
            if name not in specimen_props:
                continue
            sp = specimen_props[name]
            if c_mf  is not None: sp.max_force_N   = _safe_float(raw.iloc[i, c_mf])
            if c_md  is not None: sp.max_disp_mm    = _safe_float(raw.iloc[i, c_md])
            if c_ms  is not None: sp.max_stress_MPa = _safe_float(raw.iloc[i, c_ms])
            if c_mst is not None: sp.max_strain_pct = _safe_float(raw.iloc[i, c_mst])

    data.specimens = [specimen_props[n] for n in specimen_order]
    return data


def _parse_csv(path: Path) -> FlexionData:
    sep = "\t" if path.suffix.lower() == ".txt" else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip() for c in df.columns]
    data = FlexionData()

    # Intentar leer tabla directa Name, Max_Force, Max_Disp, Max_Stress, Max_Strain
    name_col   = next((c for c in df.columns if "name" in c.lower()), None)
    force_col  = next((c for c in df.columns if "force" in c.lower()), None)
    disp_col   = next((c for c in df.columns if "disp" in c.lower()), None)
    stress_col = next((c for c in df.columns if "stress" in c.lower()), None)
    strain_col = next((c for c in df.columns if "strain" in c.lower()), None)

    for _, row in df.iterrows():
        name = str(row[name_col]).strip() if name_col else f"Espécimen"
        sp = FlexionSpecimen(name=name, thickness_mm=4.0, width_mm=10.0, span_mm=60.0)
        if force_col:  sp.max_force_N   = _safe_float(row[force_col])
        if disp_col:   sp.max_disp_mm   = _safe_float(row[disp_col])
        if stress_col: sp.max_stress_MPa= _safe_float(row[stress_col])
        if strain_col: sp.max_strain_pct= _safe_float(row[strain_col])
        data.specimens.append(sp)

    return data


def parse(path: str | Path) -> FlexionData:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    suffix = p.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return _parse_xlsx(p)
    if suffix in (".csv", ".txt"):
        return _parse_csv(p)
    raise ValueError(f"Formato no soportado: {suffix}")
