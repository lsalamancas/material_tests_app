"""
Cálculo de propiedades mecánicas para ensayo de flexión de 3 puntos.

Fórmulas (viga simplemente apoyada, carga central):
  σ_max = (3 × F × L) / (2 × b × h²)     [N/mm² = MPa]
  δ_max = desplazamiento máximo            [mm]
  ε_max = (6 × h × δ) / L²               [sin unidades → %]
  E_flex = (F × L³) / (4 × b × h³ × δ)  [MPa]

donde:
  F = fuerza máxima [N]
  L = luz libre (span) [mm]
  b = ancho [mm]
  h = espesor [mm]
  δ = desplazamiento en el punto de carga [mm]
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.parsers.flexion_parser import FlexionSpecimen


@dataclass
class FlexionProperties:
    specimen_name: str

    flexural_strength_MPa: float = float("nan")   # Resistencia máxima a flexión
    flexural_modulus_MPa: float = float("nan")     # Módulo de flexión (E_flex)
    max_strain_pct: float = float("nan")           # Deformación máxima en fibra exterior
    max_force_N: float = float("nan")
    max_disp_mm: float = float("nan")

    # Verificación: esfuerzo calculado vs. reportado
    stress_from_file_MPa: float = float("nan")


def calculate(specimen: FlexionSpecimen) -> FlexionProperties:
    props = FlexionProperties(specimen_name=specimen.name)

    F = specimen.max_force_N
    L = specimen.span_mm
    b = specimen.width_mm
    h = specimen.thickness_mm
    delta = specimen.max_disp_mm

    props.max_force_N = F
    props.max_disp_mm = delta
    props.stress_from_file_MPa = specimen.max_stress_MPa

    if any(np.isnan(x) for x in (F, L, b, h)):
        return props

    # Resistencia a flexión
    if b > 0 and h > 0:
        props.flexural_strength_MPa = (3 * F * L) / (2 * b * h ** 2)

    # Módulo de flexión (requiere desplazamiento)
    if not np.isnan(delta) and delta > 0 and b > 0 and h > 0:
        props.flexural_modulus_MPa = (F * L ** 3) / (4 * b * h ** 3 * delta)

    # Deformación máxima en la fibra exterior [%]
    if not np.isnan(delta) and L > 0:
        props.max_strain_pct = (6 * h * delta / L ** 2) * 100

    return props


def calculate_all(specimens: list[FlexionSpecimen]) -> list[FlexionProperties]:
    return [calculate(sp) for sp in specimens]
