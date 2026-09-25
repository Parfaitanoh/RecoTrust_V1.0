"""
RecoTrust V2.x — Taux de conversion par marchand / par date courte.

Module purement additif : ne modifie aucune règle métier de matching.
Consomme un DataFrame PMT déjà préparé (colonnes standard via pmt_schema).

Sorties :
  - tableau détaillé : Marchand × Date → Nb trx, SUCCESS, PENDING, FAILED, %
  - agrégats par marchand (toutes dates)
  - agrégats journaliers globaux
  - UI Streamlit + export CSV

Perf :
  - agrégation vectorisée (pas de groupby.apply)
  - cache session_state des agrégats
  - filtres isolés via st.fragment (pas de rerun global de la page)
"""
from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd
# streamlit importé à la demande dans les fonctions render_*

# Statuts PMT normalisés (côté fichier Paymetrust)
STATUS_SUCCESS = "SUCCESS","succes","succès","réussi","ok"
STATUS_PENDING = "PENDING", "pending", "en attente", "waiting"
STATUS_FAILED = "FAILED", "failed", "échec", "echec", "ko", "error"
KNOWN_STATUSES = (STATUS_SUCCESS, STATUS_PENDING, STATUS_FAILED)

# Alias de colonnes possibles (défense en profondeur si prepare_pmt_dataframe n'a pas tout résolu)
_MERCHANT_CANDIDATES = ("Merchant Name", "merchant_name", "Merchant", "Marchand")
_STATUS_CANDIDATES = ("Statut", "statut", "Status", "status", "STATE")
_DATE_CANDIDATES = ("Date", "Created Date", "Payment Date", "created_at", "payment_date")
# Colonnes horodatées prioritaires pour l'évolution par heure (0–23)
# "Date" est souvent une date sans heure → placée en dernier recours
_DATETIME_CANDIDATES = (
    "Created Date",
    "created_at",
    "Created At",
    "created date",
    "Payment Date",
    "payment_date",
    "Payment At",
    "Date",
)
_AMOUNT_CANDIDATES = ("Montant", "amount", "Amount", "montant")
_TXN_CANDIDATES = ("Transaction ID", "transaction_id", "Transaction Id", "id_transaction")


def _resolve_col(df: pd.DataFrame, candidates: Tuple[str, ...]) -> Optional[str]:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    cols = list(df.columns)
    colset = set(cols)
    for c in candidates:
        if c in colset:
            return c
    lower_map = {str(c).strip().lower(): c for c in cols}
    for c in candidates:
        key = str(c).strip().lower()
        if key in lower_map:
            return lower_map[key]
    return None


