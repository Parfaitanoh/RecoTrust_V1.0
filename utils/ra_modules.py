"""
RecoTrust V2.x — Modules Revenue Assurance complémentaires.

Modules additifs (n'altèrent pas le matching ni les résultats de réconciliation) :
  1. Taux de conversion par marchand / date   → utils.merchant_conversion
  2. Vieillissement des PENDING (aging)
  3. Top marchands à risque (taux d'échec élevé)
  4. Score de qualité de réconciliation (si colonnes match présentes)
  5. Synthèse opérationnelle RA

Point d'entrée unique : render_ra_extra_modules(dfpmt, ...)
Affiché UNIQUEMENT dans l'onglet Analytics Avancés.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
# streamlit importé à la demande dans les fonctions render_*

from utils.merchant_conversion import (
    render_merchant_conversion,
    _resolve_col,
    _normalize_status,
    _MERCHANT_CANDIDATES,
    _STATUS_CANDIDATES,
    _DATE_CANDIDATES,
    _AMOUNT_CANDIDATES,
    STATUS_SUCCESS,
    STATUS_PENDING,
    STATUS_FAILED,
)


def _render_pending_aging(dfpmt: pd.DataFrame, key_prefix: str = "aging") -> None:
    """Répartition des PENDING par ancienneté (jours depuis date transaction)."""
    import streamlit as st

    st.caption(
        "Identifie les en-cours qui stagnent : critique pour le cash-flow et le suivi ops. "
        "Buckets : 0-1 j · 2-3 j · 4-7 j · > 7 j."
    )

    s_col = _resolve_col(dfpmt, _STATUS_CANDIDATES)
    d_col = _resolve_col(dfpmt, _DATE_CANDIDATES)
    m_col = _resolve_col(dfpmt, _MERCHANT_CANDIDATES)
    a_col = _resolve_col(dfpmt, _AMOUNT_CANDIDATES)

    if not s_col:
        st.info("Colonne Statut absente — aging non calculable.")
        return

    work = dfpmt.copy()
    work["_statut"] = _normalize_status(work[s_col])
    pending = work[work["_statut"] == STATUS_PENDING].copy()

    if pending.empty:
        st.success("Aucune transaction PENDING dans le périmètre chargé.")
        return

    if d_col:
        pending["_dt"] = pd.to_datetime(pending[d_col], errors="coerce")
        today = pd.Timestamp.now().normalize()
        pending["Age_jours"] = (today - pending["_dt"].dt.normalize()).dt.days
        pending["Age_jours"] = pending["Age_jours"].fillna(0).clip(lower=0).astype(int)
    else:
        pending["Age_jours"] = 0

    def _bucket(age: int) -> str:
        if age <= 1:
            return "0-1 j"
        if age <= 3:
            return "2-3 j"
        if age <= 7:
            return "4-7 j"
        return "> 7 j"

    pending["Bucket"] = pending["Age_jours"].apply(_bucket)
    bucket_order = ["0-1 j", "2-3 j", "4-7 j", "> 7 j"]

    agg = (
        pending.groupby("Bucket", dropna=False)
        .agg(
            Nb=("Age_jours", "count"),
            Volume=(a_col, "sum") if a_col else ("Age_jours", "count"),
        )
        .reindex(bucket_order)
        .fillna(0)
        .reset_index()
    )
    if a_col:
        agg["Volume"] = pd.to_numeric(agg["Volume"], errors="coerce").fillna(0.0)
    else:
        agg = agg.rename(columns={"Volume": "Nb_bis"})
        agg["Volume"] = 0.0

    c1, c2, c3, c4 = st.columns(4)
    for i, row in agg.iterrows():
        col = [c1, c2, c3, c4][i] if i < 4 else c4
        col.metric(str(row["Bucket"]), f"{int(row['Nb']):,}")

    cols_show = ["Bucket", "Nb", "Volume"]
    st.dataframe(agg[cols_show], use_container_width=True, hide_index=True)

    if m_col:
        by_m = (
            pending.groupby(pending[m_col].astype(str))
            .agg(Nb=("Age_jours", "count"), Age_max=("Age_jours", "max"), Age_moy=("Age_jours", "mean"))
            .reset_index()
            .rename(columns={m_col: "Marchand"})
            .sort_values("Nb", ascending=False)
        )
        by_m["Age_moy"] = by_m["Age_moy"].round(1)
        st.caption("PENDING par marchand (tri volume décroissant)")
        st.dataframe(by_m.head(50), use_container_width=True, hide_index=True)

    critical = pending[pending["Age_jours"] > 7]
    if not critical.empty:
        st.warning(f"⚠️ {len(critical):,} transaction(s) PENDING de plus de 7 jours — action recommandée.")
        show_cols = [c for c in [m_col, d_col, s_col, a_col] if c]
        st.dataframe(critical[show_cols].head(100), use_container_width=True, hide_index=True)


def _render_risk_merchants(dfpmt: pd.DataFrame, key_prefix: str = "risk") -> None:
    """Top marchands avec taux d'échec / pending élevé (seuil configurable)."""
    import streamlit as st

    st.caption(
        "Classe les marchands par taux de non-succès (FAILED + PENDING). "
        "Utile pour prioriser les actions commerciales / techniques."
    )

    m_col = _resolve_col(dfpmt, _MERCHANT_CANDIDATES)
    s_col = _resolve_col(dfpmt, _STATUS_CANDIDATES)
    a_col = _resolve_col(dfpmt, _AMOUNT_CANDIDATES)

    if not m_col or not s_col:
        st.info("Colonnes Marchand / Statut requises.")
        return

    work = dfpmt.copy()
    work["_statut"] = _normalize_status(work[s_col])
    work["_ok"] = (work["_statut"] == STATUS_SUCCESS).astype(int)
    work["_ko"] = (work["_statut"].isin([STATUS_FAILED, STATUS_PENDING])).astype(int)

    min_n = st.slider("Seuil minimum de transactions", 5, 200, 20, key=f"{key_prefix}_min_n")
    threshold = st.slider("Seuil d'alerte non-succès (%)", 5, 80, 25, key=f"{key_prefix}_thr")

    g = work.groupby(work[m_col].astype(str)).agg(
        Nb=("_ok", "count"),
        SUCCESS=("_ok", "sum"),
        Non_succes=("_ko", "sum"),
        Volume=(a_col, "sum") if a_col else ("_ok", "count"),
    )
    g = g.reset_index().rename(columns={m_col: "Marchand"})
    g["Pct_non_succes"] = (100.0 * g["Non_succes"] / g["Nb"]).round(2)
    g["Pct_SUCCESS"] = (100.0 * g["SUCCESS"] / g["Nb"]).round(2)
    if a_col:
        g["Volume"] = pd.to_numeric(g["Volume"], errors="coerce").fillna(0.0)

    risk = g[(g["Nb"] >= min_n) & (g["Pct_non_succes"] >= threshold)].sort_values(
        "Pct_non_succes", ascending=False
    )

    if risk.empty:
        st.success(
            f"Aucun marchand au-dessus du seuil ({threshold}% non-succès, min {min_n} trx)."
        )
    else:
        st.error(f"{len(risk)} marchand(s) au-dessus du seuil d'alerte.")
        st.dataframe(risk, use_container_width=True, hide_index=True)
        csv = risk.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Export CSV — Marchands à risque",
            data=csv,
            file_name="marchands_a_risque.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl",
        )


