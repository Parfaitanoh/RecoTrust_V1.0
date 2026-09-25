"""
V1.2.0 — Schéma PMT souple.

Les colonnes du fichier Paymetrust sont CONSERVÉES telles quelles
(aucun renommage destructif). Des alias standard sont ajoutés uniquement
s'ils sont absents, afin que la logique métier historique continue de
fonctionner quel que soit le nommage du fichier source
(snake_case historique OU libellés déjà normalisés).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

# standard_name -> candidats possibles dans le fichier source (ordre de priorité)
PMT_COLUMN_ALIASES: Dict[str, List[str]] = {
    "Created Date": ["Created Date", "created_at", "Created At", "created date"],
    "Payment Date": ["Payment Date", "payment_date", "Payment At", "payment date"],
    "Operator": ["Operator", "operator"],
    "External Transaction Id": [
        "External Transaction Id",
        "external_transaction_id",
        "External Transaction ID",
        "external_transaction_ID",
    ],
    "Merchant Name": ["Merchant Name", "merchant_name", "Merchant"],
    "Transaction ID": [
        "Transaction ID",
        "transaction_id",
        "Transaction Id",
        "transactionId",
        "id_transaction",
    ],
    "ID Opérateur": [
        "ID Opérateur",
        "id_operator",
        "ID Operator",
        "Id Operator",
        "idoperator",
    ],
    "Phone Number": [
        "Phone Number",
        "phone_number",
        "Phone",
        "msisdn",
        "MSISDN",
    ],
    "Montant": ["Montant", "amount", "Amount", "montant"],
    "Pays": ["Pays", "country", "Country", "pays"],
    "Fee amount": ["Fee amount", "fee_amount", "Fee Amount", "fees"],
    "Merchant amount": [
        "Merchant amount",
        "merchant_amount",
        "Merchant Amount",
    ],
    "Statut": ["Statut", "statut", "Status", "status", "STATE"],
}


def _find_source_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Retourne le premier candidat présent dans df (comparaison exacte puis insensible à la casse)."""
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


def prepare_pmt_dataframe(pmt: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare le DataFrame PMT pour la réconciliation :

    1. Conserve **toutes** les colonnes d'origine (aucune suppression / renommage).
    2. Ajoute les alias standard absents en copiant depuis les candidats connus.
    3. Crée la colonne ``Date`` (jour) si possible.
    4. Convertit ``Montant`` en numérique.
    5. Déduplique sur Transaction ID / transaction_id.
    6. Cast ``Phone Number`` en object si présent.

    Compatible avec les anciens exports (snake_case) et les nouveaux
    fichiers déjà libellés.
    """
    if pmt is None or not isinstance(pmt, pd.DataFrame):
        return pmt

    df = pmt.copy()

    # --- Alias standard (ajout uniquement, colonnes d'origine intactes) ---
    for standard, candidates in PMT_COLUMN_ALIASES.items():
        if standard in df.columns:
            continue
        src = _find_source_column(df, candidates)
        if src is not None:
            df[standard] = df[src]

    # --- Date journalière ---
    if "Date" not in df.columns:
        date_src = _find_source_column(
            df,
            ["created_at", "Created Date", "Created At", "payment_date", "Payment Date", "Date"],
        )
        if date_src is not None:
            def _extract_day(val):
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return val
                try:
                    if hasattr(val, "strftime"):
                        return val.strftime("%Y-%m-%d")
                except Exception:
                    pass
                s = str(val).strip()
                if not s or s.lower() in ("nan", "nat", "none"):
                    return None
                # "2026-09-05 12:30:00" ou "2026-09-05T12:30:00"
                return s.replace("T", " ").split(" ")[0]

            df["Date"] = df[date_src].apply(_extract_day)

    # --- Montant numérique ---
    if "Montant" in df.columns:
        df["Montant"] = pd.to_numeric(df["Montant"], errors="coerce")
    else:
        amt_src = _find_source_column(df, ["amount", "Amount", "montant"])
        if amt_src is not None:
            df[amt_src] = pd.to_numeric(df[amt_src], errors="coerce")
            df["Montant"] = df[amt_src]

    # --- Déduplication ---
    dedupe_key = _find_source_column(
        df, ["Transaction ID", "transaction_id", "Transaction Id", "id_transaction"]
    )
    if dedupe_key is not None:
        df = df.drop_duplicates(subset=dedupe_key, keep="first")

    # --- Phone Number en object ---
    if "Phone Number" in df.columns:
        df["Phone Number"] = df["Phone Number"].astype(object)

    return df


def resolve_pmt_column(df: pd.DataFrame, logical_name: str) -> Optional[str]:
    """
    Résout un nom logique vers une colonne réellement présente dans df.
    Utile pour le matching dynamique et les exports.
    """
    candidates = PMT_COLUMN_ALIASES.get(logical_name, [logical_name])
    # logical_name lui-même en tête
    ordered = [logical_name] + [c for c in candidates if c != logical_name]
    return _find_source_column(df, ordered)
