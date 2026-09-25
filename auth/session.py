"""
RecoTrust V4.0 — Gestion des sessions et gate d'authentification.

Flux : Accueil → Connexion → Application
URLs sécurisées :
  ?page=accueil | connexion | reconciliation | administration
Aucune donnée d'auth dans l'URL.
"""
from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st

from auth.users import authenticate, get_role, get_user, is_authorized, normalize_email
from auth.validators import validate_email, validate_password
from auth.navigation import (
    PAGE_ACCUEIL,
    PAGE_ADMINISTRATION,
    PAGE_CONNEXION,
    PAGE_RECONCILIATION,
    clear_navigation_params,
    get_page,
    get_sid,
    sanitize_query_params,
    set_page,
    set_sid,
)
from auth import audit
from auth import persistent_session as psess


def get_authenticated_email() -> Optional[str]:
    if st.session_state.get("authenticated") and st.session_state.get("user_email"):
        return normalize_email(st.session_state["user_email"])
    return None


def get_current_user_info() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    email = get_authenticated_email()
    if not email or not is_authorized(email):
        return None, None, None
    user = get_user(email)
    role = user.get("role") if user else None
    display = user.get("display_name") if user else email
    return email, role, display


def require_auth() -> Tuple[str, str]:
    """
    Gate principal.

    1. Sanitize URL (page / step / view / sid)
    2. Restaurer la session depuis le jeton opaque `sid` si besoin (survie au F5)
    3. Si session valide → rester sur la page URL (reconciliation/admin)
    4. Sinon → connexion si page protégée ou demandée, sinon accueil
    """
    sanitize_query_params()
    page = get_page()

    # Mémoriser la page demandée pour y revenir après login
    if page in (PAGE_RECONCILIATION, PAGE_ADMINISTRATION):
        st.session_state["return_page"] = page

    # --- Restauration après F5 (session_state vide mais sid encore dans l'URL) ---
    if not (st.session_state.get("authenticated") and st.session_state.get("user_email")):
        _try_restore_from_sid()

    # --- Session authentifiée ---
    if st.session_state.get("authenticated") and st.session_state.get("user_email"):
        email = normalize_email(st.session_state["user_email"])
        user = get_user(email)

        # Utilisateur explicitement désactivé → déconnexion forcée
        if user is not None and not user.get("active", False):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            set_page(PAGE_CONNEXION)
            st.warning("Votre compte a été désactivé. Contactez un administrateur.")
            _render_login_screen()
            st.stop()

        # Utilisateur toujours autorisé (ou registre temporairement indisponible
        # mais session existante : on ne casse pas la navigation)
        if user is None or user.get("active", False):
            role = (user.get("role") if user else None) or st.session_state.get("user_role") or "USER"

            # Restaurer / conserver la page protégée après F5
            if page == PAGE_ADMINISTRATION:
                if role == "ADMIN":
                    set_page(PAGE_ADMINISTRATION, view="admin")
                    st.session_state["app_view"] = "admin"
                else:
                    set_page(PAGE_RECONCILIATION, view="reco")
                    st.session_state["app_view"] = "reco"
            elif page == PAGE_RECONCILIATION:
                set_page(PAGE_RECONCILIATION, step=st.session_state.get("config_step", 0), view="reco")
                st.session_state["app_view"] = "reco"
            elif page in (PAGE_ACCUEIL, PAGE_CONNEXION) or page not in (
                PAGE_RECONCILIATION, PAGE_ADMINISTRATION
            ):
                # Connecté mais URL publique / vide après F5 → rester dans l'app (reco)
                set_page(PAGE_RECONCILIATION, step=0, view="reco")
                st.session_state["app_view"] = "reco"
            else:
                view = st.session_state.get("app_view", "reco")
                if view == "admin" and role == "ADMIN":
                    set_page(PAGE_ADMINISTRATION, view="admin")
                else:
                    set_page(PAGE_RECONCILIATION, step=st.session_state.get("config_step", 0), view="reco")
                    st.session_state["app_view"] = "reco"

            # Garantir que le jeton opaque reste dans l'URL après set_page
            try:
                tok = st.session_state.get("_session_token")
                if tok:
                    set_sid(tok)
                    persist_work_snapshot()
            except Exception:
                pass
            return email, role

    # --- Non authentifié ---
    # Page protégée demandée → connexion (PAS accueil), pour y revenir après login
    if page in (PAGE_RECONCILIATION, PAGE_ADMINISTRATION):
        st.session_state["show_login"] = True
        st.session_state["return_page"] = page
        set_page(PAGE_CONNEXION)
        _render_login_screen()
        st.stop()

    if page == PAGE_CONNEXION or st.session_state.get("show_login"):
        set_page(PAGE_CONNEXION)
        _render_login_screen()
    else:
        set_page(PAGE_ACCUEIL)
        _render_welcome_page()
    st.stop()
    return "", ""


def logout_user() -> None:
    email = st.session_state.get("user_email") or "-"
    audit.logout(email)
    # Invalider la session serveur + jeton URL
    try:
        psess.destroy_session(st.session_state.get("_session_token") or get_sid())
    except Exception:
        pass
    try:
        set_sid(None)
    except Exception:
        pass
    try:
        from utils.data_loader import clear_file_caches
        clear_file_caches()
    except Exception:
        pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    clear_navigation_params()


def _finalize_session(email: str) -> Tuple[str, str]:
    role = get_role(email) or "USER"
    user_rec = get_user(email)
    display_name = (user_rec or {}).get("display_name") or email

    if st.session_state.get("_auth_logged_email") != email:
        audit.login_success(email, method="email_password")
        st.session_state["_auth_logged_email"] = email
        st.session_state["user_email"] = email
        st.session_state["user_role"] = role
        st.session_state["user_display_name"] = display_name
        st.session_state["authenticated"] = True
        st.session_state["show_login"] = False

    # Session serveur opaque (survie au rafraîchissement navigateur)
    try:
        token = st.session_state.get("_session_token")
        if not token or not psess.load_session(token):
            token = psess.create_session(email, role, display_name)
            st.session_state["_session_token"] = token
        set_sid(token)
    except Exception:
        pass

    # Revenir à la page demandée avant login (ex. F5 sur reconciliation)
    ret = st.session_state.pop("return_page", None)
    if ret == PAGE_ADMINISTRATION and role == "ADMIN":
        set_page(PAGE_ADMINISTRATION, view="admin")
        st.session_state["app_view"] = "admin"
    else:
        step = st.session_state.get("config_step", 0)
        set_page(PAGE_RECONCILIATION, step=step, view="reco")
        st.session_state["app_view"] = "reco"
    return email, role


def _try_restore_from_sid() -> bool:
    """
    Restaure authenticated / user_* depuis le jeton opaque `sid` (URL).
    Restaure aussi l'état de travail léger (étape, flags, période).
    Retourne True si restauration réussie.
    """
    token = get_sid() or st.session_state.get("_session_token")
    if not token:
        return False
    data = psess.load_session(token)
    if not data:
        try:
            set_sid(None)
        except Exception:
            pass
        return False

    email = normalize_email(data.get("email") or "")
    if not email or not is_authorized(email):
        psess.destroy_session(token)
        try:
            set_sid(None)
        except Exception:
            pass
        return False

    user = get_user(email)
    if user is not None and not user.get("active", False):
        psess.destroy_session(token)
        try:
            set_sid(None)
        except Exception:
            pass
        return False

    role = (user.get("role") if user else None) or data.get("role") or "USER"
    display = (user.get("display_name") if user else None) or data.get("display_name") or email

    st.session_state["authenticated"] = True
    st.session_state["user_email"] = email
    st.session_state["user_role"] = role
    st.session_state["user_display_name"] = display
    st.session_state["_auth_logged_email"] = email
    st.session_state["_session_token"] = token
    st.session_state["show_login"] = False
    set_sid(token)

    # Après F5 : toujours revenir au chargement des données (pas aux résultats)
    # On restaure uniquement le contexte utile (type/partenaire mémorisés), pas already_processed
    work = data.get("work") or {}
    if isinstance(work, dict):
        for k in ("last_pmt_name", "last_partner_name", "last_reco_type", "last_partner_label"):
            if k in work and work[k] is not None:
                st.session_state[k] = work[k]

    st.session_state["config_step"] = 0
    st.session_state["already_processed"] = False
    st.session_state.pop("pending_run", None)
    st.session_state.pop("excel_report_bytes", None)
    st.session_state.pop("excel_report_name", None)
    st.session_state.pop("excel_report_cache_key", None)
    st.session_state.pop("reco_results", None)

    # Forcer la page réconciliation (jamais connexion si sid valide)
    set_page(PAGE_RECONCILIATION, step=0, view="reco")
    st.session_state["app_view"] = "reco"

    return True


def persist_work_snapshot() -> None:
    """Enregistre un snapshot léger de l'état de réconciliation (appelé depuis main)."""
    token = st.session_state.get("_session_token") or get_sid()
    if not token:
        return
    work = {}
    for k in (
        "config_step",
        "already_processed",
        "saved_reco_start",
        "saved_reco_end",
        "saved_match_col_pmt",
        "saved_match_col_partner",
        "app_view",
        "upload_sig",
        "reco_elapsed_sec",
        "last_pmt_name",
        "last_partner_name",
        "last_reco_type",
        "last_partner_label",
    ):
        if k in st.session_state:
            work[k] = st.session_state[k]
    try:
        psess.save_work_state(token, work)
    except Exception:
        pass


def _render_welcome_page() -> None:
    from styles.custom import render_sidebar_logo

    render_sidebar_logo()
    st.sidebar.markdown("---")
    st.sidebar.info("Bienvenue sur **RecoTrust**")
    st.sidebar.caption("Plateforme de réconciliation des flux partenaires — PayMeTrust")

    st.markdown(
        """
        <div style="max-width:920px;margin:1.5rem auto 0 auto;text-align:center;">
            <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;
                 font-size:2.1rem;font-weight:800;margin-bottom:0.4rem;">
                🛡️ RecoTrust
            </div>
            <p style="color:#4338CA !important;-webkit-text-fill-color:#4338CA !important;
               font-size:1.15rem;font-weight:700;margin-bottom:1.2rem;">
                Application de Réconciliation Revenue Assurance
            </p>
            <p style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;
               font-size:1.05rem;line-height:1.55;max-width:780px;margin:0 auto 1.8rem auto;">
                Le <strong style="color:#0F172A;">Revenue Assurance (RA)</strong> dans une fintech est l'ensemble des processus,
                contrôles et analyses permettant de garantir que <strong style="color:#0F172A;">toutes les transactions sont
                correctement enregistrées, facturées, encaissées et réconciliées</strong>, afin d'éviter
                les pertes financières dues à des erreurs, des anomalies, des fraudes ou des défaillances techniques.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                        border-radius:14px;padding:1.1rem 1rem;min-height:160px;box-shadow:0 4px 16px rgba(15,23,42,0.06);">
                <div style="font-size:1.6rem;margin-bottom:0.4rem;">🔄</div>
                <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;font-weight:800;font-size:1rem;margin-bottom:0.35rem;">Réconciliation</div>
                <div style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;font-size:0.88rem;line-height:1.45;font-weight:500;">
                    Comparer les transactions entre le système interne, les partenaires de paiement
                    (Wave, Orange Money, MTN, Visa, CinetPay…) et les banques.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                        border-radius:14px;padding:1.1rem 1rem;min-height:160px;box-shadow:0 4px 16px rgba(15,23,42,0.06);">
                <div style="font-size:1.6rem;margin-bottom:0.4rem;">🔍</div>
                <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;font-weight:800;font-size:1rem;margin-bottom:0.35rem;">Détection d'anomalies</div>
                <div style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;font-size:0.88rem;line-height:1.45;font-weight:500;">
                    Identifier les transactions manquantes, doublons, écarts de montants,
                    hausses d'échecs ou de remboursements avant qu'ils ne deviennent coûteux.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;
                        border-radius:14px;padding:1.1rem 1rem;min-height:160px;box-shadow:0 4px 16px rgba(15,23,42,0.06);">
                <div style="font-size:1.6rem;margin-bottom:0.4rem;">📊</div>
                <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;font-weight:800;font-size:1rem;margin-bottom:0.35rem;">Reporting &amp; KPIs</div>
                <div style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;font-size:0.88rem;line-height:1.45;font-weight:500;">
                    Tableaux de bord : volumes, chiffre d'affaires, taux opérateur, taux marchand,
                    commissions, pertes, écarts, transactions en attente et taux de réussite.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        if st.button(
            "🔐  Connexion",
            type="primary",
            use_container_width=True,
            key="welcome_go_login",
        ):
            st.session_state["show_login"] = True
            set_page(PAGE_CONNEXION)
            st.rerun()

    st.markdown(
        """
        <div style="text-align:center;margin-top:2rem;color:#64748B !important;-webkit-text-fill-color:#64748B !important;font-size:0.85rem;">
            © 2026 RecoTrust · PayMeTrust · Revenue Assurance
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_login_screen() -> None:
    from styles.custom import render_sidebar_logo

    render_sidebar_logo()
    st.sidebar.markdown("---")
    st.sidebar.info("Connexion réservée aux utilisateurs autorisés")
    if st.sidebar.button("← Retour à l'accueil", use_container_width=True, key="back_welcome"):
        st.session_state["show_login"] = False
        set_page(PAGE_ACCUEIL)
        st.rerun()
    st.sidebar.caption("RecoTrust · PayMeTrust · Revenue Assurance")

    st.markdown(
        """
        <div style="max-width:520px;margin:3rem auto 0 auto;text-align:center;">
            <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;
                 font-size:1.5rem;font-weight:800;margin-bottom:0.5rem;">
                🔐 Connexion RecoTrust
            </div>
            <p style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;
               font-size:1.05rem;line-height:1.5;font-weight:500;">
                Entrez votre adresse e-mail et votre mot de passe pour accéder à l'application.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Adresse e-mail *",
                placeholder="prenom.nom@paymetrust.net",
                key="login_email_input",
                help="Adresse e-mail professionnelle autorisée.",
            )
            password = st.text_input(
                "Mot de passe *",
                type="password",
                placeholder="••••••••",
                key="login_password_input",
                help="Mot de passe fourni par votre administrateur.",
            )
            submitted = st.form_submit_button(
                "Se connecter",
                type="primary",
                use_container_width=True,
            )
            if submitted:
                errors = []
                ok_email, msg_email = validate_email(email, required=True)
                if not ok_email:
                    errors.append(msg_email)
                ok_pwd, msg_pwd = validate_password(
                    password, required=True, check_strength=False
                )
                if not ok_pwd:
                    errors.append(msg_pwd)

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    email_clean = normalize_email(email)
                    if not is_authorized(email_clean):
                        audit.login_failed(email_clean, "email_non_autorise")
                        st.error(
                            "⛔ Accès refusé. Identifiants incorrects ou compte désactivé."
                        )
                    elif not authenticate(email_clean, password):
                        audit.login_failed(email_clean, "mauvais_mot_de_passe")
                        st.error(
                            "⛔ Accès refusé. Identifiants incorrects ou compte désactivé."
                        )
                    else:
                        _finalize_session(email_clean)
                        st.rerun()

        st.caption(
            "Mot de passe oublié ? Contactez un administrateur RecoTrust "
            "pour obtenir un nouveau mot de passe."
        )

    st.markdown(
        """
        <div style="text-align:center;margin-top:3rem;color:#64748B !important;-webkit-text-fill-color:#64748B !important;font-size:0.85rem;">
            © 2026 RecoTrust · PayMeTrust · Revenue Assurance
        </div>
        """,
        unsafe_allow_html=True,
    )
