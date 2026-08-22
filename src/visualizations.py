"""Reusable Plotly figures for the screening dashboards."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import plotly.graph_objects as go


NAVY = "#07111F"
PANEL = "#0D1B2A"
TEXT = "#E8EEF6"
MUTED = "#91A3B7"
TEAL = "#34D3B5"
BLUE = "#5B8FF9"
AMBER = "#F5B84B"
RED = "#F06A6A"
GRID = "rgba(145, 163, 183, 0.16)"


def _score_color(score: float) -> str:
    if score >= 80:
        return TEAL
    if score >= 60:
        return BLUE
    if score >= 40:
        return AMBER
    return RED


def _base_layout(figure: go.Figure, height: int) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=40, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, ui-sans-serif, sans-serif", color=TEXT),
        hoverlabel=dict(bgcolor=PANEL, font_color=TEXT, bordercolor=GRID),
        showlegend=False,
    )
    return figure


def build_score_radar_chart(categories: Mapping[str, Mapping[str, Any]]) -> go.Figure:
    """Build a closed radar chart from category score results."""
    labels = list(categories)
    scores = [categories[label]["score"] for label in labels]
    figure = go.Figure(
        go.Scatterpolar(
            r=scores + [scores[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(52, 211, 181, 0.16)",
            line=dict(color=TEAL, width=3),
            marker=dict(color=TEAL, size=7),
            hovertemplate="%{theta}<br><b>%{r}/100</b><extra></extra>",
        )
    )
    _base_layout(figure, 480)
    figure.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], tickvals=[20, 40, 60, 80, 100], tickfont=dict(color=MUTED, size=10), gridcolor=GRID, linecolor=GRID),
            angularaxis=dict(tickfont=dict(color=TEXT, size=11), gridcolor=GRID, linecolor=GRID),
        )
    )
    return figure


def build_score_bar_chart(categories: Mapping[str, Mapping[str, Any]]) -> go.Figure:
    """Build a horizontal category comparison chart."""
    labels = list(categories)
    scores = [categories[label]["score"] for label in labels]
    colors = [_score_color(score) for score in scores]
    figure = go.Figure(
        go.Bar(
            x=scores[::-1],
            y=labels[::-1],
            orientation="h",
            marker=dict(color=colors[::-1], cornerradius=5),
            text=[f"{score}" for score in scores[::-1]],
            textposition="outside",
            textfont=dict(color=TEXT),
            cliponaxis=False,
            hovertemplate="%{y}<br><b>%{x}/100</b><extra></extra>",
        )
    )
    _base_layout(figure, 480)
    figure.update_xaxes(range=[0, 108], showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title=None)
    figure.update_yaxes(showgrid=False, tickfont=dict(color=TEXT, size=11), title=None)
    return figure


def build_risk_summary_chart(flags: Sequence[Mapping[str, str]]) -> go.Figure:
    """Build a compact severity distribution chart."""
    severities = ("High", "Medium", "Context")
    counts = [sum(flag.get("severity") == severity for flag in flags) for severity in severities]
    figure = go.Figure(
        go.Bar(
            x=severities,
            y=counts,
            marker=dict(color=[RED, AMBER, BLUE], cornerradius=5),
            text=counts,
            textposition="outside",
            hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
        )
    )
    _base_layout(figure, 260)
    upper = max(counts + [1]) + 1
    figure.update_yaxes(range=[0, upper], dtick=1, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title=None)
    figure.update_xaxes(showgrid=False, tickfont=dict(color=TEXT), title=None)
    return figure
