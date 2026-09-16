"""
Contenido educativo: diagramas esquemáticos (SVG), fórmulas y una curva
esfuerzo-deformación ilustrativa anotada. Independiente de los datos que
cargue el usuario — vive en un expander colapsado en cada pestaña para no
quitarle protagonismo a la gráfica real (ver streamlit_app.py).
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

_SVG_TENSION = """
<svg viewBox="0 0 160 240" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:200px;display:block;margin:0 auto;">
  <rect x="55" y="10" width="50" height="24" rx="4" fill="#1976D2"/>
  <line x1="80" y1="10" x2="80" y2="0" stroke="#1976D2" stroke-width="3"/>
  <polygon points="80,0 75,10 85,10" fill="#1976D2"/>
  <text x="92" y="10" font-size="13" fill="#1976D2" font-family="sans-serif" font-weight="700">F</text>

  <path d="M60,34 L60,70 Q60,80 70,90 L70,150 Q70,160 60,170 L60,206 L100,206 L100,170 Q100,160 90,150 L90,90 Q90,80 100,70 L100,34 Z" fill="none" stroke="#424242" stroke-width="2.5"/>

  <line x1="40" y1="90" x2="40" y2="150" stroke="#9E9E9E" stroke-width="1.5"/>
  <line x1="35" y1="90" x2="45" y2="90" stroke="#9E9E9E" stroke-width="1.5"/>
  <line x1="35" y1="150" x2="45" y2="150" stroke="#9E9E9E" stroke-width="1.5"/>
  <text x="12" y="124" font-size="12" fill="#616161" font-family="sans-serif">L₀</text>

  <rect x="55" y="206" width="50" height="24" rx="4" fill="#1976D2"/>
  <line x1="80" y1="230" x2="80" y2="240" stroke="#1976D2" stroke-width="3"/>
  <polygon points="80,240 75,230 85,230" fill="#1976D2"/>
  <text x="92" y="238" font-size="13" fill="#1976D2" font-family="sans-serif" font-weight="700">F</text>
</svg>
"""

_SVG_FLEXION = """
<svg viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:260px;display:block;margin:0 auto;">
  <rect x="30" y="70" width="180" height="14" fill="none" stroke="#424242" stroke-width="2.5"/>

  <polygon points="50,84 40,104 60,104" fill="#388E3C"/>
  <polygon points="190,84 180,104 200,104" fill="#388E3C"/>
  <line x1="30" y1="104" x2="220" y2="104" stroke="#9E9E9E" stroke-width="1.5"/>

  <line x1="120" y1="40" x2="120" y2="68" stroke="#388E3C" stroke-width="3"/>
  <polygon points="120,68 115,58 125,58" fill="#388E3C"/>
  <text x="128" y="52" font-size="14" fill="#388E3C" font-family="sans-serif" font-weight="700">F</text>

  <line x1="50" y1="118" x2="190" y2="118" stroke="#9E9E9E" stroke-width="1.5"/>
  <line x1="50" y1="113" x2="50" y2="123" stroke="#9E9E9E" stroke-width="1.5"/>
  <line x1="190" y1="113" x2="190" y2="123" stroke="#9E9E9E" stroke-width="1.5"/>
  <text x="98" y="134" font-size="12" fill="#616161" font-family="sans-serif">L (luz libre)</text>
</svg>
"""

_SVG_IMPACT = """
<svg viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:220px;display:block;margin:0 auto;">
  <circle cx="110" cy="20" r="5" fill="#424242"/>
  <path d="M40,20 A70,70 0 0 1 170,150" fill="none" stroke="#BDBDBD" stroke-width="1.5" stroke-dasharray="4 3"/>

  <line x1="110" y1="20" x2="110" y2="150" stroke="#F57C00" stroke-width="4"/>
  <circle cx="110" cy="160" r="16" fill="#F57C00"/>

  <rect x="70" y="188" width="80" height="12" fill="none" stroke="#424242" stroke-width="2.5"/>
  <polygon points="108,188 112,188 110,196" fill="#424242"/>
  <rect x="65" y="200" width="10" height="14" fill="#616161"/>
  <rect x="145" y="200" width="10" height="14" fill="#616161"/>

  <text x="14" y="95" font-size="12" fill="#616161" font-family="sans-serif">péndulo</text>
  <text x="66" y="216" font-size="11" fill="#616161" font-family="sans-serif">probeta con muesca</text>
