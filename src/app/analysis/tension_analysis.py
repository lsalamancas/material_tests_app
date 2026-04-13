"""
Cálculo de propiedades mecánicas para ensayo de tracción.

Propiedades calculadas:
- Módulo de Young (E) — regresión lineal en la región elástica inicial
- Límite elástico (σy) — método del 0.2% de deformación compensada (offset)
- Resistencia máxima a tracción (UTS)
- Deformación de rotura
- Tenacidad (área bajo la curva esfuerzo-deformación)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as scipy_stats

from app.parsers.tension_parser import TensionSpecimen


@dataclass
class TensionProperties:
    specimen_name: str

    # Propiedades calculadas de la curva
    youngs_modulus_MPa: float = float("nan")   # Pendiente de la región lineal
    yield_stress_MPa: float = float("nan")      # Límite elástico 0.2% offset
    yield_strain_pct: float = float("nan")
    uts_MPa: float = float("nan")               # Resistencia máxima (UTS)
    uts_strain_pct: float = float("nan")
    break_stress_MPa: float = float("nan")
    break_strain_pct: float = float("nan")
    toughness_MJ_m3: float = float("nan")       # Área bajo la curva (MJ/m³)

    # Datos para graficar la línea de módulo y la línea offset
    elastic_strain_range: np.ndarray | None = None
    elastic_stress_fit: np.ndarray | None = None
    offset_strain_range: np.ndarray | None = None
    offset_stress_line: np.ndarray | None = None


def _find_linear_region(strain: np.ndarray, stress: np.ndarray,
                        max_fraction: float = 0.4) -> tuple[int, int]:
    """
    Detecta la región lineal inicial usando correlación de Pearson en ventanas deslizantes.
    Retorna (start_idx, end_idx) del mejor tramo lineal.
    """
    n = len(strain)
    if n < 5:
        return 0, n - 1

    # Tomamos hasta el max_fraction del esfuerzo máximo como candidato
    max_stress = np.max(stress)
    upper_limit = max_stress * max_fraction
    end_candidate = int(np.searchsorted(stress, upper_limit))
    end_candidate = max(end_candidate, 5)
    end_candidate = min(end_candidate, n - 1)

    best_r2 = -1.0
    best_end = end_candidate

    # Buscar el tramo desde 0 hasta el punto que maximice R²
    for end in range(5, end_candidate + 1):
        if strain[end] - strain[0] < 1e-10:
            continue
        slope, intercept, r, *_ = scipy_stats.linregress(strain[0:end], stress[0:end])
        r2 = r ** 2
        if r2 > best_r2:
            best_r2 = r2
            best_end = end

    return 0, best_end


def _young_modulus(strain_pct: np.ndarray, stress_MPa: np.ndarray) -> tuple[float, int, int]:
    """Retorna (E en MPa, start_idx, end_idx) del ajuste lineal."""
    strain_frac = strain_pct / 100.0  # Convertir a fracción
    start, end = _find_linear_region(strain_frac, stress_MPa)
    if end - start < 2:
        return float("nan"), 0, 0
    slope, _, _, _, _ = scipy_stats.linregress(strain_frac[start:end+1],
                                                stress_MPa[start:end+1])
    return float(slope), start, end


def _yield_stress_offset(strain_pct: np.ndarray, stress_MPa: np.ndarray,
                          E_MPa: float, offset: float = 0.2) -> tuple[float, float]:
    """
    Método del 0.2% de deformación compensada.
    La línea offset parte de strain = offset% con pendiente E.
    Retorna (yield_stress_MPa, yield_strain_pct).
    """
    if np.isnan(E_MPa) or E_MPa <= 0:
        return float("nan"), float("nan")

    # Línea offset: σ = E × (ε - offset/100)
    offset_frac = offset / 100.0
    # Puntos de intersección: E * (strain/100 - offset_frac) == stress
    # → encontrar cruce entre la curva real y la línea offset
    strain_frac = strain_pct / 100.0
    offset_stress = E_MPa * (strain_frac - offset_frac)

    diff = stress_MPa - offset_stress
    # Buscar cambio de signo (la curva real cruza la línea offset)
    sign_changes = np.where(np.diff(np.sign(diff)))[0]

    if len(sign_changes) == 0:
        return float("nan"), float("nan")

    idx = sign_changes[0]
    # Interpolación lineal
    s0, s1 = strain_frac[idx], strain_frac[idx + 1]
    d0, d1 = diff[idx], diff[idx + 1]
    if abs(d1 - d0) < 1e-12:
        return float("nan"), float("nan")

    strain_yield = s0 - d0 * (s1 - s0) / (d1 - d0)
    stress_yield = E_MPa * (strain_yield - offset_frac)

    return float(stress_yield), float(strain_yield * 100)


def calculate(specimen: TensionSpecimen) -> TensionProperties:
    props = TensionProperties(specimen_name=specimen.name)

    stress = specimen.stress_MPa
    strain = specimen.strain_pct

    if len(stress) < 5 or len(strain) < 5:
        # Sin datos de curva — usar resumen del archivo
        props.uts_MPa         = specimen.max_stress_MPa
        props.uts_strain_pct  = specimen.max_strain_pct
        props.break_stress_MPa= specimen.break_stress_MPa
        props.break_strain_pct= specimen.break_strain_pct
        props.youngs_modulus_MPa = specimen.elastic_modulus_MPa
        return props

    # Eliminar valores iniciales negativos o cero en fuerza
    valid = stress > 0
    stress = stress[valid]
    strain = strain[valid]

    if len(stress) < 5:
        return props

    # UTS
    max_idx = int(np.argmax(stress))
    props.uts_MPa        = float(stress[max_idx])
    props.uts_strain_pct = float(strain[max_idx])

    # Rotura (último punto significativo — caída brusca de carga)
    props.break_stress_MPa = float(stress[-1])
    props.break_strain_pct = float(strain[-1])

    # Módulo de Young
    E, s_idx, e_idx = _young_modulus(strain, stress)
    props.youngs_modulus_MPa = E

    if e_idx > s_idx:
        props.elastic_strain_range = strain[s_idx:e_idx + 1]
        props.elastic_stress_fit   = (E / 100) * strain[s_idx:e_idx + 1]

    # Límite elástico 0.2% offset
    sy, ey = _yield_stress_offset(strain, stress, E)
    props.yield_stress_MPa = sy
    props.yield_strain_pct = ey

    if not np.isnan(sy) and not np.isnan(E):
        # Línea offset para graficar
        offset_frac = 0.2 / 100
        s_range = np.linspace(0.2, strain[max_idx], 100)
        props.offset_strain_range = s_range
        props.offset_stress_line  = (E / 100) * (s_range / 100 - offset_frac) * 100 * 100

        # Recalcular correctamente
        props.offset_stress_line = E * (s_range / 100 - offset_frac)

    # Tenacidad = área bajo la curva σ-ε (trapz, en MPa·% → ÷100 para fracción → MJ/m³)
    toughness_MPa_pct = float(np.trapezoid(stress, strain))
    props.toughness_MJ_m3 = toughness_MPa_pct / 100.0  # MPa·(%) → MJ/m³

    return props
