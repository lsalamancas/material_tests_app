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

import education  # noqa: E402  (mismo directorio que este script)

COLORS = [
    "#1976D2", "#D32F2F", "#388E3C", "#F57C00", "#7B1FA2",
    "#0097A7", "#C62828", "#558B2F", "#4527A0", "#00838F", "#AD1457",
]

# Mismos datos/colores que TEST_TYPES en src/app/ui/home_screen.py — el
# icono usa el shortcode nativo de Streamlit (":material/x:"), Material
# Symbols de Google, en vez de emojis/unicode.
TEST_TYPES = [
    {
        "id": "tension", "label": "Tracción", "icon": "trending_up",
        "subtitle": "Curva esfuerzo–deformación · Módulo de Young · UTS · Límite elástico",
        "color": "#1976D2",
    },
    {
        "id": "flexion", "label": "Flexión", "icon": "architecture",
        "subtitle": "Ensayo 3 puntos · Módulo de flexión · Resistencia máxima",
        "color": "#388E3C",
    },
    {
        "id": "impact", "label": "Impacto", "icon": "bolt",
        "subtitle": "ASTM D256 (Charpy / Izod) · Energía absorbida · Tenacidad",
        "color": "#F57C00",
    },
]
LABEL_FOR_ID = {t["id"]: t["label"] for t in TEST_TYPES}
ICON_FOR_ID = {t["id"]: t["icon"] for t in TEST_TYPES}
COLOR_FOR_ID = {t["id"]: t["color"] for t in TEST_TYPES}

# Fotos de fondo de cada tarjeta de inicio — mismo tratamiento que el hero
# de bustral (landing_page/src/components/HeroSection.astro): foto +
# degradado del color de marca encima para que el texto siga legible.
# Generadas (no son fotos de stock con licencia incierta), servidas desde
# webapp/static/ vía server.enableStaticServing (.streamlit/config.toml) en
# la URL app/static/<archivo> — evita incrustar ~1MB de base64 por imagen
# directo en el CSS.
CARD_ART_URL = {
    "tension": "app/static/card_tension.jpeg",
    "flexion": "app/static/card_flexion.jpeg",
    "impact": "app/static/card_impact.jpeg",
}


st.set_page_config(page_title="Fertechnologies · Material Testing Analyzer", page_icon="🧪", layout="wide")


