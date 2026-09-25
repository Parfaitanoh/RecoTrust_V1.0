"""
Registre centralisé des processeurs de réconciliation — chargement LAZY.

Architecture :
  PROCESSORS[type_reco][nom_partenaire] = "module.ClassName"  (chaîne)

Le module n'est importé qu'au moment où get_processor() est appelé.
→ Démarrage ultra-rapide (local + cloud), faible empreinte mémoire.

Pour ajouter un nouveau partenaire (voir aussi PROCEDURE_NOUVEAU_PARTENAIRE.md) :
  1. Créer partenaires/<code>_payin.py et/ou <code>_payout.py avec classe *Processor
  2. L'enregistrer dans PROCESSORS : "Libellé UI": "module.ClassName"
  3. Ajouter les clés de matching dans utils/match_config.py (même libellé UI)
  4. python -m py_compile partenaires/<module>.py puis redémarrer Streamlit

Sans l'étape 1, erreur : No module named 'partenaires.<module>'
"""

from __future__ import annotations

import importlib
from typing import Dict, List, Optional, Type, Any

# ---------------------------------------------------------------------------
# Registre central — source unique de vérité (références LAZY par chaîne)
# ---------------------------------------------------------------------------
# Clé niveau 1 : type de réconciliation ("Payment" | "Transfer")
# Clé niveau 2 : nom affiché du partenaire (utilisé dans la selectbox)
# Valeur      : "module_name.ClassName"  → import uniquement à la demande
# ---------------------------------------------------------------------------
PROCESSORS: Dict[str, Dict[str, Optional[str]]] = {
    "Payment": {
        "Bizao": "bizao_payin.BizaoPayinProcessor",
        "CinetPay": "cinetpay_payin.CinetpayPayinProcessor",
        "Ifutur": "ifutur_payin.ifuturPayinProcessor",
        "Moov CI": "moovci_payin.MoovciPayinProcessor",
        "MTN CI": "mtnci_payin.MtnciPayinProcessor",
        "MTN CM": "mtncm_payin.MtncmPayinProcessor",
        "OM BF": "ombf_payin.OmbfPayinProcessor",
        "Orange CI": "omci_payin.OmciPayinProcessor",
        "Wave BF": "wavebf_payin.WavebfPayinProcessor",
        "Wave CI": "waveci_payin.WaveciPayinProcessor",
        "Wave SN": "wavesn_payin.WavesnPayinProcessor",
        "Moov BF": "moovbf_payin.MoovbfPayinProcessor",
        "Orange SN": "orangesn_payin.OrangesnPayinProcessor",
    },
    "Transfer": {
        "CinetPay": "cinetpay_payout.CinetpayPayoutProcessor",
        "Ifutur": "ifutur_payout.IfuturPayoutProcessor",
        "MTN CI": "mtnci_payout.MtnciPayoutProcessor",
        "MTN CM": "mtncm_payout.MtncmPayoutProcessor",
        "OM BF": "ombf_payout.OmbfPayoutProcessor",
        "Orange CI": "omci_payout.OmciPayoutProcessor",
        "Wave BF": "wavebf_payout.WavebfPayoutProcessor",
        "Wave CI": "waveci_payout.WaveciPayoutProcessor",
        "Wave SN": "wavesn_payout.WavesnPayoutProcessor",
        "Moov BF": "moovbf_payout.MoovbfPayoutProcessor",
        "Moov CI": "moovci_payout.MoovciPayoutProcessor",
        "Orange SN": "orangesn_payout.OrangesnPayoutProcessor",
    },
}

# Ordre d'affichage des types dans la selectbox
RECO_TYPES: List[str] = ["Payment", "Transfer"]

# Cache des classes déjà importées (évite re-importlib dans la même session process)
_CLASS_CACHE: Dict[str, Type] = {}


def _resolve_class(ref: str) -> Type:
    """
    Résout "module.ClassName" → classe Python.
    Import lazy + cache process-local.
    """
    if ref in _CLASS_CACHE:
        return _CLASS_CACHE[ref]

    module_name, _, class_name = ref.rpartition(".")
    if not module_name or not class_name:
        raise ValueError(f"Référence processeur invalide : « {ref} »")

    # Import relatif au package partenaires
    mod = importlib.import_module(f".{module_name}", package=__name__)
    cls = getattr(mod, class_name)
    _CLASS_CACHE[ref] = cls
    return cls


def get_available_partners(reco_type: str) -> List[str]:
    """Retourne la liste triée des partenaires disponibles pour un type donné."""
    partners = PROCESSORS.get(reco_type, {})
    return sorted(partners.keys())


def get_processor(
    reco_type: str,
    partner: str,
    data_file,
    partner_file,
    reco_start=None,
    reco_end=None,
    reco_date=None,
    match_col_pmt=None,
    match_col_partner=None,
):
    """
    Instancie et retourne le processeur correspondant au couple
    (type de réconciliation, partenaire).

    Le module du partenaire n'est importé qu'ici (lazy).
    Le nom du fichier n'intervient plus dans la sélection.

    V1.1 — match_col_pmt / match_col_partner : colonnes de matching
    choisies dynamiquement par l'utilisateur (optionnel). Si None,
    chaque processeur conserve ses clés hardcodées d'origine.
    """
    # Compatibilité V1.1.1 : une seule date → plage d'un jour
    if reco_date is not None and reco_start is None and reco_end is None:
        reco_start = reco_date
        reco_end = reco_date

    type_map = PROCESSORS.get(reco_type)
    if type_map is None:
        raise ValueError(
            f"Type de réconciliation inconnu : « {reco_type} ». "
            f"Valeurs attendues : {', '.join(RECO_TYPES)}."
        )

    ref = type_map.get(partner)
    if ref is None:
        available = [k for k, v in type_map.items() if v is not None]
        if partner in type_map:
            raise ValueError(
                f"Le processeur « {reco_type} / {partner} » n'est pas encore implémenté. "
                f"Ajoutez la classe dans partenaires/ et référencez-la dans PROCESSORS."
            )
        raise ValueError(
            f"Partenaire « {partner} » non disponible pour le type « {reco_type} ». "
            f"Partenaires disponibles : {', '.join(available) if available else 'aucun'}."
        )

    cls = _resolve_class(ref)
    return cls(
        data_file,
        partner_file,
        reco_start=reco_start,
        reco_end=reco_end,
        match_col_pmt=match_col_pmt,
        match_col_partner=match_col_partner,
    )
