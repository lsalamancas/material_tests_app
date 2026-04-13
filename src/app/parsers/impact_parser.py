"""
Parser para archivos de ensayo de impacto (ASTM D256 — Charpy/Izod).

Estructura del archivo:
- Fila 1: Standard, ASTM D256, Batch Number, nombre
- Fila 2: Type: V, Deep (mm): 2.54
- Fila 3: encabezados (Sn, Area, Energy, Toughness)
- Fila 4: unidades ([mm²], [J], ...)
- Filas 5-15: datos por espécimen
- Filas 20-23: estadísticas (Min, Max, Mean, Std Dev)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ImpactSpecimen:
    number: int
    area_mm2: float
    energy_J: float
    toughness_J_mm2: float


@dataclass
class ImpactData:
    standard: str = "ASTM D256"
    notch_type: str = "V"
    notch_depth_mm: float = 2.54
    batch_name: str = ""

    specimens: list[ImpactSpecimen] = field(default_factory=list)

    # Estadísticas (precalculadas en el archivo o calculadas internamente)
    min_energy_J: float = float("nan")
    max_energy_J: float = float("nan")
    mean_energy_J: float = float("nan")
    std_energy_J: float = float("nan")

    min_toughness: float = float("nan")
    max_toughness: float = float("nan")
    mean_toughness: float = float("nan")
    std_toughness: float = float("nan")

    def recalc_stats(self) -> None:
        energies   = [s.energy_J      for s in self.specimens if not np.isnan(s.energy_J)]
        toughnesses= [s.toughness_J_mm2 for s in self.specimens if not np.isnan(s.toughness_J_mm2)]
        if energies:
            self.min_energy_J  = float(np.min(energies))
            self.max_energy_J  = float(np.max(energies))
            self.mean_energy_J = float(np.mean(energies))
            self.std_energy_J  = float(np.std(energies, ddof=1))
        if toughnesses:
            self.min_toughness  = float(np.min(toughnesses))
            self.max_toughness  = float(np.max(toughnesses))
            self.mean_toughness = float(np.mean(toughnesses))
            self.std_toughness  = float(np.std(toughnesses, ddof=1))


def _safe_float(value) -> float:
    try:
        f = float(value)
        return f if not np.isnan(f) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _parse_xlsx(path: Path) -> ImpactData:
    raw = pd.read_excel(path, sheet_name=0, header=None)
    data = ImpactData()

    # Fila 0: Standard y batch
    try:
        data.standard   = str(raw.iloc[0, 1]).strip()
        data.batch_name = str(raw.iloc[0, 3]).strip()
    except Exception:
        pass

    # Fila 1: notch type y depth
    try:
        type_cell  = str(raw.iloc[1, 1]).strip()
        depth_cell = str(raw.iloc[1, 3]).strip()
        data.notch_type = type_cell.replace("Type:", "").strip().split()[0] if type_cell else "V"
        data.notch_depth_mm = float(depth_cell) if depth_cell else 2.54
    except Exception:
        pass

    # Fila 2: encabezados (Sn, Area, Energy, Toughness)
    header_row = 2
    headers = [str(raw.iloc[header_row, c]).strip().lower() for c in range(raw.shape[1])]
    sn_col   = next((i for i, h in enumerate(headers) if "sn" in h or "number" in h or h == "#"), 0)
    area_col = next((i for i, h in enumerate(headers) if "area" in h), 1)
    energy_col     = next((i for i, h in enumerate(headers) if "energy" in h or "ener" in h), 2)
    toughness_col  = next((i for i, h in enumerate(headers) if "tough" in h), 3)

    # Fila 3: unidades — saltar
    # Filas 4+: datos
    stats_labels = {"min", "max", "mean", "average", "std", "desv", "stdev"}
    stat_rows: list[tuple[str, int]] = []

    for i in range(header_row + 2, len(raw)):
        sn_val = raw.iloc[i, sn_col]
        if pd.isna(sn_val):
            continue

        sn_str = str(sn_val).strip().lower()

        # Detectar filas de estadísticas
        if any(lab in sn_str for lab in stats_labels):
            stat_rows.append((sn_str, i))
            continue

        # Plantillas vacías del formato (contienen "&")
        if "&" in sn_str:
            continue

        try:
            sn_int = int(float(sn_val))
        except (ValueError, TypeError):
            continue

        sp = ImpactSpecimen(
            number=sn_int,
            area_mm2=_safe_float(raw.iloc[i, area_col]),
            energy_J=_safe_float(raw.iloc[i, energy_col]),
            toughness_J_mm2=_safe_float(raw.iloc[i, toughness_col]),
        )
        data.specimens.append(sp)

    # Leer estadísticas del archivo
    for label, row_i in stat_rows:
        e = _safe_float(raw.iloc[row_i, energy_col])
        t = _safe_float(raw.iloc[row_i, toughness_col])
        if "min" in label:
            data.min_energy_J = e; data.min_toughness = t
        elif "max" in label:
            data.max_energy_J = e; data.max_toughness = t
        elif "mean" in label or "average" in label:
            data.mean_energy_J = e; data.mean_toughness = t
        elif "std" in label or "desv" in label:
            data.std_energy_J = e; data.std_toughness = t

    # Si las stats no estaban en el archivo, calcularlas
    if np.isnan(data.mean_energy_J):
        data.recalc_stats()

    return data


def _parse_csv(path: Path) -> ImpactData:
    sep = "\t" if path.suffix.lower() == ".txt" else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [c.strip() for c in df.columns]
    data = ImpactData()

    sn_col   = next((c for c in df.columns if "sn" in c.lower() or "num" in c.lower()), None)
    area_col = next((c for c in df.columns if "area" in c.lower()), None)
    energy_col    = next((c for c in df.columns if "energy" in c.lower()), None)
    tough_col     = next((c for c in df.columns if "tough" in c.lower()), None)

    for idx, row in df.iterrows():
        try:
            sn = int(float(row[sn_col])) if sn_col else idx + 1
        except Exception:
            sn = idx + 1
        sp = ImpactSpecimen(
            number=sn,
            area_mm2=_safe_float(row[area_col]) if area_col else float("nan"),
            energy_J=_safe_float(row[energy_col]) if energy_col else float("nan"),
            toughness_J_mm2=_safe_float(row[tough_col]) if tough_col else float("nan"),
        )
        data.specimens.append(sp)

    data.recalc_stats()
    return data


def parse(path: str | Path) -> ImpactData:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    suffix = p.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return _parse_xlsx(p)
    if suffix in (".csv", ".txt"):
        return _parse_csv(p)
    raise ValueError(f"Formato no soportado: {suffix}")