def _inject_css() -> None:
    """
    Tipografía + shell (top bar / tarjetas de inicio). Usa
    st.container(key=...), que Streamlit renderiza como
    <div class="st-key-<key>"> — permite colorear cada pieza sin depender
    de selectores frágiles por posición.
    """
    page = st.session_state.get("page", "home")
    rules = ["""
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        /* Sube el tamaño base — de esto heredan (via rem) casi todos los
           textos e inputs de Streamlit, así que un solo cambio escala toda
           la app en vez de ir componente por componente. */
        html { font-size: 18px; }

        html, body, [class*="st-key-"], .stMarkdown, .stButton, .stTextInput,
        .stSelectbox, .stMultiSelect, .stSlider, .stRadio, .stDataFrame,
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            font-family: 'Manrope', sans-serif !important;
        }
        h1 { font-weight: 800 !important; letter-spacing: -0.02em; font-size: 2.75rem !important; }
        h1, h2, h3 { font-family: 'Manrope', sans-serif !important; }
        h3 { font-size: 1.6rem !important; }
        p, label, span { font-size: 1rem; }
        [data-testid="stCaptionContainer"] p { font-size: 0.95rem !important; }
        .stMainBlockContainer { padding-top: 1.5rem; max-width: 1400px; }

        /* Top bar — dock estilo macOS: flotante, angosto, translúcido con
           blur, bordes completamente redondos. No ocupa el ancho completo
           del contenedor (max-width + margin:auto lo centra). */
        .st-key-topbar {
            background: rgba(255,255,255,0.65);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(255,255,255,0.6);
            border-radius: 999px;
            padding: 10px 28px;
            margin: 4px auto 32px auto;
            max-width: 1180px;
            box-shadow: 0 8px 32px rgba(17,24,39,0.10), 0 1px 3px rgba(17,24,39,0.06);
        }
        .st-key-logo button {
            background: transparent !important; border: none !important; box-shadow: none !important;
            color: #111827 !important; font-size: 1.4rem !important; font-weight: 800 !important;
            justify-content: flex-start !important; padding: 0 !important;
        }
        .st-key-logo button:hover { color: #1976D2 !important; }
    """]

    for pid in ["home"] + list(LABEL_FOR_ID.keys()):
        accent = COLOR_FOR_ID.get(pid, "#1976D2")
        text_color = "white" if pid == page else "#374151"
        bg = f"background:{accent} !important;box-shadow:0 4px 14px {accent}66 !important;" if pid == page else "background:transparent !important;"
        # El color hay que aplicarlo también a los hijos del botón (el label
        # de Streamlit va envuelto en div/p internos que si no, se quedan
        # con su propio color por defecto y el texto/ícono se ve invisible
        # sobre el fondo de color — mismo problema que las tarjetas de inicio.
        rules.append(f"""
            .st-key-navpill_{pid} button {{
                border-radius: 999px !important; border: none !important;
                font-weight: 700 !important; font-size: 1.15rem !important; padding: 16px 8px !important;
                transition: background .15s ease, transform .1s ease;
                {bg}
            }}
            .st-key-navpill_{pid} button, .st-key-navpill_{pid} button * {{
                color: {text_color} !important;
            }}
            .st-key-navpill_{pid} button:hover {{
                background: {accent if pid == page else 'rgba(17,24,39,0.06)'} !important;
                transform: translateY(-1px);
            }}
            .st-key-navpill_{pid} button:hover, .st-key-navpill_{pid} button:hover * {{
                color: {'white' if pid == page else accent} !important;
            }}
        """)

    for t in TEST_TYPES:
        # Tarjeta = degradado del color de marca + la ilustración del
        # ensayo asomando por la derecha, mismo tratamiento que el hero de
        # bustral (foto + gradient-to-r para que el texto de la izquierda
        # quede legible) — ver el comentario en CARD_ART_URL más arriba.
        rules.append(f"""
            .st-key-card_{t['id']} {{
                background:
                    linear-gradient(to top, {t['color']} 0%, {t['color']}F2 38%, {t['color']}A8 60%, {t['color']}55 100%),
                    url("{CARD_ART_URL[t['id']]}");
                background-size: cover, cover;
                background-position: center, center top;
                background-repeat: no-repeat, no-repeat;
                border-radius: 24px; padding: 36px 44px 40px 44px; margin-bottom: 24px;
                min-height: 280px; display: flex; flex-direction: column; justify-content: flex-end;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06); transition: transform .15s ease, box-shadow .15s ease;
            }}
            .st-key-card_{t['id']}:hover {{
                transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,0.16);
            }}
            .st-key-card_{t['id']} button {{
                background: transparent !important; border: none !important; color: white !important;
                font-size: 2.6rem !important; font-weight: 800 !important; line-height: 1.15 !important;
                justify-content: flex-start !important; padding: 0 !important; box-shadow: none !important;
                width: 100%;
            }}
            .st-key-card_{t['id']} button div, .st-key-card_{t['id']} button p {{
                text-align: left !important; justify-content: flex-start !important; width: 100%;
                font-size: 2.6rem !important; line-height: 1.15 !important;
            }}
            .st-key-card_{t['id']} button span[role="img"] {{
                font-size: 2.2rem !important;
            }}
            .st-key-card_{t['id']} [data-testid="stCaptionContainer"] p {{
                color: rgba(255,255,255,0.94) !important; font-size: 1.4rem !important; margin-top: 10px;
                line-height: 1.4 !important;
            }}
        """)

    # Franja de acento (no una barra completa — el color ya vive en el pill
    # activo de la top bar) sobre las pestañas de ensayo.
    if page in COLOR_FOR_ID:
        rules.append(f"""
            .st-key-pageaccent {{ height: 4px; border-radius: 4px; margin-bottom: 18px;
                background: {COLOR_FOR_ID[page]}; }}
        """)

    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def _go(page_id: str) -> None:
    st.session_state.page = page_id
    st.rerun()