</svg>
"""


def _schematic_stress_strain_fig() -> go.Figure:
    """Curva esfuerzo-deformación ilustrativa (no son datos reales) para
    explicar visualmente qué es cada región/punto antes de ver la curva
    real del espécimen cargado."""
    e_elastic = np.linspace(0, 2, 40)
    s_elastic = e_elastic * 40

    e_plastic = np.linspace(2, 7, 100)
    s_plastic = 80 + 30 * np.sqrt(e_plastic - 2)

    e_neck = np.linspace(7, 9.5, 40)
    s_neck = s_plastic[-1] - 22 * ((e_neck - 7) / 2.5) ** 2

    strain = np.concatenate([e_elastic, e_plastic, e_neck])
    stress = np.concatenate([s_elastic, s_plastic, s_neck])

    fig = go.Figure()
    fig.add_vrect(x0=0, x1=2, fillcolor="#E3F2FD", opacity=0.6, line_width=0,
                  annotation_text="Región elástica", annotation_position="top left",
                  annotation_font_size=10, annotation_font_color="#1565C0")
    fig.add_vrect(x0=2, x1=7, fillcolor="#FFF3E0", opacity=0.6, line_width=0,
                  annotation_text="Región plástica", annotation_position="top left",
                  annotation_font_size=10, annotation_font_color="#E65100")
    fig.add_vrect(x0=7, x1=9.5, fillcolor="#FFEBEE", opacity=0.6, line_width=0,
                  annotation_text="Estricción", annotation_position="top left",
                  annotation_font_size=10, annotation_font_color="#C62828")

    fig.add_trace(go.Scatter(x=strain, y=stress, mode="lines",
                              line=dict(color="#212121", width=2.5), showlegend=False))

    points = [
        (2, 80, "σy — Límite elástico<br>(offset 0.2%)", -40, -30),
        (7, s_plastic[-1], "UTS — Resistencia máxima", 0, -40),
        (9.5, s_neck[-1], "Rotura", 30, 20),
    ]
    for x, y, label, ax, ay in points:
        fig.add_annotation(x=x, y=y, text=label, showarrow=True, arrowhead=2,
                            ax=ax, ay=ay, font=dict(size=11, color="#212121"),
                            bgcolor="rgba(255,255,255,0.85)")

    fig.update_layout(
        title="Cómo leer la curva esfuerzo–deformación",
        xaxis_title="Deformación (ε)", yaxis_title="Esfuerzo (σ)",
        template="plotly_white", autosize=True, height=380,
        margin=dict(l=50, r=20, t=50, b=50),
        font=dict(family="Manrope, sans-serif", size=11),
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig


def render_tension_help() -> None:
    with st.expander("📚 ¿Cómo funciona el ensayo de tracción?"):
        col_svg, col_text = st.columns([1, 2])
        with col_svg:
            st.markdown(_SVG_TENSION, unsafe_allow_html=True)
        with col_text:
            st.markdown(
                "Se sujeta la probeta por sus dos extremos y se estira a velocidad "
                "constante hasta la rotura, midiendo la fuerza y el alargamiento."
            )
            st.latex(r"\sigma = \frac{F}{A_0} \quad,\quad A_0 = t \times w")
            st.caption("Esfuerzo — fuerza dividida por el área original de la sección transversal.")
            st.latex(r"\varepsilon = \frac{\Delta L}{L_0} \times 100\%")
            st.caption("Deformación — alargamiento respecto a la longitud calibrada original.")
            st.latex(r"E = \frac{\sigma}{\varepsilon} \Big|_{\text{región elástica}}")
            st.caption("Módulo de Young — pendiente de la parte recta inicial (rigidez del material).")

        st.markdown("---")
        st.latex(r"\sigma_y \;:\; \text{intersección con } \sigma = E\,(\varepsilon - 0.002)")
        st.latex(r"U_r = \frac{\sigma_y^{2}}{2E} \qquad U_t = \int \sigma \, d\varepsilon")
        st.caption(
            "Límite elástico (σy) por el método de offset 0.2% · Resiliencia (Ur) = energía elástica "
            "recuperable · Tenacidad (Ut) = área bajo toda la curva, energía total absorbida hasta la rotura."
        )
        st.plotly_chart(_schematic_stress_strain_fig(), use_container_width=True)


def render_flexion_help() -> None:
    with st.expander("📚 ¿Cómo funciona el ensayo de flexión (3 puntos)?"):
        col_svg, col_text = st.columns([1, 2])
        with col_svg:
            st.markdown(_SVG_FLEXION, unsafe_allow_html=True)
        with col_text:
            st.markdown(
                "La probeta se apoya en dos puntos y se aplica una carga en el centro "
                "hasta la rotura o el desplazamiento máximo definido."
            )
            st.latex(r"\sigma_{max} = \frac{3FL}{2bh^{2}}")
            st.caption("Resistencia a flexión — esfuerzo máximo en la fibra externa, en el punto de carga.")
            st.latex(r"E_{flex} = \frac{FL^{3}}{4bh^{3}\delta}")
            st.caption("Módulo de flexión — rigidez a partir de la pendiente carga–desplazamiento.")
            st.latex(r"\varepsilon_{max} = \frac{6h\delta}{L^{2}}")
            st.caption("Deformación máxima en la fibra externa.")
        st.caption("F = fuerza · L = luz libre (distancia entre apoyos) · b = ancho · h = espesor · δ = desplazamiento en el punto de carga.")


def render_impact_help() -> None:
    with st.expander("📚 ¿Cómo funciona el ensayo de impacto (ASTM D256)?"):
        col_svg, col_text = st.columns([1, 2])
        with col_svg:
            st.markdown(_SVG_IMPACT, unsafe_allow_html=True)
        with col_text:
            st.markdown(
                "Un péndulo con un martillo en la punta se deja caer desde una altura fija "
                "y golpea una probeta con muesca. La energía que el péndulo pierde al romperla "
                "es la energía absorbida por el material."
            )
            st.latex(r"\text{Tenacidad al impacto} = \frac{E_{\text{absorbida}}}{A_{\text{muesca}}}")
            st.caption(
                "La energía absorbida (en Joules) la calcula directamente el equipo, comparando la "
                "altura de subida del péndulo antes y después del golpe. La tenacidad la normaliza "
                "por el área de la sección bajo la muesca, para poder comparar probetas de distinto tamaño."
            )
