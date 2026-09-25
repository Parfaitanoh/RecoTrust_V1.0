"""
Helper pour enregistrer les résultats de réconciliation dans la session
et afficher le bouton de téléchargement du rapport Excel.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from utils.excel_export import ExcelExporter


def save_and_offer_report(
    partner_name: str,
    metrics: Dict[str, Any],
    sheets: Dict[str, Optional[pd.DataFrame]],
    key_suffix: str = "default",
    reco_start=None,
    reco_end=None,
):
    """
    Enregistre les résultats et affiche le bouton de téléchargement.
    Les bytes Excel sont mis en cache dans st.session_state pour que
    le clic « Télécharger » ne régénère pas le fichier ni ne bloque l'UI.

    L'e-mail de l'utilisateur connecté (session) est injecté automatiquement
    dans les métriques du rapport — aucune modification des processeurs requise.
    """
    # Injecter l'e-mail utilisateur dans les métriques (sans écraser si déjà présent)
    metrics = dict(metrics) if metrics else {}
    user_email = st.session_state.get("user_email")
    if user_email and "Utilisateur" not in metrics:
        metrics = {"Utilisateur": user_email, **metrics}

    # Ajouter le temps de traitement s'il est disponible
    elapsed = st.session_state.get("reco_elapsed_sec")
    if elapsed is not None and "Temps de traitement (s)" not in metrics:
        metrics["Temps de traitement (s)"] = round(float(elapsed), 2)

    clean_sheets = {
        name: df for name, df in sheets.items()
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty
    }

    st.session_state["reco_results"] = {
        "partner_name": partner_name,
        "metrics": metrics,
        "sheets": clean_sheets,
        "reco_start": reco_start,
        "reco_end": reco_end,
        "user_email": user_email,
    }

    st.markdown("---")
    st.subheader("📥 Générer le rapport final")
    ExcelExporter.download_button(
        partner_name=partner_name,
        metrics=metrics,
        sheets=clean_sheets,
        key=f"report_btn_{key_suffix}",
        reco_start=reco_start,
        reco_end=reco_end,
    )
