"""Smoke non-régression : registre partenaires cohérent avec les fichiers modules."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from partenaires import PROCESSORS  # noqa: E402


def test_all_processor_modules_exist_and_classes_load():
    missing = []
    bad_class = []
    for reco_type, partners in PROCESSORS.items():
        for name, ref in partners.items():
            if not ref:
                continue
            module_name, _, cls_name = ref.partition(".")
            mod_path = ROOT / "partenaires" / f"{module_name}.py"
            if not mod_path.is_file():
                missing.append(f"{reco_type}/{name}: fichier manquant {mod_path.name}")
                continue
            # Import sans exécuter Streamlit runtime si possible
            try:
                mod = importlib.import_module(f"partenaires.{module_name}")
            except Exception as e:
                # streamlit may be missing in CI minimal — fichier présent suffit alors
                if "streamlit" in str(e).lower():
                    continue
                bad_class.append(f"{reco_type}/{name}: import error {e}")
                continue
            if not hasattr(mod, cls_name):
                bad_class.append(f"{reco_type}/{name}: classe {cls_name} absente")
    assert not missing, "Modules manquants:\n" + "\n".join(missing)
    assert not bad_class, "Classes invalides:\n" + "\n".join(bad_class)


def test_orange_sn_registered():
    assert "Orange SN" in PROCESSORS["Payment"]
    assert "Orange SN" in PROCESSORS["Transfer"]
    assert PROCESSORS["Payment"]["Orange SN"].startswith("orangesn_payin")
    assert PROCESSORS["Transfer"]["Orange SN"].startswith("orangesn_payout")
