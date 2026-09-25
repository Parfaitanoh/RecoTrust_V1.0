"""
RecoTrust V3.0 — Journalisation professionnelle des événements de sécurité et d'activité.

Événements enregistrés :
  LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT,
  USER_ADDED, USER_DISABLED,
  FILE_UPLOADED, RECONCILIATION_STARTED, RECONCILIATION_COMPLETED,
  RECONCILIATION_FAILED, EXPORT_GENERATED

Les données sensibles (contenu des transactions, secrets, tokens) ne sont jamais loggées.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Logger dédié (n'interfère pas avec le logging Streamlit)
_logger = logging.getLogger("recotrust.audit")
_logger.setLevel(logging.INFO)

# Handler console (toujours actif)
if not _logger.handlers:
    _console = logging.StreamHandler()
    _console.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    _logger.addHandler(_console)

# Fichier de log optionnel (créé uniquement si le dossier est accessible)
_LOG_DIR = Path(os.environ.get("RECOTRUST_LOG_DIR", "logs"))
_file_handler_initialized = False


def _ensure_file_handler() -> None:
    global _file_handler_initialized
    if _file_handler_initialized:
        return
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _LOG_DIR / "recotrust_audit.log"
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        _logger.addHandler(fh)
        _file_handler_initialized = True
    except Exception:
        # Pas de droit d'écriture → on continue uniquement en console
        pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(
    event: str,
    user: Optional[str] = None,
    result: str = "OK",
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
) -> None:
    """
    Enregistre un événement d'audit de façon structurée.

    Parameters
    ----------
    event : str
        Code événement (LOGIN_SUCCESS, FILE_UPLOADED, …)
    user : str | None
        Email de l'utilisateur concerné
    result : str
        "OK" | "FAILED" | "DENIED" …
    details : dict | None
        Métadonnées non sensibles (nom de fichier, nb transactions, durée…)
    level : str
        "INFO" | "WARNING" | "ERROR"
    """
    _ensure_file_handler()

    payload: Dict[str, Any] = {
        "ts": _now_iso(),
        "event": event,
        "user": user or "-",
        "result": result,
    }
    if details:
        # Filtre de sécurité : jamais de contenu de fichier / token / password
        safe = {
            k: v
            for k, v in details.items()
            if k.lower() not in ("password", "token", "secret", "content", "data")
        }
        payload["details"] = safe

    msg = json.dumps(payload, ensure_ascii=False, default=str)

    if level == "ERROR":
        _logger.error(msg)
    elif level == "WARNING":
        _logger.warning(msg)
    else:
        _logger.info(msg)


# Raccourcis pratiques
def login_success(user: str, method: str = "email") -> None:
    log_event("LOGIN_SUCCESS", user=user, details={"method": method})


def login_failed(user: str, reason: str) -> None:
    log_event(
        "LOGIN_FAILED",
        user=user or "-",
        result="DENIED",
        details={"reason": reason},
        level="WARNING",
    )


def logout(user: str) -> None:
    log_event("LOGOUT", user=user)


def file_uploaded(user: str, filename: str, size_bytes: int, kind: str) -> None:
    log_event(
        "FILE_UPLOADED",
        user=user,
        details={"filename": filename, "size_bytes": size_bytes, "kind": kind},
    )


def reconciliation_started(user: str, reco_type: str, partner: str) -> None:
    log_event(
        "RECONCILIATION_STARTED",
        user=user,
        details={"reco_type": reco_type, "partner": partner},
    )


def reconciliation_completed(
    user: str, reco_type: str, partner: str, duration_sec: float
) -> None:
    log_event(
        "RECONCILIATION_COMPLETED",
        user=user,
        details={
            "reco_type": reco_type,
            "partner": partner,
            "duration_sec": round(duration_sec, 2),
        },
    )


def reconciliation_failed(
    user: str, reco_type: str, partner: str, error: str
) -> None:
    log_event(
        "RECONCILIATION_FAILED",
        user=user,
        result="FAILED",
        details={"reco_type": reco_type, "partner": partner, "error": str(error)[:200]},
        level="ERROR",
    )


def export_generated(user: str, export_type: str, filename: str) -> None:
    log_event(
        "EXPORT_GENERATED",
        user=user,
        details={"export_type": export_type, "filename": filename},
    )
