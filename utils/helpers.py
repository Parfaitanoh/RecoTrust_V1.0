def metric_card(title, value, color="#6366F1", icon=""):
    """Carte KPI premium (présentation uniquement — mêmes valeurs métier)."""
    icon_html = f'<span style="margin-right:6px;opacity:0.85;">{icon}</span>' if icon else ""
    return f"""
    <div class="rw-metric" style="border-left-color:{color};">
        <div class="rw-metric-title">{icon_html}{title}</div>
        <div class="rw-metric-value">{value}</div>
    </div>
    """


def safe_show(df, max_rows=2000, label=None):
    """
    Affiche un DataFrame de façon performante.
    - Pas de copie inutile si index déjà RangeIndex
    - Limitation d'aperçu pour les très gros tableaux (UI fluide)
    """
    import streamlit as st
    import pandas as pd

    if df is None:
        st.info("Aucune donnée")
        return
    if not isinstance(df, pd.DataFrame):
        st.write(df)
        return

    n = len(df)
    if label:
        st.caption(f"{label} — {n:,} lignes")
    else:
        st.caption(f"{n:,} lignes")

    if n == 0:
        st.info("Tableau vide")
        return

    # Éviter .copy() + reset_index si déjà propre
    needs_reset = not isinstance(df.index, pd.RangeIndex) or df.index.name is not None
    if n > max_rows:
        st.warning(
            f"Aperçu des {max_rows:,} premières lignes sur {n:,} "
            "(export Excel pour le détail complet)."
        )
        view = df.head(max_rows)
        if needs_reset:
            view = view.reset_index()
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        view = df.reset_index() if needs_reset else df
        st.dataframe(view, use_container_width=True, hide_index=True)


def filter_succes_abs_by_reco_date(df, reco_start=None, reco_end=None, date_col="Date"):
    """Filtre SUCCESS absents partenaire sur [reco_start, reco_end] inclus."""
    import pandas as pd
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df, 0
    if reco_start is None and reco_end is None:
        return df, len(df)
    before = len(df)
    if date_col not in df.columns:
        return df, before

    series = pd.to_datetime(df[date_col], errors="coerce")
    mask = pd.Series(True, index=df.index)

    if reco_start is not None:
        try:
            start = pd.Timestamp(reco_start).normalize()
        except Exception:
            start = pd.to_datetime(str(reco_start)[:10], errors="coerce")
        if pd.notna(start):
            mask &= series.dt.normalize() >= start

    if reco_end is not None:
        try:
            end = pd.Timestamp(reco_end).normalize()
        except Exception:
            end = pd.to_datetime(str(reco_end)[:10], errors="coerce")
        if pd.notna(end):
            mask &= series.dt.normalize() <= end

    return df.loc[mask].copy(), before


def format_maj_sheet(df, operation_origin: str = "Payment"):
    """
    Formate la feuille « transactions à mettre à jour » au format opérationnel :

        Phone Number | Operation origin | Transaction ID | Message | partner_unique_id

    - Phone Number : numéro avec préfixe « + »
    - Operation origin : « Payment » (payin) ou « transfer » (payout)
    - Transaction ID : identifiant transaction PMT
    - Message : toujours « SUCCESS » (statut cible de la mise à jour)
    - partner_unique_id : IDOPERATOR (réf. partenaire), sinon ID Opérateur / External Transaction Id
    """
    import pandas as pd

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(
            columns=[
                "Phone Number",
                "Operation origin",
                "Transaction ID",
                "Message",
                "partner_unique_id",
            ]
        )

    out = pd.DataFrame(index=df.index)

    # Phone Number avec « + » (alias V1.2.0)
    _phone_col = None
    for _c in ("Phone Number", "phone_number", "Phone", "msisdn", "MSISDN"):
        if _c in df.columns:
            _phone_col = _c
            break
    if _phone_col is not None:
        phones = df[_phone_col].astype(str).str.strip()
        phones = phones.replace({"nan": "", "None": "", "NaT": ""})
        phones = phones.apply(
            lambda x: x if (not x or str(x).startswith("+")) else f"+{x}"
        )
        out["Phone Number"] = phones
    else:
        out["Phone Number"] = ""

    # Operation origin
    origin = (operation_origin or "Payment").strip()
    if origin.lower() in ("transfer", "payout", "transfer/payout"):
        origin = "transfer"
    else:
        origin = "Payment"
    out["Operation origin"] = origin

    # Transaction ID (alias V1.2.0)
    _tid_col = None
    for _c in ("Transaction ID", "transaction_id", "Transaction Id", "id_transaction"):
        if _c in df.columns:
            _tid_col = _c
            break
    if _tid_col is not None:
        out["Transaction ID"] = df[_tid_col].astype(object)
    else:
        out["Transaction ID"] = ""

    # Message = statut cible
    out["Message"] = "SUCCESS"

    # partner_unique_id (IDOPERATOR en priorité) — alias V1.2.0
    partner_id = None
    for col in (
        "IDOPERATOR", "ID Opérateur", "id_operator",
        "External Transaction Id", "external_transaction_id",
        "ID Operator",
    ):
        if col in df.columns:
            partner_id = df[col]
            break
    if partner_id is not None:
        out["partner_unique_id"] = partner_id.astype(object)
    else:
        out["partner_unique_id"] = ""

    return out.reset_index(drop=True)


def infer_operation_origin(partner_name: str = "", reco_type: str = "") -> str:
    """Déduit « Payment » ou « transfer » depuis le libellé partenaire / type de reco."""
    blob = f"{partner_name or ''} {reco_type or ''}".upper()
    if any(k in blob for k in ("PAYOUT", "TRANSFER", "TRANSFERT")):
        return "transfer"
    return "Payment"