def _render_topbar() -> None:
    with st.container(key="topbar"):
        c_logo, c_home, c_tension, c_flexion, c_impact = st.columns([2.4, 1, 1.5, 1.4, 1.4])
        with c_logo:
            with st.container(key="logo"):
                if st.button(":material/science: Material Testing Analyzer", key="logo_btn"):
                    _go("home")
        pills = [("home", "home", "Inicio"), *[(t["id"], t["icon"], t["label"]) for t in TEST_TYPES]]
        for col, (pid, icon, label) in zip([c_home, c_tension, c_flexion, c_impact], pills):
            with col:
                with st.container(key=f"navpill_{pid}"):
                    if st.button(f":material/{icon}: {label}", key=f"navbtn_{pid}", use_container_width=True):
                        _go(pid)


def _render_home() -> None:
    st.markdown(
        "<p style='text-align:center;color:#374151;font-size:1.4rem;font-weight:700;margin:8px 0 28px 0;'>"
        "Selecciona un ensayo para comenzar</p>",
        unsafe_allow_html=True,
    )
    for t in TEST_TYPES:
        with st.container(key=f"card_{t['id']}"):
            clicked = st.button(f":material/{t['icon']}: {t['label']}",
                                 key=f"cardbtn_{t['id']}", use_container_width=True)
            st.caption(t["subtitle"])
        if clicked:
            _go(t["id"])
    st.markdown(
        "<p style='text-align:center;color:#9CA3AF;font-size:0.85rem;margin-top:24px;'>"
        "Carga archivos .xlsx · .csv · .txt</p>",
        unsafe_allow_html=True,
    )


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


