"""
RecoTrust V5.1 — Sessions persistantes côté serveur (survie au F5).

Stockage : fichier JSON sous data/sessions/
Jeton opaque (sid) dans l'URL — jamais d'e-mail, mot de passe ou rôle en clair.
Durée de vie : 12 h d'inactivité (glissante).
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

_lock = threading.Lock()

_APP_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = Path(os.environ.get("RECOTRUST_DATA_DIR", str(_APP_ROOT / "data")))
_SESSIONS_DIR = _DATA_DIR / "sessions"

# 12 heures d'inactivité
_TTL_SECONDS = int(os.environ.get("RECOTRUST_SESSION_TTL", str(12 * 3600)))

# Clés de travail légères à restaurer (pas de DataFrames ni bytes Excel)
_WORK_KEYS = (
    "config_step",
    "already_processed",
    "saved_reco_start",
    "saved_reco_end",
    "saved_match_col_pmt",
    "saved_match_col_partner",
    "app_view",
    "reco_type_select",  # may not work for widgets
    "partner_select",
    "upload_sig",
    "reco_elapsed_sec",
    # noms de fichiers pour message UX (pas le contenu)
    "last_pmt_name",
    "last_partner_name",
    "last_reco_type",
    "last_partner_label",
)


def _ensure_dir() -> None:
    try:
        _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _path(token: str) -> Path:
    # sanitize token to filename
    safe = "".join(c for c in token if c.isalnum() or c in ("-", "_"))[:128]
    return _SESSIONS_DIR / f"{safe}.json"


def create_session(email: str, role: str, display_name: str) -> str:
    """Crée une session serveur et retourne le jeton opaque."""
    _ensure_dir()
    token = secrets.token_urlsafe(32)
    now = time.time()
    payload = {
        "token": token,
        "email": email,
        "role": role,
        "display_name": display_name,
        "created_at": now,
        "last_seen": now,
        "work": {},
    }
    with _lock:
        try:
            _path(token).write_text(
                json.dumps(payload, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass
    return token


def load_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Charge et valide une session. None si absente / expirée."""
    if not token or not isinstance(token, str) or len(token) < 16:
        return None
    path = _path(token)
    with _lock:
        try:
            if not path.is_file():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    last = float(data.get("last_seen") or 0)
    if time.time() - last > _TTL_SECONDS:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return None

    # sliding expiration
    data["last_seen"] = time.time()
    with _lock:
        try:
            path.write_text(
                json.dumps(data, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass
    return data


def destroy_session(token: Optional[str]) -> None:
    if not token:
        return
    with _lock:
        try:
            _path(token).unlink(missing_ok=True)
        except Exception:
            pass


def save_work_state(token: Optional[str], work: Dict[str, Any]) -> None:
    """Persiste un snapshot léger de l'état de travail (sans fichiers binaires)."""
    if not token:
        return
    path = _path(token)
    with _lock:
        try:
            if not path.is_file():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            data["last_seen"] = time.time()
            # sérialiser dates
            clean = {}
            for k, v in work.items():
                if k not in _WORK_KEYS and not str(k).startswith("saved_"):
                    continue
                if hasattr(v, "isoformat"):
                    clean[k] = v.isoformat()
                else:
                    try:
                        json.dumps(v)
                        clean[k] = v
                    except Exception:
                        clean[k] = str(v)
            data["work"] = clean
            path.write_text(
                json.dumps(data, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass


def cleanup_expired() -> int:
    """Supprime les sessions expirées. Retourne le nombre supprimé."""
    _ensure_dir()
    removed = 0
    now = time.time()
    with _lock:
        try:
            for p in _SESSIONS_DIR.glob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    last = float(data.get("last_seen") or 0)
                    if now - last > _TTL_SECONDS:
                        p.unlink(missing_ok=True)
                        removed += 1
                except Exception:
                    try:
                        p.unlink(missing_ok=True)
                        removed += 1
                    except Exception:
                        pass
        except Exception:
            pass
    return removed
