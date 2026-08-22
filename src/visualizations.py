"""Purpose-led Plotly figures for the screening dashboards."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import plotly.graph_objects as go


PAPER = "#F7F4EC"
INK = "#17201B"
MUTED = "#6D746E"
LINE = "#D8D4C9"
RUST = "#C9573D"
GREEN = "#236B53"
AMBER = "#B7791F"
RED = "#B74A3B"


def _score_color(score: float) -> str:
    if score >= 80:
        return GREEN
    if score >= 60:
        return "#315F78"
    if score >= 40:
        return AMBER
    return RED


def _base_layout(figure: go.Figure, height: int) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=18, r=30, t=24, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, ui-sans-serif, sans-serif", color=INK, size=12),
        hoverlabel=dict(bgcolor=INK, font_color=PAPER, bordercolor=INK),
        showlegend=False,
    )
    return figure


def build_score_profile_chart(categories: Mapping[str, Mapping[str, Any]]) -> go.Figure:
    """Compare category scores with a restrained horizontal lollipop chart."""
    labels = list(categories)[::-1]
    scores = [categories[label]["score"] for label in labels]
    colors = [_score_color(score) for score in scores]
    figure = go.Figure()
    for label, score, color in zip(labels, scores, colors):
        figure.add_shape(type="line", x0=0, x1=score, y0=label, y1=label, line=dict(color=LINE, width=4))
        figure.add_trace(
            go.Scatter(
                x=[score], y=[label], mode="markers+text",
                marker=dict(size=13, color=color, line=dict(width=2, color=PAPER)),
                text=[str(score)], textposition="middle right",
                textfont=dict(color=INK, size=12),
                hovertemplate=f"{label}<br><b>{score}/100</b><extra></extra>",
            )
        )
    _base_layout(figure, 430)
    figure.update_xaxes(
        range=[0, 108], tickvals=[0, 20, 40, 60, 80, 100],
        tickfont=dict(color=MUTED, size=10), gridcolor="#E8E4DB",
        zeroline=False, title=None, side="top",
    )
    figure.update_yaxes(showgrid=False, tickfont=dict(color=INK, size=11), title=None)
    return figure


def build_weighted_contribution_chart(categories: Mapping[str, Mapping[str, Any]]) -> go.Figure:
    """Show how much each category contributes to the overall score."""
    rows = sorted(
        (
            (name, result["score"] * result["weight"], result["weight"])
            for name, result in categories.items()
        ),
        key=lambda row: row[1],
    )
    labels = [row[0] for row in rows]
    contributions = [row[1] for row in rows]
    weights = [row[2] for row in rows]
    figure = go.Figure(
        go.Bar(
            x=contributions,
            y=labels,
            orientation="h",
            marker=dict(color=RUST),
            customdata=weights,
            text=[f"{value:.1f}" for value in contributions],
            textposition="outside",
            textfont=dict(color=INK),
            hovertemplate="%{y}<br><b>%{x:.1f} points</b><br>Weight: %{customdata:.0%}<extra></extra>",
        )
    )
    _base_layout(figure, 430)
    figure.update_xaxes(
        range=[0, max(contributions + [1]) * 1.18],
        showgrid=True, gridcolor="#E8E4DB", zeroline=False,
        tickfont=dict(color=MUTED, size=10), title=None, side="top",
    )
    figure.update_yaxes(showgrid=False, tickfont=dict(color=INK, size=11), title=None)
    return figure


def build_risk_summary_chart(flags: Sequence[Mapping[str, str]]) -> go.Figure:
    """Show the risk register as one compact part-to-whole bar."""
    severities = ("High", "Medium", "Context")
    colors = (RED, AMBER, "#637C8A")
    figure = go.Figure()
    for severity, color in zip(severities, colors):
        count = sum(flag.get("severity") == severity for flag in flags)
        figure.add_trace(
            go.Bar(
                x=[count], y=["Flags"], orientation="h", name=severity,
                marker=dict(color=color), text=[str(count) if count else ""],
                textposition="inside", insidetextanchor="middle",
                hovertemplate=f"{severity}: <b>{count}</b><extra></extra>",
            )
        )
    _base_layout(figure, 145)
    figure.update_layout(
        barmode="stack", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, font=dict(color=MUTED, size=10)),
    )
    figure.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, title=None)
    figure.update_yaxes(showgrid=False, showticklabels=False, title=None)
    return figure
