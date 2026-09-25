"""
RecoTrust V3 — Reconciliation Workspace (UI pure).
Présentation premium — aucun calcul métier.
Couleurs à contraste élevé pour lisibilité.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

# Palette lisible (texte foncé sur fond clair)
_C_TITLE = "#0F172A"
_C_LABEL = "#334155"
_C_MUTED = "#475569"
_C_PRIMARY = "#4338CA"


def workspace_header(
    *,
    partner: str,
    reco_type: str,
    status: str = "ready",
    pmt_name: str = "",
    partner_name: str = "",
    period: str = "",
    user_email: str = "",
) -> None:
    status_map = {
        "ready": ("En attente", "#1E293B", "#E2E8F0"),
        "config": ("Configuration", "#1E3A8A", "#DBEAFE"),
        "running": ("En cours", "#92400E", "#FEF3C7"),
        "done": ("Terminée", "#14532D", "#BBF7D0"),
        "error": ("Échec", "#7F1D1D", "#FECACA"),
    }
    label, fg, bg = status_map.get(status, status_map["ready"])
    type_label = (
        "Payin" if reco_type == "Payment"
        else ("Payout" if reco_type == "Transfer" else reco_type)
    )
    meta_bits = [partner or "—", type_label]
    if period:
        meta_bits.append(period)
    meta = " · ".join(meta_bits)
    pmt_disp = pmt_name or "—"
    part_disp = partner_name or "—"

    st.markdown(
        f"""
        <div class="rw-header">
          <div class="rw-header-top">
            <div>
              <div class="rw-kicker">Reconciliation Workspace</div>
              <div class="rw-title">{partner or "Réconciliation"}</div>
              <div class="rw-meta">{meta}</div>
            </div>
            <div class="rw-status" style="color:{fg} !important;background:{bg};border:1px solid {fg}44;">
              ● {label}
            </div>
          </div>
          <div class="rw-files">
            <div class="rw-file">
              <span class="rw-file-label">PMT</span>
              <span class="rw-file-name">{pmt_disp}</span>
            </div>
            <div class="rw-file">
              <span class="rw-file-label">Partenaire</span>
              <span class="rw-file-name">{part_disp}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_grid(items: list) -> None:
    if not items:
        return
    cols = st.columns(min(len(items), 4))
    for i, (label, value) in enumerate(items):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div class="rw-sum-card">
                  <div class="rw-sum-label">{label}</div>
                  <div class="rw-sum-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def match_preview(col_pmt: str, col_partner: str, default_pmt: str = "", default_partner: str = "") -> None:
    st.markdown(
        f"""
        <div class="rw-match-box">
          <div class="rw-match-title">Configuration du matching</div>
          <div class="rw-match-row">
            <div class="rw-match-col">
              <div class="rw-sum-label">Colonne PMT</div>
              <div class="rw-match-key">✓ {col_pmt}</div>
            </div>
            <div class="rw-match-arrow">↔</div>
            <div class="rw-match-col">
              <div class="rw-sum-label">Colonne Partenaire</div>
              <div class="rw-match-key">✓ {col_partner}</div>
            </div>
          </div>
          <div class="rw-match-hint">
            Défaut historique : {default_pmt or "—"} ↔ {default_partner or "—"}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def results_banner(
    *,
    partner: str,
    reco_type: str,
    duration_sec: Optional[float] = None,
    match_pmt: str = "",
    match_partner: str = "",
) -> None:
    dur = f"{duration_sec:.1f}s" if isinstance(duration_sec, (int, float)) else "—"
    type_label = (
        "Payin" if reco_type == "Payment"
        else ("Payout" if reco_type == "Transfer" else reco_type)
    )
    st.markdown(
        f"""
        <div class="rw-results-banner">
          <div>
            <div class="rw-kicker">Résultats</div>
            <div class="rw-title" style="font-size:1.25rem;">{partner} · {type_label}</div>
            <div class="rw-meta">Matching : {match_pmt or "—"} ↔ {match_partner or "—"} · Durée {dur}</div>
          </div>
          <div class="rw-status" style="color:#14532D !important;background:#BBF7D0;border:1px solid #4ADE80;">
            ● Terminée
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state_guide() -> None:
    st.markdown(
        """
        <div class="rw-guide">
          <div class="rw-guide-title">Démarrer une réconciliation</div>
          <ol class="rw-guide-list">
            <li>Choisir le <strong>type</strong> (Payment / Transfer) et le <strong>partenaire</strong></li>
            <li>Charger le fichier <strong>PMT</strong> et le fichier <strong>Partenaire</strong></li>
            <li>Configurer la <strong>période</strong> et les <strong>colonnes de matching</strong></li>
            <li>Lancer le traitement puis consulter les onglets et l’export Excel</li>
          </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )
