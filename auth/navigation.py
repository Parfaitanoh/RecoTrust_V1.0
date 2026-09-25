"""
RecoTrust V4.0 — Navigation navigateur sécurisée.

URLs de type :
  http://localhost:8501/?page=accueil
  http://localhost:8501/?page=connexion
  http://localhost:8501/?page=reconciliation
  http://localhost:8501/?page=administration

Règles de sécurité :
  - Aucune donnée d'identité (e-mail) ni mot de passe dans l'URL
  - `sid` = jeton opaque serveur (survie au F5) — pas un secret métier
  - Seules les clés listées dans ALLOWED_QUERY_KEYS sont conservées
  - Les pages protégées exigent une session authentifiée
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

# Clés d'URL autorisées (navigation uniquement — jamais d'auth)
ALLOWED_QUERY_KEYS = frozenset({"page", "step", "view", "sid"})
# sid = jeton de session opaque côté serveur (pas d'e-mail / mot de passe / rôle)

# Valeurs de page autorisées
PAGE_ACCUEIL = "accueil"
PAGE_CONNEXION = "connexion"
PAGE_RECONCILIATION = "reconciliation"
PAGE_ADMINISTRATION = "administration"

PUBLIC_PAGES = frozenset({PAGE_ACCUEIL, PAGE_CONNEXION})
PROTECTED_PAGES = frozenset({PAGE_RECONCILIATION, PAGE_ADMINISTRATION})
ALL_PAGES = PUBLIC_PAGES | PROTECTED_PAGES

# Clés interdites (strip immédiat si présentes)
_FORBIDDEN_KEYS = frozenset({
    "user", "email", "password", "token", "secret", "auth",
    "session", "code", "state", "access_token", "id_token",
    "refresh_token", "api_key", "key",
})


def sanitize_query_params() -> None:
    """Supprime toute clé non autorisée ou interdite de l'URL."""
    try:
        current = dict(st.query_params)
        if not current:
            return
        dirty = [
            k for k in current.keys()
            if k in _FORBIDDEN_KEYS or k not in ALLOWED_QUERY_KEYS
        ]
        for k in dirty:
            try:
                del st.query_params[k]
            except Exception:
                pass
        # Valider la valeur de page
        page = _raw_page()
        if page and page not in ALL_PAGES:
            try:
                del st.query_params["page"]
            except Exception:
                pass
    except Exception:
        pass


def _raw_page() -> Optional[str]:
    try:
        val = st.query_params.get("page", None)
        if isinstance(val, (list, tuple)):
            val = val[0] if val else None
        return (val or "").strip().lower() or None
    except Exception:
        return None


def get_page() -> str:
    """Retourne la page courante depuis l'URL ou la session."""
    page = _raw_page()
    if page in ALL_PAGES:
        return page
    # Fallback session
    sp = st.session_state.get("nav_page")
    if sp in ALL_PAGES:
        return sp
    return PAGE_ACCUEIL


def set_page(page: str, *, step: Optional[int] = None, view: Optional[str] = None) -> None:
    """
    Met à jour l'URL et la session pour refléter la page courante.
    N'accepte que les pages de la liste blanche.
    """
    page = (page or "").strip().lower()
    if page not in ALL_PAGES:
        page = PAGE_ACCUEIL

    st.session_state["nav_page"] = page

    try:
        # Préserver le jeton de session opaque (survie F5)
        _keep_sid = None
        try:
            _keep_sid = st.query_params.get("sid") or st.session_state.get("_session_token")
            if isinstance(_keep_sid, (list, tuple)):
                _keep_sid = _keep_sid[0] if _keep_sid else None
        except Exception:
            _keep_sid = st.session_state.get("_session_token")

        st.query_params["page"] = page

        if step is not None:
            st.session_state["config_step"] = int(step)
            st.query_params["step"] = str(int(step))
        elif "step" in st.query_params and page not in (
            PAGE_RECONCILIATION,
        ):
            try:
                del st.query_params["step"]
            except Exception:
                pass

        if view is not None:
            view = view if view in ("reco", "admin") else "reco"
            st.session_state["app_view"] = view
            st.query_params["view"] = view
        elif page == PAGE_ADMINISTRATION:
            st.session_state["app_view"] = "admin"
            st.query_params["view"] = "admin"
        elif page == PAGE_RECONCILIATION:
            st.session_state["app_view"] = "reco"
            st.query_params["view"] = "reco"

        if _keep_sid:
            st.query_params["sid"] = str(_keep_sid)
    except Exception:
        pass


def sync_step_to_url(step: int) -> None:
    """Persiste l'étape de configuration dans l'URL (survit au F5)."""
    try:
        st.session_state["config_step"] = int(step)
        st.query_params["step"] = str(int(step))
        if _raw_page() != PAGE_RECONCILIATION:
            st.query_params["page"] = PAGE_RECONCILIATION
            st.session_state["nav_page"] = PAGE_RECONCILIATION
    except Exception:
        pass


def restore_step_from_url() -> Optional[int]:
    """Lit l'étape depuis l'URL si présente."""
    try:
        val = st.query_params.get("step", None)
        if isinstance(val, (list, tuple)):
            val = val[0] if val else None
        if val is None or val == "":
            return None
        return int(val)
    except Exception:
        return None


def restore_view_from_url() -> Optional[str]:
    try:
        val = st.query_params.get("view", None)
        if isinstance(val, (list, tuple)):
            val = val[0] if val else None
        val = (val or "").strip().lower()
        if val in ("reco", "admin"):
            return val
    except Exception:
        pass
    return None


def clear_navigation_params() -> None:
    """Utilisé à la déconnexion — remet l'URL sur l'accueil (sans sid)."""
    try:
        st.query_params.clear()
        st.query_params["page"] = PAGE_ACCUEIL
    except Exception:
        pass
    st.session_state["nav_page"] = PAGE_ACCUEIL
    st.session_state["show_login"] = False
    st.session_state["app_view"] = "reco"


def get_sid() -> Optional[str]:
    """Lit le jeton de session opaque depuis l'URL."""
    try:
        val = st.query_params.get("sid", None)
        if isinstance(val, (list, tuple)):
            val = val[0] if val else None
        val = (val or "").strip()
        return val or None
    except Exception:
        return None


def set_sid(token: Optional[str]) -> None:
    """Écrit ou supprime le jeton opaque dans l'URL."""
    try:
        if token:
            st.query_params["sid"] = token
        elif "sid" in st.query_params:
            del st.query_params["sid"]
    except Exception:
        pass