def _manual_mapping_ui(path: Path, display_name: str) -> tension_parser.TensionData | None:
    """
    Fallback para formatos de tracción que ninguno de los parsers
    conocidos (_parse_xlsx / _parse_csv_multi_curve / _parse_csv_single en
    tension_parser.py) reconoce. En vez de intentar anticipar cada
    máquina/software de laboratorio existente — un problema sin fondo,
    cada uno exporta con su propio idioma de encabezados, separador,
    decimal, unidades — se le pide al usuario, una sola vez por archivo,
    que indique cómo leerlo: mismo patrón que el asistente de importación
    de Excel/Google Sheets.

    Soporta un espécimen por archivo (el caso típico de "una máquina nueva
    exportó distinto"); el formato multi-espécimen en columnas paralelas ya
    lo resuelve _parse_csv_multi_curve automáticamente.
    """
    st.warning(
        "No reconocimos el formato de este archivo automáticamente. "
        "Indícanos cómo leerlo (una sola vez):"
    )
    suffix = path.suffix.lower()

    sep = dec = None
    if suffix in (".csv", ".txt"):
        c1, c2 = st.columns(2)
        with c1:
            sep_label = st.selectbox(
                "Separador de columnas", ["Coma (,)", "Punto y coma (;)", "Tabulador"],
                key="map_sep",
            )
        with c2:
            dec_label = st.selectbox("Separador decimal", ["Punto (.)", "Coma (,)"], key="map_dec")
        sep = {"Coma (,)": ",", "Punto y coma (;)": ";", "Tabulador": "\t"}[sep_label]
        dec = "." if dec_label.startswith("Punto") else ","

    c3, c4 = st.columns(2)
    with c3:
        header_row = st.number_input(
            "Fila del encabezado (0 = primera fila)", min_value=0, max_value=20, value=0, key="map_header",
        )
    with c4:
        has_units_row = st.checkbox("Hay una fila de unidades justo debajo del encabezado", key="map_units")

    try:
        if suffix in (".csv", ".txt"):
            preview = pd.read_csv(path, sep=sep, decimal=dec, header=None, nrows=15, dtype=str)
        else:
            preview = pd.read_excel(path, sheet_name=0, header=None, nrows=15)
    except Exception as exc:
        st.error(f"No se pudo leer con esos parámetros: {exc}")
        return None

    st.caption("Vista previa del archivo (primeras filas):")
    st.dataframe(preview, use_container_width=True, hide_index=True)

    col_labels = [f"Columna {i}" for i in range(preview.shape[1])]
    c5, c6, c7 = st.columns(3)
    with c5:
        time_col = st.selectbox("Columna de Tiempo", ["(ninguna)"] + col_labels, key="map_time")
    with c6:
        force_col = st.selectbox("Columna de Fuerza", ["(ninguna)"] + col_labels, key="map_force")
    with c7:
        disp_col = st.selectbox("Columna de Desplazamiento", ["(ninguna)"] + col_labels, key="map_disp")

    name = st.text_input("Nombre del espécimen", value=display_name, key="map_name")

    if force_col == "(ninguna)":
        st.info("Selecciona al menos la columna de Fuerza para continuar.")
        return None
    if not st.button(":material/check: Usar esta configuración", key="map_confirm"):
        return None

    if suffix in (".csv", ".txt"):
        # engine="python": el motor C por defecto de pandas no respeta el
        # parámetro `decimal` en varios casos (columnas con texto mezclado,
        # como aquí — verificado con pandas 3.0.2) y deja el separador
        # decimal sin convertir, silenciosamente. El motor python sí lo hace.
        full = pd.read_csv(path, sep=sep, decimal=dec, header=None, engine="python")
    else:
        full = pd.read_excel(path, sheet_name=0, header=None)

    data_start = int(header_row) + 1 + (1 if has_units_row else 0)
    numeric = full.iloc[data_start:].apply(pd.to_numeric, errors="coerce")

    def _idx(label: str) -> int | None:
        return None if label == "(ninguna)" else col_labels.index(label)

    cols = [c for c in (_idx(time_col), _idx(force_col), _idx(disp_col)) if c is not None]
    chunk = numeric.iloc[:, cols].dropna()

    sp = tension_parser.TensionSpecimen(
        name=name or display_name, thickness_mm=float("nan"), width_mm=float("nan"), gauge_length_mm=float("nan"),
    )
    if _idx(time_col) is not None:
        sp.time_s = chunk[_idx(time_col)].to_numpy()
    sp.force_N = chunk[_idx(force_col)].to_numpy()
    if _idx(disp_col) is not None:
        sp.stroke_mm = chunk[_idx(disp_col)].to_numpy()

    if len(sp.force_N) < 2:
        st.error("Con esa selección no quedaron suficientes filas numéricas. Revisa la fila de encabezado/unidades.")
        return None

    data = tension_parser.TensionData()
    data.specimens = [sp]
    return data


def _load_tension_data(path: Path, display_name: str) -> tension_parser.TensionData | None:
    try:
        data = tension_parser.parse(path)
        has_curve = any(len(sp.force_N) > 1 for sp in data.specimens)
    except Exception:
        has_curve = False

    if has_curve:
        return data
    return _manual_mapping_ui(path, display_name)


