"""Notifications utilisateur in-app (session + fichier léger)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

_DATA = Path(__file__).resolve().parents[1] / "data" / "notifications.json"
_MAX = 40


def _load_all() -> Dict[str, List[Dict[str, Any]]]:
    try:
        if _DATA.exists():
            return json.loads(_DATA.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_all(data: Dict[str, List[Dict[str, Any]]]) -> None:
    try:
        _DATA.parent.mkdir(parents=True, exist_ok=True)
        _DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _sync_session(email: str, arr: List[Dict[str, Any]]) -> None:
    st.session_state[f"_notif::{email}"] = list(arr)


def push_notification(
    user_email: str,
    title: str,
    body: str = "",
    kind: str = "success",
) -> None:
    email = (user_email or "").strip().lower()
    if not email:
        return
    item = {
        "id": f"{int(time.time() * 1000)}",
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "body": body,
        "kind": kind,
        "read": False,
    }
    data = _load_all()
    arr = data.get(email, [])
    arr.insert(0, item)
    data[email] = arr[:_MAX]
    _save_all(data)
    _sync_session(email, data[email])


def list_notifications(user_email: str, limit: int = 15) -> List[Dict[str, Any]]:
    email = (user_email or "").strip().lower()
    if not email:
        return []
    key = f"_notif::{email}"
    if key in st.session_state and st.session_state[key] is not None:
        return list(st.session_state[key])[:limit]
    data = _load_all()
    arr = data.get(email, [])[:limit]
    st.session_state[key] = arr
    return arr


def unread_count(user_email: str) -> int:
    return sum(1 for n in list_notifications(user_email) if not n.get("read"))


def mark_all_read(user_email: str) -> None:
    email = (user_email or "").strip().lower()
    if not email:
        return
    data = _load_all()
    arr = data.get(email, [])
    for n in arr:
        n["read"] = True
    data[email] = arr
    _save_all(data)
    _sync_session(email, arr)


def delete_notification(user_email: str, notif_id: str) -> None:
    """Supprime une notification par id (fichier + session)."""
    email = (user_email or "").strip().lower()
    if not email or not notif_id:
        return
    data = _load_all()
    arr = [n for n in data.get(email, []) if str(n.get("id")) != str(notif_id)]
    data[email] = arr
    _save_all(data)
    _sync_session(email, arr)


def clear_all_notifications(user_email: str) -> None:
    """Supprime toutes les notifications de l'utilisateur."""
    email = (user_email or "").strip().lower()
    if not email:
        return
    data = _load_all()
    data[email] = []
    _save_all(data)
    _sync_session(email, [])
