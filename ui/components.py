"""Composants UI V3.1 fintech — pure présentation."""
from __future__ import annotations

from typing import List, Sequence, Tuple

import streamlit as st


def kpi_card(
    label: str,
    value: str,
    hint: str = "",
    tone: str = "neutral",
    icon: str = "",
    hint_tone: str = "",
) -> str:
    tone_cls = {
        "neutral": "rt-kpi-neutral",
        "success": "rt-kpi-success",
        "warning": "rt-kpi-warning",
        "danger": "rt-kpi-danger",
        "info": "rt-kpi-info",
    }.get(tone, "rt-kpi-neutral")
    hint_cls = "rt-kpi-hint"
    if hint_tone == "up":
        hint_cls += " up"
    elif hint_tone == "down":
        hint_cls += " down"
    hint_html = f'<div class="{hint_cls}">{hint}</div>' if hint else ""
    icon_html = f'<div class="rt-kpi-icon">{icon}</div>' if icon else ""
    return (
        f'<div class="rt-kpi {tone_cls}">'
        f"{icon_html}"
        f'<div class="rt-kpi-label">{label}</div>'
        f'<div class="rt-kpi-value">{value}</div>'
        f"{hint_html}</div>"
    )


def render_kpi_row(cards: Sequence[tuple]) -> None:
    """cards: (label, value, hint, tone[, icon[, hint_tone]])"""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        label, value, hint, tone = card[0], card[1], card[2], card[3]
        icon = card[4] if len(card) > 4 else ""
        hint_tone = card[5] if len(card) > 5 else ""
        with col:
            st.markdown(
                kpi_card(label, value, hint, tone, icon=icon, hint_tone=hint_tone),
                unsafe_allow_html=True,
            )


def step_indicator(current: int, steps: List[str]) -> None:
    parts = []
    for i, name in enumerate(steps):
        if i < current:
            cls, icon = "rt-step done", "✓"
            color = "#166534"
        elif i == current:
            cls, icon = "rt-step active", str(i + 1)
            color = "#3730A3"
        else:
            cls, icon = "rt-step", str(i + 1)
            color = "#334155"
        parts.append(
            f'<div class="{cls}" style="color:{color} !important;">'
            f'<span class="rt-step-num">{icon}</span>'
            f'<span class="rt-step-label" style="color:{color} !important;'
            f'font-weight:700 !important;opacity:1 !important;">{name}</span></div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="rt-step-sep"></div>')
    st.markdown(
        f'<div class="rt-stepper" style="background:#fff;border:1px solid #E2E8F0;">'
        f'{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    s = (status or "").lower()
    if s == "completed":
        return '<span class="rt-badge rt-badge-ok">Completed</span>'
    if s == "failed":
        return '<span class="rt-badge rt-badge-err">Failed</span>'
    if s == "running":
        return '<span class="rt-badge rt-badge-run">Running</span>'
    return f'<span class="rt-badge rt-badge-muted">{status or "—"}</span>'


def hero_header(
    title: str,
    subtitle: str = "",
    kicker: str = "RecoTrust",
    tabs: List[str] | None = None,
    active_tab: str = "",
) -> None:
    """Hero sombre : couleurs claires en inline (ne pas dépendre du CSS global)."""
    tabs = tabs or []
    tabs_html = ""
    if tabs:
        items = []
        for t in tabs:
            if t == active_tab:
                items.append(
                    f'<span class="rt-hero-tab active" style="color:#FFFFFF !important;'
                    f'background:rgba(99,102,241,0.45);border:1px solid rgba(165,180,252,0.5);'
                    f'padding:0.35rem 0.85rem;border-radius:999px;font-weight:700;">{t}</span>'
                )
            else:
                items.append(
                    f'<span class="rt-hero-tab" style="color:#E2E8F0 !important;'
                    f'background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);'
                    f'padding:0.35rem 0.85rem;border-radius:999px;font-weight:600;">{t}</span>'
                )
        tabs_html = f'<div class="rt-hero-tabs" style="display:flex;gap:0.5rem;margin-top:0.9rem;flex-wrap:wrap;">{"".join(items)}</div>'
    sub = (
        f'<p class="rt-hero-sub" style="color:#E2E8F0 !important;-webkit-text-fill-color:#E2E8F0 !important;'
        f'font-size:0.95rem;font-weight:500;margin:0.4rem 0 0 0;opacity:1 !important;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f'<div class="rt-hero" style="background:linear-gradient(135deg,#0B1220 0%,#151E33 55%,#1A2450 100%);'
        f'border-radius:16px;padding:1.25rem 1.5rem;margin:0 0 1.15rem 0;">'
        f'<div class="rt-hero-kicker" style="color:#C7D2FE !important;-webkit-text-fill-color:#C7D2FE !important;'
        f'font-size:0.78rem;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;'
        f'opacity:1 !important;margin:0 0 0.35rem 0;">{kicker}</div>'
        f'<div class="rt-hero-title" style="color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;'
        f'font-size:1.55rem;font-weight:800;margin:0;opacity:1 !important;text-shadow:none !important;";display:block;line-height:1.25;">{title}</div>'
        f"{sub}{tabs_html}</div>",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    """Compat : redirige vers hero fintech."""
    hero_header(title=title, subtitle=subtitle)


def panel_start(title: str) -> None:
    st.markdown(
        f'<div class="rt-panel"><div class="rt-panel-title">{title}</div>',
        unsafe_allow_html=True,
    )


def panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)