def _render_reco_quality(dfpmt: pd.DataFrame) -> None:
    """
    Score de qualité si une colonne de matching côté partenaire a été posée
    (ex. OMCI, WAVE, CINETPAY… = 0/1). Non bloquant si absente.
    """
    import streamlit as st

    st.caption(
        "Mesure la part des transactions PMT retrouvées chez le partenaire "
        "(colonne flag 0/1 posée par le processeur : OMCI, WAVE, CINETPAY, etc.)."
    )

    flag_candidates = [
        "OMCI", "OMBF", "WAVE", "WAVECI", "WAVEBF", "WAVESN",
        "CINETPAY", "MTNCI", "MTNCM", "MOOV", "MOOVCI", "MOOVBF",
        "IFUTUR", "BIZAO", "PMT_MATCH", "MATCHED",
    ]
    flag_col = None
    for c in flag_candidates:
        if c in dfpmt.columns:
            flag_col = c
            break
    if flag_col is None:
        for c in dfpmt.columns:
            if dfpmt[c].dtype in ("int64", "int32", "float64") and set(
                pd.Series(dfpmt[c].dropna().unique()).astype(int)
            ).issubset({0, 1}):
                if c not in ("Montant", "Fee amount", "Merchant amount", "Nombre"):
                    flag_col = c
                    break

    if flag_col is None:
        st.info(
            "Aucune colonne de matching binaire détectée sur ce processeur. "
            "Le score de couverture sera disponible après exécution d'un processeur "
            "qui pose le flag partenaire (comportement historique inchangé)."
        )
        return

    total = len(dfpmt)
    matched = int(pd.to_numeric(dfpmt[flag_col], errors="coerce").fillna(0).astype(int).sum())
    rate = round(100.0 * matched / total, 2) if total else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Transactions PMT", f"{total:,}")
    c2.metric(f"Matchées ({flag_col}=1)", f"{matched:,}")
    c3.metric("Taux de couverture", f"{rate:.1f}%")

    if rate >= 95:
        st.success("Couverture excellente (≥ 95 %).")
    elif rate >= 85:
        st.warning("Couverture correcte mais perfectible (85–95 %).")
    else:
        st.error("Couverture faible (< 85 %) — vérifier période, clés de matching et fichiers.")


