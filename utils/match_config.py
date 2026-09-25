"""
Configuration des colonnes de matching par défaut (V1.1).

Ces valeurs reproduisent exactement les clés hardcodées de la V1.0
pour chaque couple (type, partenaire). Elles servent de défauts
dans l'UI et de fallback dans les processeurs.

L'utilisateur peut les surcharger dynamiquement après chargement des fichiers
sans modifier les règles métier (filtres, calculs, KPI, exports).
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

# (reco_type, partner_display_name) -> (colonne_PMT_au_moment_du_match, colonne_Partenaire)
# Les noms côté PMT sont ceux APRÈS rename dans le processeur.
# Les noms côté partenaire sont ceux utilisés au moment du isin/set_index
# (parfois une colonne transformée, ex. Externalid).
DEFAULT_MATCH_KEYS: Dict[Tuple[str, str], Tuple[str, str]] = {
    # --- Payment (payin) ---
    ("Payment", "Bizao"): ("External Transaction Id", "Order ID"),
    ("Payment", "CinetPay"): ("Transaction ID", "ID transaction"),
    ("Payment", "Ifutur"): ("Transaction ID", "external_reference"),
    ("Payment", "Moov BF"): ("Transaction ID", "ThirdPartyTransactionId"),
    ("Payment", "Moov CI"): ("ID Opérateur", "Receipt No."),
    ("Payment", "MTN CI"): ("Transaction ID", "Externalid"),
    ("Payment", "MTN CM"): ("Transaction ID", "Externalid"),
    ("Payment", "OM BF"): ("Transaction ID", "FTXN_ID"),
    ("Payment", "Orange CI"): ("ID Opérateur", "Reference"),
    ("Payment", "Wave BF"): ("Transaction ID", "Référence client"),
    ("Payment", "Wave CI"): ("Transaction ID", "Référence client"),
    ("Payment", "Wave SN"): ("Transaction ID", "Référence client"),
    ("Payment", "Orange SN"): ("Transaction ID", "Référence Partenaire"),
        
    # --- Transfer (payout) ---
    
    ("Transfer", "CinetPay"): ("Transaction ID", "ID Marchand"),
    ("Transfer", "Ifutur"): ("ID Opérateur", "REFERENCE"),
    ("Transfer", "Moov BF"): ("Transaction ID", "ThirdPartyTransactionId"),
    ("Transfer", "Moov CI"): ("ID Opérateur", "Receipt No."),
    ("Transfer", "MTN CI"): ("Transaction ID", "External id"),
    ("Transfer", "MTN CM"): ("Transaction ID", "External id"),
    ("Transfer", "OM BF"): ("Transaction ID", "FTXN_ID"),
    ("Transfer", "Orange CI"): ("ID Opérateur", "Reference"),
    ("Transfer", "Wave BF"): ("Transaction ID", "Référence client"),
    ("Transfer", "Wave CI"): ("Transaction ID", "Référence client"),
    ("Transfer", "Wave SN"): ("Transaction ID", "Référence client"),
    ("Transfer", "Orange SN"): ("Transaction ID", "Référence Partenaire"),
}


def get_default_match_keys(reco_type: str, partner: str) -> Tuple[str, str]:
    """Retourne (col_pmt, col_partner) par défaut pour le couple donné."""
    return DEFAULT_MATCH_KEYS.get(
        (reco_type, partner),
        ("Transaction ID", "Transaction ID"),
    )


def resolve_match_key(
    override: Optional[str],
    default: str,
    available_columns,
) -> str:
    """
    Choisit la colonne de matching à utiliser :
    1. override s'il est fourni et présent dans les colonnes disponibles
    2. sinon default s'il est présent
    3. sinon override même s'il n'est pas listé (laisser le processeur échouer proprement)
    4. sinon default
    """
    cols = set(available_columns) if available_columns is not None else set()
    if override and (not cols or override in cols):
        return override
    if default in cols or not cols:
        return default
    if override:
        return override
    return default
