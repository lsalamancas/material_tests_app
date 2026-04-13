"""
Procesamiento estadístico para ensayo de impacto (ASTM D256).

La energía y tenacidad ya vienen calculadas por el equipo.
Aquí se organizan y presentan los resultados estadísticos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.parsers.impact_parser import ImpactData, ImpactSpecimen


@dataclass
class ImpactSummary:
    specimens: list[ImpactSpecimen] = field(default_factory=list)
    n: int = 0

    mean_energy_J: float = float("nan")
    std_energy_J: float = float("nan")
    min_energy_J: float = float("nan")
    max_energy_J: float = float("nan")
    cv_energy_pct: float = float("nan")  # Coeficiente de variación

    mean_toughness: float = float("nan")
    std_toughness: float = float("nan")
    min_toughness: float = float("nan")
    max_toughness: float = float("nan")
    cv_toughness_pct: float = float("nan")


def summarize(data: ImpactData) -> ImpactSummary:
    summary = ImpactSummary(specimens=data.specimens)
    valid = [s for s in data.specimens if not np.isnan(s.energy_J)]
    summary.n = len(valid)

    if not valid:
        return summary

    energies     = np.array([s.energy_J for s in valid])
    toughnesses  = np.array([s.toughness_J_mm2 for s in valid])

    summary.mean_energy_J  = float(np.mean(energies))
    summary.std_energy_J   = float(np.std(energies, ddof=1)) if len(energies) > 1 else 0.0
    summary.min_energy_J   = float(np.min(energies))
    summary.max_energy_J   = float(np.max(energies))
    if summary.mean_energy_J > 0:
        summary.cv_energy_pct = (summary.std_energy_J / summary.mean_energy_J) * 100

    valid_t = toughnesses[~np.isnan(toughnesses)]
    if len(valid_t):
        summary.mean_toughness = float(np.mean(valid_t))
        summary.std_toughness  = float(np.std(valid_t, ddof=1)) if len(valid_t) > 1 else 0.0
        summary.min_toughness  = float(np.min(valid_t))
        summary.max_toughness  = float(np.max(valid_t))
        if summary.mean_toughness > 0:
            summary.cv_toughness_pct = (summary.std_toughness / summary.mean_toughness) * 100

    return summary
