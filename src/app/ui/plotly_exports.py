"""
Utilidades para exportar gráficos interactivos en HTML usando Plotly.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def create_tension_plot(specimens: list, props: list, indices: list[int], 
                        colors: list[str], offset_pct: float) -> go.Figure:
    """
    Crear gráfico interactivo de tracción (Plotly).
    
    Args:
        specimens: Lista de TensionSpecimen
        props: Lista de TensionProperties
        indices: Índices de especímenes seleccionados
        colors: Paleta de colores
        offset_pct: Parámetro de offset actual
    """
    fig = go.Figure()
    
    for i in indices:
        sp = specimens[i]
        props_i = props[i]
        color = colors[i % len(colors)]
        
        stress = sp.stress_MPa
        strain = sp.strain_pct
        
        if len(stress) > 1 and len(strain) > 1:
            # Curva principal
            fig.add_trace(go.Scatter(
                x=strain, y=stress,
                mode='lines',
                name=sp.name,
                line=dict(color=color, width=2),
                hovertemplate=f"{sp.name}<br>Deformación: %{{x:.3f}}%<br>Esfuerzo: %{{y:.2f}} MPa<extra></extra>"
            ))
            
            # Módulo de Young (línea punteada)
            if props_i.elastic_strain_range is not None and len(props_i.elastic_strain_range) > 0:
                fig.add_trace(go.Scatter(
                    x=props_i.elastic_strain_range,
                    y=props_i.elastic_stress_fit,
                    mode='lines',
                    name=f"{sp.name} (E)",
                    line=dict(color=color, width=1.5, dash='dash'),
                    hovertemplate=f"Módulo E<br>Deformación: %{{x:.3f}}%<br>Esfuerzo: %{{y:.2f}} MPa<extra></extra>"
                ))
            
            # Línea offset
            if props_i.offset_strain_range is not None and len(props_i.offset_strain_range) > 0:
                fig.add_trace(go.Scatter(
                    x=props_i.offset_strain_range,
                    y=props_i.offset_stress_line,
                    mode='lines',
                    name=f"{sp.name} (offset {offset_pct:.2f}%)",
                    line=dict(color=color, width=1, dash='dot'),
                    hovertemplate=f"Offset {offset_pct:.2f}%<br>Deformación: %{{x:.3f}}%<br>Esfuerzo: %{{y:.2f}} MPa<extra></extra>"
                ))
            
            # Punto UTS
            if not np.isnan(props_i.uts_MPa):
                fig.add_trace(go.Scatter(
                    x=[props_i.uts_strain_pct],
                    y=[props_i.uts_MPa],
                    mode='markers',
                    name=f"{sp.name} (UTS)",
                    marker=dict(color=color, size=10, symbol='circle'),
                    hovertemplate=f"UTS: %{{y:.2f}} MPa @ %{{x:.3f}}%<extra></extra>"
                ))
            
            # Límite elástico 0.2%
            if not np.isnan(props_i.yield_stress_MPa):
                fig.add_trace(go.Scatter(
                    x=[props_i.yield_strain_pct],
                    y=[props_i.yield_stress_MPa],
                    mode='markers',
                    name=f"{sp.name} (σy)",
                    marker=dict(color=color, size=12, symbol='triangle-up'),
                    hovertemplate=f"σy: %{{y:.2f}} MPa @ %{{x:.3f}}%<extra></extra>"
                ))
        else:
            # Sin series — puntos resumen
            if not np.isnan(sp.max_stress_MPa):
                fig.add_trace(go.Scatter(
                    x=[sp.max_strain_pct],
                    y=[sp.max_stress_MPa],
                    mode='markers',
                    name=sp.name,
                    marker=dict(color=color, size=12),
                    hovertemplate=f"{sp.name}<br>Máximo: %{{y:.2f}} MPa<extra></extra>"
                ))
    
    fig.update_layout(
        title=f"Curva Esfuerzo – Deformación (Tracción) | Offset: {offset_pct:.2f}%",
        xaxis_title="Deformación (%)",
        yaxis_title="Esfuerzo (MPa)",
        hovermode='x unified',
        template='plotly_white',
        width=1200,
        height=600,
        font=dict(family="Segoe UI, sans-serif", size=11),
        legend=dict(
            x=1.02, y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#E0E0E0',
            borderwidth=1,
        ),
        margin=dict(l=60, r=260, t=60, b=60)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    return fig


def create_impact_plot(specimens: list, summary, indices: list[int], 
                       colors: list[str], var_key: str) -> go.Figure:
    """Crear gráfico interactivo de impacto (Plotly)."""
    fig = go.Figure()
    
    if var_key == "energy":
        values = [s.energy_J for s in specimens]
        ylabel = "Energía absorbida (J)"
        mean = summary.mean_energy_J
        std = summary.std_energy_J
    else:
        values = [s.toughness_J_mm2 for s in specimens]
        ylabel = "Tenacidad (J/mm²)"
        mean = summary.mean_toughness
        std = summary.std_toughness
    
    # Gráfico de barras
    selected_labels = [f"#{s.number}" for i, s in enumerate(specimens) if i in indices]
    selected_values = [values[i] for i in indices]
    selected_colors = [colors[i % len(colors)] for i in indices]
    
    fig.add_trace(go.Bar(
        x=selected_labels,
        y=selected_values,
        marker=dict(color=selected_colors, line=dict(width=1, color='white')),
        hovertemplate="%{x}<br>" + ylabel + ": %{y:.4f}<extra></extra>"
    ))
    
    # Línea de media
    if not np.isnan(mean):
        fig.add_hline(y=mean, line_dash="dash", line_color="red", 
                     annotation_text=f"Media: {mean:.4f}", annotation_position="right")
    
    # Banda ±σ
    if not np.isnan(std):
        fig.add_hrect(y0=mean-std, y1=mean+std, fillcolor="red", opacity=0.1)
    
    fig.update_layout(
        title=f"Impacto (ASTM D256) — {ylabel}",
        xaxis_title="Espécimen",
        yaxis_title=ylabel,
        template='plotly_white',
        width=1000,
        height=600,
        font=dict(family="Segoe UI, sans-serif", size=11),
        hovermode='x',
        showlegend=False
    )
    
    return fig


def create_flexion_plot(props: list, indices: list[int], 
                        colors: list[str], attr: str, label: str) -> go.Figure:
    """Crear gráfico interactivo de flexión (Plotly)."""
    fig = go.Figure()
    
    selected_names = [props[i].specimen_name for i in indices]
    selected_values = [getattr(props[i], attr) for i in indices]
    selected_colors = [colors[i % len(colors)] for i in indices]
    
    # Filtrar NaN
    valid_data = [(n, v, c) for n, v, c in zip(selected_names, selected_values, selected_colors) 
                  if not np.isnan(v)]
    
    if not valid_data:
        fig.add_annotation(text="Sin datos disponibles", xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False, font=dict(size=12, color="gray"))
    else:
        names_v, vals_v, colors_v = zip(*valid_data)
        
        fig.add_trace(go.Bar(
            x=list(names_v),
            y=list(vals_v),
            marker=dict(color=list(colors_v), line=dict(width=1, color='white')),
            hovertemplate="%{x}<br>" + label + ": %{y:.2f}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"Flexión 3 puntos — {label}",
        xaxis_title="Espécimen",
        yaxis_title=label,
        template='plotly_white',
        width=1000,
        height=600,
        font=dict(family="Segoe UI, sans-serif", size=11),
        hovermode='x',
        showlegend=False,
        xaxis_tickangle=-35
    )
    
    return fig
