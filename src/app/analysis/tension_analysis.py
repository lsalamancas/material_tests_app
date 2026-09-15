"""
Cálculo de propiedades mecánicas para ensayo de tracción.

Propiedades calculadas:
- Módulo de Young (E) — regresión lineal en la región elástica inicial
- Límite proporcional (σp) — donde comienza desviación de linealidad
- Límite elástico (σy) — método del 0.2% de deformación compensada (offset)
- Resistencia máxima a tracción (UTS)
- Deformación de rotura
- Resiliencia — capacidad de absorber energía elástica (σy²/2E)
- Tenacidad — área bajo la curva esfuerzo-deformación (energía total)
- Identificación de regiones elástica, plástica y de estricción (necking)
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
    proportional_limit_MPa: float = float("nan")  # Límite proporcional
    proportional_limit_strain_pct: float = float("nan")  # Deformación en límite proporcional
    yield_stress_MPa: float = float("nan")      # Límite elástico 0.2% offset
    yield_strain_pct: float = float("nan")
    uts_MPa: float = float("nan")               # Resistencia máxima (UTS)
    uts_strain_pct: float = float("nan")
    break_stress_MPa: float = float("nan")
    break_strain_pct: float = float("nan")
    resilience_MJ_m3: float = float("nan")      # Resiliencia (capacidad de recuperación elástica)
    toughness_MJ_m3: float = float("nan")       # Área bajo la curva (MJ/m³)

    # Identificación de regiones (deformación donde comienza cada región)
    elastic_end_strain_pct: float = float("nan")       # Deformación final de región elástica
    plastic_start_strain_pct: float = float("nan")     # Deformación inicial de región plástica
    necking_start_strain_pct: float = float("nan")     # Deformación donde comienza estricción
    necking_start_stress_MPa: float = float("nan")     # Esfuerzo donde comienza estricción

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
        # El tramo realmente regresionado es strain[0:end] (índice `end`
        # excluido) — comparar contra strain[end-1], no strain[end], que no
        # forma parte de la regresión. Con la comparación original, curvas
        # crudas con varios puntos iniciales de desplazamiento idéntico
        # (recorrido/holgura de mordazas antes de tomar carga — común en
        # exportaciones directas del equipo, a diferencia de los .xlsx ya
        # procesados) colaban un tramo [0:end] con varianza cero en x y
        # scipy.stats.linregress lanzaba ValueError.
        if strain[end - 1] - strain[0] < 1e-10:
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


def _proportional_limit(strain_pct: np.ndarray, stress_MPa: np.ndarray,
                        E_MPa: float) -> tuple[float, int]:
    """
    Calcula el límite proporcional detectando dónde se pierde la linealidad.
    Usa desviación porcentual del esfuerzo máximo como criterio.
    Retorna (stress_MPa, índice).
    """
    if np.isnan(E_MPa) or E_MPa <= 0 or len(stress_MPa) < 5:
        return float("nan"), 0

    strain_frac = strain_pct / 100.0
    expected_stress = E_MPa * strain_frac
    max_stress = np.max(stress_MPa)

    # Error absoluto normalizado por el máximo esfuerzo
    # Criterio: desviación > 2% del esfuerzo máximo
    error_abs = np.abs(stress_MPa - expected_stress)
    threshold = 0.02 * max_stress

    # Buscar a partir del punto 5 para evitar ruido inicial
    above_threshold = np.where(error_abs[5:] > threshold)[0]

    if len(above_threshold) > 0:
        idx = above_threshold[0] + 5  # Ajustar índice
        if idx > 1:
            idx -= 1  # Retroceder un paso
        return float(stress_MPa[idx]), int(idx)

    # Si nunca se desvia significativamente, retornar punto a ~70% de UTS
    max_idx = int(np.argmax(stress_MPa))
    proportional_idx = max(5, int(max_idx * 0.4))  # Usar ~40% del camino a UTS
    return float(stress_MPa[proportional_idx]), int(proportional_idx)


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


def _detect_necking_region(strain_pct: np.ndarray, stress_MPa: np.ndarray,
                           uts_idx: int) -> int:
    """
    Detecta el inicio de la estricción (necking) como donde comienza
    a disminuir significativamente la sección transversal.
    Aproximado por: donde la pendiente se hace más negativa después de UTS.
    """
    if uts_idx >= len(stress_MPa) - 5:
        return uts_idx

    # Después de UTS, calcular segunda derivada para detectar aceleración en caída
    post_uts = stress_MPa[uts_idx:]

    # Calcular pendientes en ventanas
    for i in range(len(post_uts) - 1):
        if i > 0:
            slope_current = post_uts[i + 1] - post_uts[i]
            slope_prev = post_uts[i] - post_uts[i - 1]

            # Si la caída se acelera significativamente (2x más negativa)
            if slope_current < 0 and slope_prev < 0:
                if abs(slope_current) > 2 * abs(slope_prev):
                    return uts_idx + i

    return uts_idx


def calculate(specimen: TensionSpecimen, offset_pct: float = 0.2) -> TensionProperties:
    """
    Calcula propiedades de tracción.

    Args:
        specimen: Datos del espécimen
        offset_pct: Parámetro de deformación compensada (default 0.2%, típico para aceros)
    """
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

    # Ignorar los primeros 10 puntos (acomodamiento inicial de la máquina)
    # para evitar la "U" inicial anómala que no es física
    if len(stress) > 15:
        stress = stress[10:]
        strain = strain[10:]
    elif len(stress) > 10:
        stress = stress[5:]
        strain = strain[5:]

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
        props.elastic_end_strain_pct = float(strain[e_idx])
        # Corregir: E está en MPa cuando strain es fracción, así que multiplicar por strain/100
        props.elastic_stress_fit = E * (strain[s_idx:e_idx + 1] / 100.0)

    # Límite proporcional
    sp, p_idx = _proportional_limit(strain, stress, E)
    props.proportional_limit_MPa = sp
    if p_idx < len(strain):
        props.proportional_limit_strain_pct = float(strain[p_idx])
        props.plastic_start_strain_pct = float(strain[p_idx])

    # Límite elástico con offset variable
    sy, ey = _yield_stress_offset(strain, stress, E, offset=offset_pct)
    props.yield_stress_MPa = sy
    props.yield_strain_pct = ey

    # Resiliencia = σy² / (2E) = área bajo la curva elástica hasta límite elástico
    # En términos de energía: (1/2) × σy × εy o σy² / (2E)
    if not np.isnan(sy) and not np.isnan(E) and E > 0:
        resilience_strain = sy / E  # En fracción
        props.resilience_MJ_m3 = (sy * resilience_strain / 2.0) / 100.0  # Convertir a MJ/m³

    if not np.isnan(sy) and not np.isnan(E):
        # Línea offset para graficar — extender desde 0 hasta más allá de UTS
        offset_frac = offset_pct / 100
        s_range = np.linspace(0, strain[max_idx] * 1.15, 100)
        props.offset_strain_range = s_range
        props.offset_stress_line = E * (s_range / 100.0 - offset_frac)

    # Detectar región de estricción (necking)
    necking_idx = _detect_necking_region(strain, stress, max_idx)
    if necking_idx < len(strain):
        props.necking_start_strain_pct = float(strain[necking_idx])
        props.necking_start_stress_MPa = float(stress[necking_idx])

    # Tenacidad = área bajo la curva σ-ε (trapz, en MPa·% → ÷100 para fracción → MJ/m³)
    toughness_MPa_pct = float(np.trapezoid(stress, strain))
    props.toughness_MJ_m3 = toughness_MPa_pct / 100.0  # MPa·(%) → MJ/m³

    return props