def _pick_datetime_column(df: pd.DataFrame) -> Optional[str]:
    """
    Choisit la meilleure colonne d'horodatage pour l'évolution horaire.

    Critère : maximiser le nombre d'heures distinctes (0–23).
    Évite de retenir « Date » si elle est purement journalière (tout à 00:00).
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    best_col = None
    best_score = -1
    for cand in _DATETIME_CANDIDATES:
        col = _resolve_col(df, (cand,))
        if not col:
            continue
        try:
            ts = pd.to_datetime(df[col], errors="coerce")
            valid = ts.dropna()
            if valid.empty:
                continue
            n_hours = int(valid.dt.hour.nunique())
            n_valid = int(valid.shape[0])
            # Score : diversité d'heures en priorité, puis couverture
            score = n_hours * 1_000_000 + n_valid
            if score > best_score:
                best_score = score
                best_col = col
            # Score parfait : 24 heures distinctes
            if n_hours >= 20:
                break
        except Exception:
            continue
    return best_col


def _normalize_status(series: pd.Series) -> pd.Series:
    """Normalise les libellés de statut vers SUCCESS / PENDING / FAILED / OTHER."""
    s = series.astype(str).str.strip().str.upper()
    mapping = {
        "SUCCESS": STATUS_SUCCESS,
        "SUCCES": STATUS_SUCCESS,
        "SUCCÈS": STATUS_SUCCESS,
        "REUSSI": STATUS_SUCCESS,
        "RÉUSSI": STATUS_SUCCESS,
        "OK": STATUS_SUCCESS,
        "PENDING": STATUS_PENDING,
        "PENDANT": STATUS_PENDING,
        "EN ATTENTE": STATUS_PENDING,
        "WAITING": STATUS_PENDING,
        "FAILED": STATUS_FAILED,
        "FAIL": STATUS_FAILED,
        "ECHEC": STATUS_FAILED,
        "ÉCHEC": STATUS_FAILED,
        "ERROR": STATUS_FAILED,
        "KO": STATUS_FAILED,
    }
    return s.map(lambda x: mapping.get(x, x if x in KNOWN_STATUSES else "OTHER"))


def _finalize_agg(g: pd.DataFrame) -> pd.DataFrame:
    """Ajoute pourcentages à un agrégat déjà compté (Nb / SUCCESS / PENDING / FAILED / Volume)."""
    n = g["Nb_transactions"].replace(0, pd.NA)
    g = g.copy()
    g["Pct_SUCCESS"] = (100.0 * g["SUCCESS"] / n).fillna(0).round(2)
    g["Pct_PENDING"] = (100.0 * g["PENDING"] / n).fillna(0).round(2)
    g["Pct_FAILED"] = (100.0 * g["FAILED"] / n).fillna(0).round(2)
    g["Nb_transactions"] = g["Nb_transactions"].astype(int)
    g["SUCCESS"] = g["SUCCESS"].astype(int)
    g["PENDING"] = g["PENDING"].astype(int)
    g["FAILED"] = g["FAILED"].astype(int)
    if "OTHER" in g.columns:
        g["OTHER"] = g["OTHER"].astype(int)
    return g


def compute_conversion_by_merchant_date(
    df: pd.DataFrame,
    merchant_col: Optional[str] = None,
    status_col: Optional[str] = None,
    date_col: Optional[str] = None,
    amount_col: Optional[str] = None,
) -> tuple:
    """
    Calcule les taux de conversion — version vectorisée (rapide sur millions de lignes).

    Returns
    -------
    by_merchant_date, by_merchant, by_date, by_merchant_hour, by_hour, by_merchant_hour_of_day
    """
    empty = pd.DataFrame()
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return empty, empty, empty, empty, empty, empty

    m_col = merchant_col or _resolve_col(df, _MERCHANT_CANDIDATES)
    s_col = status_col or _resolve_col(df, _STATUS_CANDIDATES)
    d_col = date_col or _resolve_col(df, _DATE_CANDIDATES)
    # Colonne horodatée dédiée (Created Date en priorité) pour l'heure 0–23
    dt_col = _pick_datetime_column(df)
    a_col = amount_col or _resolve_col(df, _AMOUNT_CANDIDATES)

    if not m_col or not s_col:
        return empty, empty, empty, empty, empty, empty

    cols = [c for c in [m_col, s_col, d_col, dt_col, a_col] if c]
    # Dédupliquer en préservant l'ordre
    seen = set()
    cols_u = []
    for c in cols:
        if c not in seen:
            seen.add(c)
            cols_u.append(c)
    work = df.loc[:, cols_u].copy()
    work.rename(columns={m_col: "Marchand", s_col: "Statut_raw"}, inplace=True)
    work["Statut"] = _normalize_status(work["Statut_raw"])

    # Date courte : colonne Date métier si dispo, sinon horodatage
    if d_col and d_col in work.columns:
        ts_date = pd.to_datetime(work[d_col], errors="coerce")
        work["Date_courte"] = ts_date.dt.strftime("%Y-%m-%d").fillna("N/A")
    elif dt_col and dt_col in work.columns:
        ts_date = pd.to_datetime(work[dt_col], errors="coerce")
        work["Date_courte"] = ts_date.dt.strftime("%Y-%m-%d").fillna("N/A")
    else:
        work["Date_courte"] = "N/A"

    # Heure de la journée : colonne horodatée riche (Created Date, etc.)
    if dt_col and dt_col in work.columns:
        ts = pd.to_datetime(work[dt_col], errors="coerce")
        work["Heure"] = ts.dt.floor("h")
        work["Heure_jour"] = ts.dt.hour
    elif d_col and d_col in work.columns:
        ts = pd.to_datetime(work[d_col], errors="coerce")
        work["Heure"] = ts.dt.floor("h")
        work["Heure_jour"] = ts.dt.hour
    else:
        work["Heure"] = pd.NaT
        work["Heure_jour"] = pd.NA

    if a_col and a_col in work.columns:
        work["Volume"] = pd.to_numeric(work[a_col], errors="coerce").fillna(0.0)
    else:
        work["Volume"] = 0.0

    work["is_ok"] = (work["Statut"] == STATUS_SUCCESS).astype("int8")
    work["is_pend"] = (work["Statut"] == STATUS_PENDING).astype("int8")
    work["is_fail"] = (work["Statut"] == STATUS_FAILED).astype("int8")
    work["is_other"] = (
        1 - work["is_ok"] - work["is_pend"] - work["is_fail"]
    ).clip(lower=0).astype("int8")

    def _group(keys):
        g = (
            work.groupby(keys, dropna=False, sort=False)
            .agg(
                Nb_transactions=("Statut", "size"),
                SUCCESS=("is_ok", "sum"),
                PENDING=("is_pend", "sum"),
                FAILED=("is_fail", "sum"),
                OTHER=("is_other", "sum"),
                Volume=("Volume", "sum"),
            )
            .reset_index()
        )
        return _finalize_agg(g)

    by_md = _group(["Marchand", "Date_courte"]).sort_values(["Date_courte", "Marchand"])
    by_m = _group(["Marchand"]).sort_values("Nb_transactions", ascending=False)
    by_d = _group(["Date_courte"]).sort_values("Date_courte")

    has_hour = work["Heure"].notna().any()
    if has_hour:
        by_mh = _group(["Marchand", "Heure", "Date_courte"]).sort_values(["Heure", "Marchand"])
        by_h = _group(["Heure", "Date_courte"]).sort_values("Heure")
        # Profil par heure de journée (0–23), conservant Date_courte pour filtrer
        work_h = work.dropna(subset=["Heure_jour"])
        if not work_h.empty:
            by_mhj = (
                work_h.groupby(["Marchand", "Heure_jour", "Date_courte"], dropna=False, sort=False)
                .agg(
                    Nb_transactions=("Statut", "size"),
                    SUCCESS=("is_ok", "sum"),
                    PENDING=("is_pend", "sum"),
                    FAILED=("is_fail", "sum"),
                    OTHER=("is_other", "sum"),
                    Volume=("Volume", "sum"),
                )
                .reset_index()
            )
            by_mhj = _finalize_agg(by_mhj).sort_values(["Heure_jour", "Marchand"])
        else:
            by_mhj = empty
    else:
        by_mh = empty
        by_h = empty
        by_mhj = empty

    return by_md, by_m, by_d, by_mh, by_h, by_mhj


def _get_cached_aggregates(dfpmt: pd.DataFrame, key_prefix: str):
    """
    Cache session_state des agrégats.
    Clé basée sur shape + colonnes + empreinte légère (évite de recalculer à chaque filtre).
    """
    import streamlit as st

    cache_key = f"_mc_agg_v2_{key_prefix}"
    sig_key = f"_mc_sig_v2_{key_prefix}"

    try:
        sig = (
            dfpmt.shape,
            tuple(dfpmt.columns.tolist()),
            int(dfpmt.index[:5].astype(str).str.len().sum()) if len(dfpmt) else 0,
        )
    except Exception:
        sig = (dfpmt.shape, tuple(dfpmt.columns.tolist()))

    if st.session_state.get(sig_key) == sig and cache_key in st.session_state:
        return st.session_state[cache_key]

    result = compute_conversion_by_merchant_date(dfpmt)
    st.session_state[cache_key] = result
    st.session_state[sig_key] = sig
    return result


def _reagg_sum(md: pd.DataFrame, keys: list) -> pd.DataFrame:
    """Ré-agrège SUCCESS/PENDING/FAILED/Volume depuis un grain plus fin."""
    if md is None or md.empty:
        return pd.DataFrame()
    agg_map = {
        "Nb_transactions": "sum",
        "SUCCESS": "sum",
        "PENDING": "sum",
        "FAILED": "sum",
    }
    if "OTHER" in md.columns:
        agg_map["OTHER"] = "sum"
    if "Volume" in md.columns:
        agg_map["Volume"] = "sum"
    g = md.groupby(keys, dropna=False, sort=False).agg(agg_map).reset_index()
    return _finalize_agg(g)


def _render_filtered_views(
    by_md: pd.DataFrame,
    by_m: pd.DataFrame,
    by_d: pd.DataFrame,
    key_prefix: str,
    by_mh: Optional[pd.DataFrame] = None,
    by_h: Optional[pd.DataFrame] = None,
    by_mhj: Optional[pd.DataFrame] = None,
) -> None:
    """Filtres + tableaux + graphiques. Conçu pour tourner dans un st.fragment."""
    import streamlit as st

    if by_mh is None:
        by_mh = pd.DataFrame()
    if by_h is None:
        by_h = pd.DataFrame()

    merchants = sorted(by_m["Marchand"].dropna().astype(str).unique().tolist()) if not by_m.empty else []
    dates = sorted(by_md["Date_courte"].dropna().astype(str).unique().tolist()) if not by_md.empty else []

    f1, f2, f3 = st.columns([2, 1.2, 1])
    with f1:
        sel_merchants = st.multiselect(
            "Filtrer marchands",
            options=merchants,
            default=[],
            key=f"{key_prefix}_merchants",
            help="Vide = tous les marchands",
        )
    with f2:
        sel_dates = st.multiselect(
            "Filtrer dates",
            options=dates,
            default=[],
            key=f"{key_prefix}_dates",
            help="Vide = toutes les dates",
        )
    with f3:
        min_trx = st.number_input(
            "Min. transactions",
            min_value=0,
            value=0,
            step=1,
            key=f"{key_prefix}_min_trx",
        )

    # Grain fin Marchand × Date
    view_md = by_md.copy() if not by_md.empty else by_md
    if sel_merchants and not view_md.empty:
        view_md = view_md[view_md["Marchand"].astype(str).isin(sel_merchants)]
    if sel_dates and not view_md.empty:
        view_md = view_md[view_md["Date_courte"].astype(str).isin(sel_dates)]

    if sel_dates or sel_merchants:
        view_m = _reagg_sum(view_md, ["Marchand"])
        if not view_m.empty:
            view_m = view_m.sort_values("Nb_transactions", ascending=False)
        view_d = _reagg_sum(view_md, ["Date_courte"])
        if not view_d.empty:
            view_d = view_d.sort_values("Date_courte")
    else:
        view_m = by_m.copy() if not by_m.empty else by_m
        view_d = by_d.copy() if not by_d.empty else by_d
        if sel_merchants and not view_m.empty:
            view_m = view_m[view_m["Marchand"].astype(str).isin(sel_merchants)]

    if min_trx > 0:
        if not view_md.empty and "Nb_transactions" in view_md.columns:
            view_md = view_md[view_md["Nb_transactions"] >= min_trx]
        if not view_m.empty and "Nb_transactions" in view_m.columns:
            view_m = view_m[view_m["Nb_transactions"] >= min_trx]
        if sel_dates or sel_merchants:
            view_m = _reagg_sum(view_md, ["Marchand"])
            if not view_m.empty:
                view_m = view_m.sort_values("Nb_transactions", ascending=False)
            view_d = _reagg_sum(view_md, ["Date_courte"])
            if not view_d.empty:
                view_d = view_d.sort_values("Date_courte")

    # Profil par heure de journée (0–23) — style référence "par Heure"
    if by_mhj is None:
        by_mhj = pd.DataFrame()
    view_mhj = by_mhj.copy() if isinstance(by_mhj, pd.DataFrame) and not by_mhj.empty else pd.DataFrame()
    if not view_mhj.empty:
        if sel_merchants:
            view_mhj = view_mhj[view_mhj["Marchand"].astype(str).isin(sel_merchants)]
        if sel_dates and "Date_courte" in view_mhj.columns:
            view_mhj = view_mhj[view_mhj["Date_courte"].astype(str).isin(sel_dates)]
        # Ré-agrégation sur l'heure de la journée uniquement
        view_hj = _reagg_sum(view_mhj, ["Heure_jour"]) if "Heure_jour" in view_mhj.columns else pd.DataFrame()
        if not view_hj.empty:
            view_hj = view_hj.sort_values("Heure_jour")
        if min_trx > 0 and not view_hj.empty and "Nb_transactions" in view_hj.columns:
            view_hj = view_hj[view_hj["Nb_transactions"] >= min_trx]
    else:
        view_hj = pd.DataFrame()

    # KPI sur la sélection
    if not view_md.empty and "Nb_transactions" in view_md.columns:
        total_n = int(view_md["Nb_transactions"].sum())
        total_ok = int(view_md["SUCCESS"].sum()) if "SUCCESS" in view_md.columns else 0
        total_pend = int(view_md["PENDING"].sum()) if "PENDING" in view_md.columns else 0
        total_fail = int(view_md["FAILED"].sum()) if "FAILED" in view_md.columns else 0
        global_rate = round(100.0 * total_ok / total_n, 2) if total_n else 0.0
    elif not view_m.empty and "Nb_transactions" in view_m.columns:
        total_n = int(view_m["Nb_transactions"].sum())
        total_ok = int(view_m["SUCCESS"].sum()) if "SUCCESS" in view_m.columns else 0
        total_pend = int(view_m["PENDING"].sum()) if "PENDING" in view_m.columns else 0
        total_fail = int(view_m["FAILED"].sum()) if "FAILED" in view_m.columns else 0
        global_rate = round(100.0 * total_ok / total_n, 2) if total_n else 0.0
    else:
        total_n = total_ok = total_pend = total_fail = 0
        global_rate = 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Transactions", f"{total_n:,}")
    c2.metric("SUCCESS", f"{total_ok:,}")
    c3.metric("PENDING", f"{total_pend:,}")
    c4.metric("FAILED", f"{total_fail:,}")
    c5.metric("Taux conversion", f"{global_rate:.1f}%")

    tab_m, tab_md, tab_d, tab_chart = st.tabs(
        [
            "👥 Par marchand",
            "📅 Marchand × Date",
            "📆 Par date (global)",
            "📊 Graphiques",
        ]
    )

    col_cfg = {
        "Pct_SUCCESS": st.column_config.NumberColumn("Pct SUCCESS %", format="%.2f"),
        "Pct_PENDING": st.column_config.NumberColumn("Pct PENDING %", format="%.2f"),
        "Pct_FAILED": st.column_config.NumberColumn("Pct FAILED %", format="%.2f"),
        "Volume": st.column_config.NumberColumn("Volume", format="%.2f"),
        "Nb_transactions": st.column_config.NumberColumn("Nb trx", format="%d"),
    }

    with tab_m:
        st.caption(
            "Agrégat sur la sélection courante (filtres marchands / dates appliqués) — "
            "trié par volume de transactions décroissant."
        )
        st.dataframe(view_m, use_container_width=True, hide_index=True, column_config=col_cfg)
        st.download_button(
            "⬇️ Export CSV — Par marchand",
            data=view_m.to_csv(index=False).encode("utf-8-sig"),
            file_name="taux_conversion_par_marchand.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_m",
        )

    with tab_md:
        st.caption("Détail par marchand et par date courte (YYYY-MM-DD).")
        st.dataframe(view_md, use_container_width=True, hide_index=True, column_config=col_cfg)
        st.download_button(
            "⬇️ Export CSV — Marchand × Date",
            data=view_md.to_csv(index=False).encode("utf-8-sig"),
            file_name="taux_conversion_marchand_date.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_md",
        )

    with tab_d:
        st.caption("Vue consolidée toutes transactions par date courte.")
        st.dataframe(view_d, use_container_width=True, hide_index=True, column_config=col_cfg)

    with tab_chart:
        try:
            import plotly.express as px

            top_n = st.slider("Top N marchands (par nb transactions)", 5, 30, 15, key=f"{key_prefix}_topn")
            top = view_m.head(top_n) if not view_m.empty else view_m
            if not top.empty:
                fig = px.bar(
                    top,
                    x="Marchand",
                    y=["Pct_SUCCESS", "Pct_PENDING", "Pct_FAILED"],
                    title=f"Répartition des statuts — Top {top_n} marchands",
                    labels={"value": "%", "variable": "Statut"},
                    barmode="stack",
                    color_discrete_map={
                        "Pct_SUCCESS": "#22C55E",
                        "Pct_PENDING": "#F59E0B",
                        "Pct_FAILED": "#EF4444",
                    },
                    template="plotly_white",
                )
                fig.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=50, b=80),
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font=dict(color="#000000", size=11),
                    xaxis_tickangle=-35,
                    legend_title_text="",
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Évolution par heure de la journée (0–23) — style référence
            # Filtres marchands / dates / min trx déjà appliqués sur view_hj
            import plotly.graph_objects as go

            chart_df = view_hj if isinstance(view_hj, pd.DataFrame) else pd.DataFrame()
            if chart_df.empty or "Heure_jour" not in chart_df.columns or "Pct_SUCCESS" not in chart_df.columns:
                st.warning(
                    "Impossible de tracer l'évolution horaire : aucune heure exploitable "
                    "dans le fichier PMT. Vérifiez la présence de **Created Date** "
                    "(ou équivalent avec heure), pas seulement une date jour."
                )
            else:
                chart_df = chart_df.dropna(subset=["Heure_jour"]).copy()
                chart_df["Heure_jour"] = chart_df["Heure_jour"].astype(int).clip(0, 23)
                chart_df = chart_df.sort_values("Heure_jour")

                n_hours = int(chart_df["Heure_jour"].nunique())
                if n_hours <= 1:
                    st.info(
                        f"Une seule heure distincte détectée ({int(chart_df['Heure_jour'].iloc[0])}h). "
                        "Le fichier PMT fournit probablement une **date sans heure** "
                        "sur la colonne utilisée. L'évolution 0h–23h nécessite "
                        "**Created Date** (horodatage complet)."
                    )

                # Titre dynamique selon filtre marchand
                if len(sel_merchants) == 1:
                    series_name = str(sel_merchants[0])
                    title = f"Évolution du Taux de Conversion — {series_name}"
                elif len(sel_merchants) > 1:
                    series_name = f"{len(sel_merchants)} marchands"
                    title = "Évolution du Taux de Conversion (sélection)"
                else:
                    series_name = "Tous marchands"
                    title = "Évolution du Taux de Conversion par Heure"

                # Compléter les heures manquantes 0–23 (ligne continue, gaps = null)
                full = pd.DataFrame({"Heure_jour": list(range(24))})
                chart_df = full.merge(chart_df, on="Heure_jour", how="left")

                x_vals = chart_df["Heure_jour"].tolist()
                y_vals = [
                    (float(v) if pd.notna(v) else None)
                    for v in chart_df["Pct_SUCCESS"].tolist()
                ]
                text_labels = [
                    (f"{v:.0f}%" if v is not None else "")
                    for v in y_vals
                ]

                # Position des labels : sous le point si taux élevé (≥90 %), sinon au-dessus
                # → évite que les % soient coupés en haut du graphique
                text_positions = []
                for v in y_vals:
                    if v is None:
                        text_positions.append("top center")
                    elif v >= 90:
                        text_positions.append("bottom center")
                    else:
                        text_positions.append("top center")

                fig2 = go.Figure()
                fig2.add_trace(
                    go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines+markers+text",
                        name=series_name,
                        text=text_labels,
                        textposition=text_positions,
                        textfont=dict(size=10, color="#2F5D1A", family="Arial"),
                        line=dict(color="#70AD47", width=2.5),
                        marker=dict(size=9, color="#70AD47", line=dict(width=1, color="#FFFFFF")),
                        hovertemplate="Heure %{x}h<br>Taux %{y:.1f}%<extra></extra>",
                        cliponaxis=False,
                    )
                )
                fig2.update_layout(
                    title=dict(text=title, x=0.5, xanchor="center", font=dict(size=15, color="#1a1a1a")),
                    height=440,
                    margin=dict(l=50, r=20, t=70, b=55),
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font=dict(color="#333333", size=11),
                    xaxis=dict(
                        title="Évolution du Taux de Conversion par Heure",
                        dtick=1,
                        range=[-0.5, 23.5],
                        showgrid=True,
                        gridcolor="#EEEEEE",
                        zeroline=False,
                    ),
                    yaxis=dict(
                        title="",
                        range=[-2, 108],
                        ticksuffix="%",
                        showgrid=True,
                        gridcolor="#EEEEEE",
                        zeroline=False,
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    showlegend=True,
                    # Laisse dépasser les labels hors zone de tracé
                    uniformtext_minsize=8,
                    uniformtext_mode="hide",
                )
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": True})
                st.caption(
                    "Profil par heure de la journée (0h–23h) sur la sélection courante "
                    "(filtres marchands, dates, min. transactions)."
                )
        except Exception as e:
            st.caption(f"Graphiques indisponibles : {e}")


def render_merchant_conversion(dfpmt: pd.DataFrame, key_prefix: str = "mc") -> None:
    """
    Affiche le module complet « Taux de conversion par marchand ».
    100 % défensif : absence de colonnes → message clair, pas d'exception.
    Filtres isolés (fragment) pour ne pas recharger toute la page.
    """
    import streamlit as st

    st.caption(
        "Pour chaque marchand et chaque date/heure : nombre de transactions, "
        "SUCCESS / PENDING / FAILED et pourcentages associés. "
        "Source : fichier PMT (statuts normalisés)."
    )

    if dfpmt is None or not isinstance(dfpmt, pd.DataFrame) or dfpmt.empty:
        st.info("Aucune donnée PMT disponible pour le calcul des taux de conversion.")
        return

    m_col = _resolve_col(dfpmt, _MERCHANT_CANDIDATES)
    s_col = _resolve_col(dfpmt, _STATUS_CANDIDATES)
    if not m_col or not s_col:
        st.warning(
            "Colonnes **Merchant Name** et/ou **Statut** introuvables dans le fichier PMT. "
            "Impossible de calculer les taux de conversion marchand."
        )
        return

    cached = _get_cached_aggregates(dfpmt, key_prefix)
    if len(cached) == 6:
        by_md, by_m, by_d, by_mh, by_h, by_mhj = cached
    else:
        by_md, by_m, by_d = cached[0], cached[1], cached[2]
        by_mh = cached[3] if len(cached) > 3 else pd.DataFrame()
        by_h = cached[4] if len(cached) > 4 else pd.DataFrame()
        by_mhj = pd.DataFrame()

    if by_m.empty:
        st.info("Aucune agrégation possible (données insuffisantes).")
        return

    fragment = getattr(st, "fragment", None)
    if callable(fragment):
        @fragment
        def _filtered_section():
            _render_filtered_views(
                by_md, by_m, by_d, key_prefix, by_mh=by_mh, by_h=by_h, by_mhj=by_mhj
            )

        _filtered_section()
    else:
        _render_filtered_views(
            by_md, by_m, by_d, key_prefix, by_mh=by_mh, by_h=by_h, by_mhj=by_mhj
        )