def _metric_row(items: list[tuple[str, str] | tuple[str, str, str]]) -> None:
    """Fila de KPIs (st.metric) — mismo dato que antes iba en una tabla
    angosta al lado de la gráfica; ahora la gráfica queda sola y grande,
    y esto va debajo a modo de resumen rápido. Un tercer elemento opcional
    (desv. std) va en el `delta` propio de st.metric — en su propia línea,
    más chico — en vez de concatenarlo al string del valor, que se corta
    con "…" cuando no cabe en la columna."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value = item[0], item[1]
        delta = item[2] if len(item) > 2 else None
        col.metric(label, value, delta=delta, delta_color="off")


# --------------------------------------------------------------------- Tracción
def tension_tab() -> None:
    education.render_tension_help()

    top_l, top_r = st.columns([3, 2])
    with top_l:
        uploaded = st.file_uploader(
            "Cargar archivo (.xlsx del equipo, .csv/.txt de curva cruda, o cualquier otro formato)",
            type=["xlsx", "xls", "csv", "txt"], key="tension_file", label_visibility="collapsed",
        )
    with top_r:
        offset_pct = st.slider(
            ":material/tune: Offset (σy)", min_value=0.01, max_value=2.0,
            value=0.2, step=0.01, format="%.2f%%",
        )

    if uploaded is None:
        st.info("Sin archivo cargado.")
        return

    path = _save_upload(uploaded)
    try:
        data = _load_tension_data(path, Path(uploaded.name).stem)
    finally:
        path.unlink(missing_ok=True)

    if data is None:
        return
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

    names = [sp.name for sp in data.specimens]
    selected_names = st.multiselect("Especímenes", names, default=names, key="tension_specimens",
                                     label_visibility="collapsed", placeholder="Especímenes")
    indices = [i for i, n in enumerate(names) if n in selected_names]
    props = [tension_analysis.calculate(sp, offset_pct=offset_pct) for sp in data.specimens]

    # La gráfica sola, a todo el ancho — es lo importante, no compite por
    # espacio con la tabla de propiedades.
    fig = None
    if indices:
        fig = plotly_exports.create_tension_plot(data.specimens, props, indices, COLORS, offset_pct)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecciona al menos un espécimen para graficar.")

    if len(indices) == 1:
        p = props[indices[0]]
        _metric_row([
            ("Módulo de Young (E)", _fmt(p.youngs_modulus_MPa, "MPa", 0)),
            ("Límite elástico (σy)", _fmt(p.yield_stress_MPa, "MPa")),
            ("UTS", _fmt(p.uts_MPa, "MPa")),
            ("Deform. de rotura", _fmt(p.break_strain_pct, "%", 2)),
            ("Tenacidad", _fmt(p.toughness_MJ_m3, "MJ/m³", 3)),
        ])
    elif len(indices) > 1:
        def _agg_fmt(attr: str, unit: str, decimals: int = 2) -> tuple[str, str | None]:
            vals = _agg(props, indices, attr)
            if not vals:
                return "–", None
            mean_str = f"{np.mean(vals):.{decimals}f} {unit}"
            std_str = f"± {np.std(vals, ddof=1):.{decimals}f} {unit}" if len(vals) > 1 else None
            return mean_str, std_str

        _metric_row([
            ("Especímenes", str(len(indices))),
            ("E (promedio)", *_agg_fmt("youngs_modulus_MPa", "MPa", 0)),
            ("σy (promedio)", *_agg_fmt("yield_stress_MPa", "MPa", 1)),
            ("UTS (promedio)", *_agg_fmt("uts_MPa", "MPa", 1)),
            ("Tenacidad (prom.)", *_agg_fmt("toughness_MJ_m3", "MJ/m³", 1)),
        ])

    if fig is not None:
        st.download_button(
            ":material/download: Descargar gráfico HTML (interactivo)",
            data=fig.to_html(), file_name="traccion.html", mime="text/html",
        )

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
        st.dataframe(full_df, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------- Flexión
def flexion_tab() -> None:
    education.render_flexion_help()

    attrs = {
        "Resistencia a flexión (MPa)": "flexural_strength_MPa",
        "Módulo de flexión (MPa)": "flexural_modulus_MPa",
        "Deformación máxima (%)": "max_strain_pct",
        "Fuerza máxima (N)": "max_force_N",
    }

    top_l, top_r = st.columns([3, 2])
    with top_l:
        uploaded = st.file_uploader(
            "Cargar archivo (.xlsx del equipo, o .csv/.txt)",
            type=["xlsx", "xls", "csv", "txt"], key="flexion_file", label_visibility="collapsed",
        )
    with top_r:
        label = st.selectbox(":material/bar_chart: Variable a graficar", list(attrs.keys()), key="flexion_attr")

    if uploaded is None:
        st.info("Sin archivo cargado.")
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
    selected = st.multiselect("Especímenes", names, default=names, key="flexion_specimens",
                               label_visibility="collapsed", placeholder="Especímenes")
    indices = [i for i, n in enumerate(names) if n in selected]

    if indices:
        fig = plotly_exports.create_flexion_plot(props, indices, COLORS, attrs[label], label)
        st.plotly_chart(fig, use_container_width=True)

        vals = [getattr(props[i], attrs[label]) for i in indices if not np.isnan(getattr(props[i], attrs[label]))]
        cols = st.columns(4)
        cols[0].metric("Especímenes", str(len(indices)))
        cols[1].metric("Promedio", f"{np.mean(vals):.2f}" if vals else "–")
        cols[2].metric("Desv. std", f"{np.std(vals, ddof=1):.2f}" if len(vals) > 1 else "–")
        cols[3].metric("Máximo", f"{np.max(vals):.2f}" if vals else "–")
    else:
        st.info("Selecciona al menos un espécimen para graficar.")

    with st.expander("Ver todas las propiedades por espécimen"):
        df = pd.DataFrame([{
            "Espécimen": p.specimen_name,
            "Resistencia (MPa)": p.flexural_strength_MPa,
            "Módulo (MPa)": p.flexural_modulus_MPa,
            "Deform. máx (%)": p.max_strain_pct,
            "Fuerza máx (N)": p.max_force_N,
            "Desplaz. máx (mm)": p.max_disp_mm,
        } for p in props])
        st.dataframe(df, hide_index=True, use_container_width=True)


# --------------------------------------------------------------------- Impacto
def impact_tab() -> None:
    education.render_impact_help()

    top_l, top_r = st.columns([3, 2])
    with top_l:
        uploaded = st.file_uploader(
            "Cargar archivo (.xlsx del equipo, o .csv/.txt)",
            type=["xlsx", "xls", "csv", "txt"], key="impact_file", label_visibility="collapsed",
        )
    with top_r:
        var_choice = st.radio("Variable", ["Energía absorbida", "Tenacidad"], horizontal=True, key="impact_var")
    var_key = "energy" if var_choice == "Energía absorbida" else "toughness"

    if uploaded is None:
        st.info("Sin archivo cargado.")
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
    indices = list(range(len(data.specimens)))

    fig = plotly_exports.create_impact_plot(data.specimens, summary, indices, COLORS, var_key)
    st.plotly_chart(fig, use_container_width=True)

    if var_key == "energy":
        _metric_row([
            ("Media", _fmt(summary.mean_energy_J, "J")),
            ("Desv. std", _fmt(summary.std_energy_J, "J")),
            ("Mín", _fmt(summary.min_energy_J, "J")),
            ("Máx", _fmt(summary.max_energy_J, "J")),
            ("CV", _fmt(summary.cv_energy_pct, "%")),
        ])
    else:
        _metric_row([
            ("Media", _fmt(summary.mean_toughness, "J/mm²", 4)),
            ("Desv. std", _fmt(summary.std_toughness, "J/mm²", 4)),
            ("Mín", _fmt(summary.min_toughness, "J/mm²", 4)),
            ("Máx", _fmt(summary.max_toughness, "J/mm²", 4)),
            ("CV", _fmt(summary.cv_toughness_pct, "%")),
        ])

    with st.expander("Ver todos los especímenes"):
        df = pd.DataFrame([{
            "N°": s.number, "Área (mm²)": s.area_mm2,
            "Energía (J)": s.energy_J, "Tenacidad (J/mm²)": s.toughness_J_mm2,
        } for s in data.specimens])
        st.dataframe(df, use_container_width=True, hide_index=True)


TAB_FOR_ID = {"tension": tension_tab, "flexion": flexion_tab, "impact": impact_tab}


def main() -> None:
    st.session_state.setdefault("page", "home")
    _inject_css()
    _render_topbar()

    page = st.session_state.page
    if page == "home":
        _render_home()
    else:
        st.markdown(f"<div class='st-key-pageaccent'></div>", unsafe_allow_html=True)
        st.markdown(f"### :material/{ICON_FOR_ID[page]}: Ensayo de {LABEL_FOR_ID[page]}")
        TAB_FOR_ID[page]()


main()
