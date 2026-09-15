"""
Material Testing Analyzer — versión web (Streamlit).

Reutiliza exactamente los mismos módulos de parsing y análisis que la app
de escritorio (src/app/parsers, src/app/analysis, src/app/ui/plotly_exports).
No importa nada de PyQt6/matplotlib — por eso puede correr en un contenedor
headless sin dependencias gráficas de sistema.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.parsers import flexion_parser, impact_parser, tension_parser  # noqa: E402
from app.analysis import flexion_analysis, impact_analysis, tension_analysis  # noqa: E402
from app.ui import plotly_exports  # noqa: E402

COLORS = [
    "#1976D2", "#D32F2F", "#388E3C", "#F57C00", "#7B1FA2",
    "#0097A7", "#C62828", "#558B2F", "#4527A0", "#00838F", "#AD1457",
]

st.set_page_config(page_title="Material Testing Analyzer", page_icon="📐", layout="wide")


def _save_upload(uploaded) -> Path:
    suffix = Path(uploaded.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getvalue())
    tmp.close()
    return Path(tmp.name)


def _fmt(value: float, unit: str = "", decimals: int = 2) -> str:
    if value is None or np.isnan(value):
        return "–"
    return f"{value:.{decimals}f} {unit}".strip()


def _agg(props: list, indices: list[int], attr: str) -> list[float]:
    return [getattr(props[i], attr) for i in indices if not np.isnan(getattr(props[i], attr))]


# --------------------------------------------------------------------- Tracción
def tension_tab() -> None:
    st.subheader("Ensayo de tracción")
    uploaded = st.file_uploader(
        "Archivo de tracción (.xlsx del equipo, o .csv/.txt de curva cruda)",
        type=["xlsx", "xls", "csv", "txt"], key="tension_file",
    )
    if uploaded is None:
        st.info("Carga un archivo para comenzar.")
        return

    path = _save_upload(uploaded)
    try:
        data = tension_parser.parse(path)
    except Exception as exc:
        st.error(f"No se pudo leer el archivo: {exc}")
        return
    finally:
        path.unlink(missing_ok=True)

    if not data.specimens:
        st.warning("No se encontraron especímenes en el archivo.")
        return

    missing_geom = [
        sp for sp in data.specimens
        if np.isnan(sp.thickness_mm) or np.isnan(sp.width_mm) or np.isnan(sp.gauge_length_mm)
    ]
    if missing_geom:
        st.warning(
            f"{len(missing_geom)} espécimen(es) no traen geometría en el archivo "
            "(este formato exporta solo la curva cruda tiempo/fuerza/desplazamiento). "
            "Complétala para poder calcular esfuerzo–deformación:"
        )
        geom_df = pd.DataFrame({
            "Espécimen": [sp.name for sp in data.specimens],
            "Espesor (mm)": pd.Series([sp.thickness_mm for sp in data.specimens], dtype="float64"),
            "Ancho (mm)": pd.Series([sp.width_mm for sp in data.specimens], dtype="float64"),
            "Long. calibrada (mm)": pd.Series([sp.gauge_length_mm for sp in data.specimens], dtype="float64"),
        })
        edited = st.data_editor(
            geom_df, hide_index=True, key="tension_geom_editor",
            disabled=["Espécimen"],
            column_config={
                "Espesor (mm)": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.3f"),
                "Ancho (mm)": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.3f"),
                "Long. calibrada (mm)": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.3f"),
            },
        )
        for i, sp in enumerate(data.specimens):
            sp.thickness_mm = float(edited.loc[i, "Espesor (mm)"])
            sp.width_mm = float(edited.loc[i, "Ancho (mm)"])
            sp.gauge_length_mm = float(edited.loc[i, "Long. calibrada (mm)"])

    offset_pct = st.slider(
        "Offset para límite elástico (σy)", min_value=0.01, max_value=2.0,
        value=0.2, step=0.01, format="%.2f%%",
    )

    names = [sp.name for sp in data.specimens]
    selected_names = st.multiselect("Especímenes", names, default=names, key="tension_specimens")
    indices = [i for i, n in enumerate(names) if n in selected_names]

    props = [tension_analysis.calculate(sp, offset_pct=offset_pct) for sp in data.specimens]

    if indices:
        fig = plotly_exports.create_tension_plot(data.specimens, props, indices, COLORS, offset_pct)
        st.plotly_chart(fig, use_container_width=True)
        st.download_button(
            "📊 Descargar gráfico HTML interactivo",
            data=fig.to_html(), file_name="traccion.html", mime="text/html",
        )
    else:
        st.info("Selecciona al menos un espécimen para graficar.")

    st.markdown("#### Propiedades mecánicas")
    if len(indices) == 1:
        p = props[indices[0]]
        rows = [
            ("Espécimen", p.specimen_name),
            ("Módulo de Young (E)", _fmt(p.youngs_modulus_MPa, "MPa", 0)),
            ("Límite proporcional", _fmt(p.proportional_limit_MPa, "MPa")),
            ("Límite elástico (σy)", _fmt(p.yield_stress_MPa, "MPa")),
            ("Deform. en σy", _fmt(p.yield_strain_pct, "%", 3)),
            ("Resiliencia", _fmt(p.resilience_MJ_m3, "MJ/m³", 4)),
            ("UTS", _fmt(p.uts_MPa, "MPa")),
            ("Deform. en UTS", _fmt(p.uts_strain_pct, "%", 3)),
            ("Esfuerzo de rotura", _fmt(p.break_stress_MPa, "MPa")),
            ("Deform. de rotura", _fmt(p.break_strain_pct, "%", 3)),
            ("Tenacidad", _fmt(p.toughness_MJ_m3, "MJ/m³", 3)),
        ]
        st.table(pd.DataFrame(rows, columns=["Propiedad", "Valor"]))
    elif len(indices) > 1:
        def _row(label: str, attr: str, unit: str, decimals: int = 2) -> tuple[str, str]:
            vals = _agg(props, indices, attr)
            if not vals:
                return (label, "–")
            if len(vals) > 1:
                return (label, f"{np.mean(vals):.{decimals}f} ± {np.std(vals, ddof=1):.{decimals}f} {unit}")
            return (label, f"{np.mean(vals):.{decimals}f} {unit}")

        rows = [
            ("Especímenes", str(len(indices))),
            _row("E (promedio ± std)", "youngs_modulus_MPa", "MPa", 0),
            _row("σy (promedio ± std)", "yield_stress_MPa", "MPa"),
            _row("UTS (promedio ± std)", "uts_MPa", "MPa"),
            _row("Resiliencia (promedio)", "resilience_MJ_m3", "MJ/m³", 4),
            _row("Tenacidad (promedio)", "toughness_MJ_m3", "MJ/m³", 3),
        ]
        st.table(pd.DataFrame(rows, columns=["Propiedad", "Valor"]))

    with st.expander("Ver todas las propiedades por espécimen"):
        full_df = pd.DataFrame([{
            "Espécimen": p.specimen_name,
            "E (MPa)": p.youngs_modulus_MPa,
            "σp (MPa)": p.proportional_limit_MPa,
            "σy (MPa)": p.yield_stress_MPa,
            "UTS (MPa)": p.uts_MPa,
            "ε_UTS (%)": p.uts_strain_pct,
            "σ_rotura (MPa)": p.break_stress_MPa,
            "ε_rotura (%)": p.break_strain_pct,
            "Resiliencia (MJ/m³)": p.resilience_MJ_m3,
            "Tenacidad (MJ/m³)": p.toughness_MJ_m3,
        } for p in props])
        st.dataframe(full_df, use_container_width=True)


# --------------------------------------------------------------------- Flexión
def flexion_tab() -> None:
    st.subheader("Ensayo de flexión (3 puntos)")
    uploaded = st.file_uploader(
        "Archivo de flexión (.xlsx del equipo, o .csv/.txt)",
        type=["xlsx", "xls", "csv", "txt"], key="flexion_file",
    )
    if uploaded is None:
        st.info("Carga un archivo para comenzar.")
        return

    path = _save_upload(uploaded)
    try:
        data = flexion_parser.parse(path)
    except Exception as exc:
        st.error(f"No se pudo leer el archivo: {exc}")
        return
    finally:
        path.unlink(missing_ok=True)

    if not data.specimens:
        st.warning("No se encontraron especímenes en el archivo.")
        return

    props = flexion_analysis.calculate_all(data.specimens)
    names = [p.specimen_name for p in props]
    selected = st.multiselect("Especímenes", names, default=names, key="flexion_specimens")
    indices = [i for i, n in enumerate(names) if n in selected]

    attrs = {
        "Resistencia a flexión (MPa)": "flexural_strength_MPa",
        "Módulo de flexión (MPa)": "flexural_modulus_MPa",
        "Deformación máxima (%)": "max_strain_pct",
        "Fuerza máxima (N)": "max_force_N",
    }
    label = st.selectbox("Variable a graficar", list(attrs.keys()), key="flexion_attr")

    if indices:
        fig = plotly_exports.create_flexion_plot(props, indices, COLORS, attrs[label], label)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecciona al menos un espécimen para graficar.")

    df = pd.DataFrame([{
        "Espécimen": p.specimen_name,
        "Resistencia (MPa)": p.flexural_strength_MPa,
        "Módulo (MPa)": p.flexural_modulus_MPa,
        "Deform. máx (%)": p.max_strain_pct,
        "Fuerza máx (N)": p.max_force_N,
        "Desplaz. máx (mm)": p.max_disp_mm,
    } for p in props])
    st.dataframe(df, use_container_width=True)


# --------------------------------------------------------------------- Impacto
def impact_tab() -> None:
    st.subheader("Ensayo de impacto (ASTM D256)")
    uploaded = st.file_uploader(
        "Archivo de impacto (.xlsx del equipo, o .csv/.txt)",
        type=["xlsx", "xls", "csv", "txt"], key="impact_file",
    )
    if uploaded is None:
        st.info("Carga un archivo para comenzar.")
        return

    path = _save_upload(uploaded)
    try:
        data = impact_parser.parse(path)
    except Exception as exc:
        st.error(f"No se pudo leer el archivo: {exc}")
        return
    finally:
        path.unlink(missing_ok=True)

    if not data.specimens:
        st.warning("No se encontraron especímenes en el archivo.")
        return

    summary = impact_analysis.summarize(data)
    var_choice = st.radio("Variable", ["Energía absorbida", "Tenacidad"], horizontal=True, key="impact_var")
    var_key = "energy" if var_choice == "Energía absorbida" else "toughness"

    indices = list(range(len(data.specimens)))
    fig = plotly_exports.create_impact_plot(data.specimens, summary, indices, COLORS, var_key)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    if var_key == "energy":
        col1.metric("Media", _fmt(summary.mean_energy_J, "J"))
        col2.metric("Desv. std", _fmt(summary.std_energy_J, "J"))
        col3.metric("Mín", _fmt(summary.min_energy_J, "J"))
        col4.metric("Máx", _fmt(summary.max_energy_J, "J"))
    else:
        col1.metric("Media", _fmt(summary.mean_toughness, "J/mm²", 4))
        col2.metric("Desv. std", _fmt(summary.std_toughness, "J/mm²", 4))
        col3.metric("Mín", _fmt(summary.min_toughness, "J/mm²", 4))
        col4.metric("Máx", _fmt(summary.max_toughness, "J/mm²", 4))

    df = pd.DataFrame([{
        "N°": s.number, "Área (mm²)": s.area_mm2,
        "Energía (J)": s.energy_J, "Tenacidad (J/mm²)": s.toughness_J_mm2,
    } for s in data.specimens])
    st.dataframe(df, use_container_width=True)


def main() -> None:
    st.title("📐 Material Testing Analyzer")
    st.caption("Análisis de ensayos de tracción, flexión e impacto")

    tabs = st.tabs(["Tracción", "Flexión", "Impacto"])
    with tabs[0]:
        tension_tab()
    with tabs[1]:
        flexion_tab()
    with tabs[2]:
        impact_tab()


main()