def _render_ops_summary(dfpmt: pd.DataFrame) -> None:
    """Synthèse ops en une ligne : volumes, taux, alertes."""
    import streamlit as st

    s_col = _resolve_col(dfpmt, _STATUS_CANDIDATES)
    a_col = _resolve_col(dfpmt, _AMOUNT_CANDIDATES)
    m_col = _resolve_col(dfpmt, _MERCHANT_CANDIDATES)

    n = len(dfpmt)
    vol = float(pd.to_numeric(dfpmt[a_col], errors="coerce").fillna(0).sum()) if a_col else 0.0
    n_merchants = dfpmt[m_col].nunique() if m_col else 0

    if s_col:
        st_norm = _normalize_status(dfpmt[s_col])
        n_ok = int((st_norm == STATUS_SUCCESS).sum())
        n_pend = int((st_norm == STATUS_PENDING).sum())
        n_fail = int((st_norm == STATUS_FAILED).sum())
        rate = round(100.0 * n_ok / n, 2) if n else 0.0
    else:
        n_ok = n_pend = n_fail = 0
        rate = 0.0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Transactions", f"{n:,}")
    k2.metric("Volume", f"{vol:,.0f}")
    k3.metric("Marchands", f"{n_merchants:,}")
    k4.metric("SUCCESS", f"{n_ok:,}")
    k5.metric("PENDING", f"{n_pend:,}")
    k6.metric("FAILED", f"{n_fail:,}")

    st.caption(f"Taux de succès global : **{rate:.1f} %**")


def render_ra_extra_modules(
    dfpmt: Optional[pd.DataFrame],
    key_prefix: str = "ra",
) -> None:
    """
    Point d'entrée unique à appeler depuis l'onglet Analytics Avancés
    de chaque processeur. Entièrement défensif.

    Disposition :
      - En-tête clair
      - Synthèse ops (toujours visible)
      - Taux de conversion (expander ouvert par défaut)
      - Aging / Risques / Couverture (expanders fermés pour ne pas saturer l'écran)
    """
    import streamlit as st

    if dfpmt is None or not isinstance(dfpmt, pd.DataFrame) or dfpmt.empty:
        return

    st.markdown("---")
    st.markdown("### 🛡️ Modules Revenue Assurance")
    st.caption(
        "Analyses complémentaires pour le suivi des transactions et la supervision des marchands. "
        "Ouvrez chaque section selon le besoin."
    )

    # 1. Taux de conversion — module principal, ouvert par défaut
    try:
        with st.expander("📈 Taux de conversion par marchand", expanded=True):
            render_merchant_conversion(dfpmt, key_prefix=f"{key_prefix}_mc")
    except Exception as e:
        st.warning(f"Module conversion marchand : {e}")

    # 2. Aging PENDING
    #try:
        #with st.expander("⏳ Vieillissement des transactions PENDING", expanded=False):
            #_render_pending_aging(dfpmt, key_prefix=f"{key_prefix}_aging")
    #except Exception as e:
        #st.warning(f"Module aging PENDING : {e}")

    # 3. Marchands à risque — retiré (demande produit V5.1.18)

    # 4. Score de couverture
    try:
        with st.expander("🎯 Score de couverture réconciliation", expanded=False):
            _render_reco_quality(dfpmt)
    except Exception as e:
        st.warning(f"Module score couverture : {e}")
