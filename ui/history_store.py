"""
Historique léger des réconciliations (métadonnées uniquement).

Ne stocke aucun détail transactionnel. Sert le Dashboard / Historique UI.
Fichier JSON sous data/reco_history.json (ou RECOTRUST_DATA_DIR).
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_MAX_ENTRIES = 500


def _data_dir() -> Path:
    return Path(os.environ.get("RECOTRUST_DATA_DIR", "data"))


def _history_path() -> Path:
    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "reco_history.json"


def _read_all() -> List[Dict[str, Any]]:
    path = _history_path()
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _write_all(entries: List[Dict[str, Any]]) -> None:
    path = _history_path()
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(entries[:_MAX_ENTRIES], f, ensure_ascii=False, indent=0)
    tmp.replace(path)


def append_run(
    *,
    user: str,
    reco_type: str,
    partner: str,
    status: str,
    duration_sec: Optional[float] = None,
    pmt_file: str = "",
    partner_file: str = "",
    match_col_pmt: str = "",
    match_col_partner: str = "",
    error: str = "",
    reco_start: str = "",
    reco_end: str = "",
) -> Dict[str, Any]:
    """Ajoute une entrée d'historique (thread-safe)."""
    entry = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": (user or "")[:120],
        "reco_type": reco_type or "",
        "partner": partner or "",
        "status": status,  # completed | failed
        "duration_sec": round(float(duration_sec), 2) if duration_sec is not None else None,
        "pmt_file": (pmt_file or "")[:200],
        "partner_file": (partner_file or "")[:200],
        "match_col_pmt": (match_col_pmt or "")[:80],
        "match_col_partner": (match_col_partner or "")[:80],
        "error": (error or "")[:200],
        "reco_start": str(reco_start or ""),
        "reco_end": str(reco_end or ""),
    }
    with _LOCK:
        entries = _read_all()
        entries.insert(0, entry)
        _write_all(entries)
    return entry


def list_runs(
    *,
    limit: int = 100,
    partner: Optional[str] = None,
    reco_type: Optional[str] = None,
    status: Optional[str] = None,
    user: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Liste l'historique. Si user est fourni, filtre strict (email, insensible à la casse)."""
    with _LOCK:
        entries = _read_all()
    user_l = (user or "").strip().lower()
    out = []
    for e in entries:
        if partner and e.get("partner") != partner:
            continue
        if reco_type and e.get("reco_type") != reco_type:
            continue
        if status and e.get("status") != status:
            continue
        if user_l and str(e.get("user") or "").strip().lower() != user_l:
            continue
        out.append(e)
        if len(out) >= limit:
            break
    return out


def aggregate_stats(entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Agrégats purement statistiques sur l'historique UI (pas de calcul métier reco)."""
    if entries is None:
        entries = list_runs(limit=_MAX_ENTRIES)
    total = len(entries)
    completed = sum(1 for e in entries if e.get("status") == "completed")
    failed = sum(1 for e in entries if e.get("status") == "failed")
    payin = sum(1 for e in entries if e.get("reco_type") == "Payment")
    payout = sum(1 for e in entries if e.get("reco_type") == "Transfer")
    durations = [e["duration_sec"] for e in entries if isinstance(e.get("duration_sec"), (int, float))]
    avg_dur = round(sum(durations) / len(durations), 1) if durations else None
    by_partner: Dict[str, int] = {}
    for e in entries:
        p = e.get("partner") or "—"
        by_partner[p] = by_partner.get(p, 0) + 1
    top_partners = sorted(by_partner.items(), key=lambda x: -x[1])[:8]
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "success_rate": round(100.0 * completed / total, 1) if total else 0.0,
        "payin": payin,
        "payout": payout,
        "avg_duration_sec": avg_dur,
        "top_partners": top_partners,
    }
