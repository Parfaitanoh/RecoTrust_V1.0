"""
RecoTrust V1.0 — Application de Réconciliation Revenue Assurance
PayMeTrust

Évolutions V1.0 (production + multi-utilisateurs)
  - Durcissement config.toml (upload 4 Go, headless, showErrorDetails=false)
  - Alignement limite validation upload
  - Requirements pinés
  - Scripts et exemples de déploiement production
  - Optimisation mémoire Streamlit (caches limités, purge uploads obsolètes)
  - Aucune modification des règles métier, processeurs partenaires, calculs ou exports

Évolutions V1.0 :
  - Page d'accueil (Revenue Assurance) héritée de V1.0
  - Authentification e-mail + mot de passe (liste blanche, hash PBKDF2)
  - Rôles USER / ADMIN + écran d'administration avec dashboard
  - Validation centralisée des formulaires
  - Sécurisation des liens navigateur (aucune auth dans l'URL)
  - Journalisation professionnelle des événements de sécurité
  

"""
from __future__ import annotations

import time
import traceback
from datetime import date, timedelta

import streamlit as st

st.set_page_config(
    page_title="RecoTrust — PaymeTrust",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles.custom import load_css, load_v3_css, render_header, render_sidebar_logo
from ui.components import step_indicator, page_header
from ui.dashboard import render_dashboard, render_history
from ui.history_store import append_run
from ui.reco_workspace import (
    workspace_header, match_preview,
    results_banner,
)
from partenaires import get_processor, get_available_partners, RECO_TYPES
from utils.match_config import get_default_match_keys
from auth.session import require_auth, logout_user
from auth import audit
from auth.navigation import (
    PAGE_ADMINISTRATION,
    PAGE_RECONCILIATION,
    get_page,
    restore_step_from_url,
    restore_view_from_url,
    set_page,
    sync_step_to_url,
)
from auth.validators import (
    validate_date_range,
    validate_match_column,
    validate_uploaded_file,
)

load_css()
load_v3_css()

# =============================================================================
# GATE D'AUTHENTIFICATION + AUTORISATION
# =============================================================================
user_email, user_role = require_auth()
# À partir d'ici : utilisateur authentifié ET autorisé

# Restaurer la navigation depuis l'URL (survit au F5)
_url_view = restore_view_from_url()
_url_step = restore_step_from_url()
if _url_view:
    st.session_state["app_view"] = _url_view
if _url_step is not None and "config_step" not in st.session_state:
    st.session_state["config_step"] = _url_step
elif _url_step is not None:
    # L'URL prime pour rester sur la même étape après refresh
    st.session_state["config_step"] = _url_step

# ---------- Sidebar (style menu FinTech) ----------
render_sidebar_logo()
# Navigation principale — labels avec icônes (style référence)
_nav_map = {
    "🏠  Home": "Dashboard",
    "🔄  Réconciliation": "Nouvelle réconciliation",
    "📋  Historique": "Historique",
}
_nav_labels = list(_nav_map.keys())
_nav_default_section = st.session_state.get("nav_section", "Nouvelle réconciliation")
_nav_default_label = next(
    (k for k, v in _nav_map.items() if v == _nav_default_section),
    "🔄  Réconciliation",
)
_nav_label = st.sidebar.radio(
    "nav",
    options=_nav_labels,
    index=_nav_labels.index(_nav_default_label) if _nav_default_label in _nav_labels else 1,
    key="nav_section_radio",
    label_visibility="collapsed",
)
st.session_state["nav_section"] = _nav_map.get(_nav_label, "Nouvelle réconciliation")
_nav = st.session_state["nav_section"]

# Navigation ADMIN
if user_role == "ADMIN":
    st.sidebar.markdown('<div class="sb-section-label">ADMIN</div>', unsafe_allow_html=True)
    _current_view = st.session_state.get("app_view", "reco")
    _admin_labels = ["📊  App métier", "🛡️  Administration"]
    _admin_idx = 1 if _current_view == "admin" else 0
    _admin_label = st.sidebar.radio(
        "admin_nav",
        options=_admin_labels,
        index=_admin_idx,
        key="admin_nav_radio",
        label_visibility="collapsed",
    )
    _new_view = "admin" if "Administration" in _admin_label else "reco"
    if _new_view != st.session_state.get("app_view"):
        st.session_state["app_view"] = _new_view
        if _new_view == "admin":
            set_page(PAGE_ADMINISTRATION, view="admin")
        else:
            set_page(
                PAGE_RECONCILIATION,
                step=st.session_state.get("config_step", 0),
                view="reco",
            )
        st.rerun()
    st.session_state["app_view"] = _new_view
else:
    st.session_state["app_view"] = "reco"
    if get_page() == PAGE_ADMINISTRATION:
        set_page(PAGE_RECONCILIATION, view="reco")

# Si vue Administration → afficher uniquement l'écran admin et stopper
if st.session_state.get("app_view") == "admin" and user_role == "ADMIN":
    set_page(PAGE_ADMINISTRATION, view="admin")
    st.sidebar.markdown("---")
    from utils.notifications import unread_count as _uc_admin
    render_header(
        title="Administration",
        subtitle="Gestion des utilisateurs, accès et journaux d'activité",
        user_email=user_email,
        user_role=user_role,
        notif_count=_uc_admin(user_email),
    )
    from auth.admin_ui import render_admin_page
    render_admin_page(user_email)
    st.stop()
else:
    # S'assurer que l'URL reflète la réconciliation
    if get_page() != PAGE_RECONCILIATION:
        set_page(
            PAGE_RECONCILIATION,
            step=st.session_state.get("config_step", 0),
            view="reco",
        )

st.sidebar.markdown('<div class="sb-spacer"></div>', unsafe_allow_html=True)
if st.sidebar.button("↪  Log out", use_container_width=True, key="logout_btn"):
    logout_user()
    st.rerun()

# ---------- Routes UI V3 (hors admin) ----------
_nav_section = st.session_state.get("nav_section", "Nouvelle réconciliation")

_header_map = {
    "Dashboard": (
        "Dashboard",
        "Vue consolidée de vos réconciliations et indicateurs",
    ),
    "Historique": (
        "Historique",
        "Toutes les instances de réconciliation dans votre périmètre",
    ),
    "Nouvelle réconciliation": (
        "Réconciliation",
        "Configurer, lancer et analyser une réconciliation partenaire",
    ),
}
_ht, _hs = _header_map.get(
    _nav_section,
    ("RecoTrust", "Plateforme de réconciliation des flux partenaires"),
)

from utils.notifications import unread_count

_n_unread = unread_count(user_email)
render_header(
    title=_ht,
    subtitle=_hs,
    user_email=user_email,
    user_role=user_role,
    notif_count=_n_unread,
)

if _nav_section == "Dashboard":
    render_dashboard(user_email, user_role=user_role)
    st.stop()
if _nav_section == "Historique":
    render_history(user_email, user_role=user_role)
    st.stop()

# ---------- Zone principale : paramètres + chargement (plus dans la sidebar) ----------
st.markdown(
    '<div class="rt-panel" style="margin-bottom:0.75rem;">'
    '<div class="rt-panel-title">Paramètres de réconciliation</div>'
    '<div style="color:#64748B;font-size:0.88rem;margin-top:0.15rem;">'
    "Type, partenaire et fichiers sources — formats CSV · XLSX · XLS · limite 4 Go"
    "</div></div>",
    unsafe_allow_html=True,
)

_c_type, _c_part = st.columns(2)
with _c_type:
    reco_type = st.selectbox(
        "Type de réconciliation",
        options=RECO_TYPES,
        index=0,
        key="reco_type_select",
    )
available_partners = get_available_partners(reco_type)
with _c_part:
    if not available_partners:
        st.warning(f"Aucun partenaire configuré pour « {reco_type} ».")
        partner = None
    else:
        partner = st.selectbox(
            "Partenaire",
            options=available_partners,
            index=0,
            key="partner_select",
        )

_u1, _u2 = st.columns(2)
with _u1:
    st.markdown("**1 · Fichier Données PMT**")
    data_file = st.file_uploader(
        "PMT (CSV / Excel / Excel 97-2003)",
        type=["csv", "xlsx", "xls"],
        key="pmt_uploader",
    )
with _u2:
    st.markdown("**2 · Fichier Partenaire**")
    partenaire_file = st.file_uploader(
        "Partenaire (CSV / Excel / Excel 97-2003)",
        type=["csv", "xlsx", "xls"],
        key="partner_uploader",
    )

_file_errors = []
if data_file is not None:
    ok_f, msg_f = validate_uploaded_file(data_file, label="fichier PMT", required=True)
    if not ok_f:
        _file_errors.append(msg_f)
if partenaire_file is not None:
    ok_f, msg_f = validate_uploaded_file(
        partenaire_file, label="fichier Partenaire", required=True
    )
    if not ok_f:
        _file_errors.append(msg_f)

for _err in _file_errors:
    st.error(_err)

files_ready = bool(
    data_file and partenaire_file and partner and not _file_errors
)

# Signature fichiers (sans période / matching)
# ---------------------------------------------------------------------------
# F5 / rafraîchissement navigateur :
#   - Les uploaders Streamlit sont vides (limitation plateforme)
#   - On reste CONNECTÉ (session sid)
#   - On revient TOUJOURS à l'écran de chargement PMT + Partenaire
#   - On n'efface les résultats que dans ce cas (pas de conservation post-F5)
# ---------------------------------------------------------------------------
upload_sig = (
    (data_file.name if data_file else None, data_file.size if data_file else 0),
    (partenaire_file.name if partenaire_file else None, partenaire_file.size if partenaire_file else 0),
    reco_type,
    partner,
)
_files_present = bool(data_file and partenaire_file)
_prev_sig = st.session_state.get("upload_sig")
_prev_had_files = bool(
    _prev_sig
    and isinstance(_prev_sig, tuple)
    and len(_prev_sig) >= 2
    and _prev_sig[0]
    and _prev_sig[0][0]
    and _prev_sig[1]
    and _prev_sig[1][0]
)

if _files_present:
    _real_file_change = (
        _prev_sig is not None
        and _prev_sig != upload_sig
        and _prev_had_files
    )
    if _real_file_change:
        st.session_state["config_step"] = 0
        sync_step_to_url(0)
        st.session_state["already_processed"] = False
        st.session_state.pop("_match_cols_sig", None)
        for _k in [k for k in list(st.session_state.keys()) if str(k).startswith("_match_cols::")]:
            st.session_state.pop(_k, None)
        try:
            from utils.data_loader import prune_stale_file_bytes, release_heavy_session_artifacts
            release_heavy_session_artifacts()
            prune_stale_file_bytes(keep_files=[data_file, partenaire_file])
        except Exception:
            for _k in ("excel_report_bytes", "excel_report_name", "excel_report_cache_key",
                       "reco_results", "reco_elapsed_sec"):
                st.session_state.pop(_k, None)
    st.session_state["upload_sig"] = upload_sig
    st.session_state["last_pmt_name"] = data_file.name
    st.session_state["last_partner_name"] = partenaire_file.name
    st.session_state["last_reco_type"] = reco_type
    st.session_state["last_partner_label"] = partner
else:
    # F5 ou pas encore de fichiers → écran de chargement (rester connecté)
    # Réinitialiser uniquement l'état de progression / résultats, PAS l'auth
    if (
        st.session_state.get("already_processed")
        or st.session_state.get("config_step", 0) > 0
        or st.session_state.get("excel_report_bytes")
        or _prev_had_files
    ):
        st.session_state["config_step"] = 0
        sync_step_to_url(0)
        st.session_state["already_processed"] = False
        st.session_state.pop("pending_run", None)
        st.session_state.pop("_match_cols_sig", None)
        for _k in [k for k in list(st.session_state.keys()) if str(k).startswith("_match_cols::")]:
            st.session_state.pop(_k, None)
        try:
            from utils.data_loader import release_heavy_session_artifacts, prune_stale_file_bytes
            release_heavy_session_artifacts()
            prune_stale_file_bytes(keep_files=None)
        except Exception:
            for _k in ("excel_report_bytes", "excel_report_name", "excel_report_cache_key",
                       "reco_results", "reco_elapsed_sec"):
                st.session_state.pop(_k, None)

# Snapshot auth/travail léger (sans forcer already_processed=True après F5)
try:
    from auth.session import persist_work_snapshot
    persist_work_snapshot()
except Exception:
    pass

if not files_ready:
    # Espace de travail : uniquement paramètres + uploads (déjà affichés ci-dessus)
    st.stop()

# Pré-chargement mémoire dès que les fichiers sont présents (+ purge des anciens uploads)
try:
    from utils.data_loader import materialize_upload, load_dataframe, prune_stale_file_bytes
    if data_file is not None:
        materialize_upload(data_file)
        audit.file_uploaded(user_email, data_file.name, getattr(data_file, "size", 0) or 0, "PMT")
    if partenaire_file is not None:
        materialize_upload(partenaire_file)
        audit.file_uploaded(user_email, partenaire_file.name, getattr(partenaire_file, "size", 0) or 0, "PARTENAIRE")
    # Ne conserver en session que les bytes des deux fichiers actifs
    prune_stale_file_bytes(keep_files=[data_file, partenaire_file])
except Exception:
    pass

# ---------- Corps : étape 1 = résumé + Suivant ----------
config_step = st.session_state.get("config_step", 0)

# Workflow guidé (présentation uniquement)
step_indicator(
    0 if config_step < 1 else (1 if not st.session_state.get("already_processed") else 2),
    ["Fichiers", "Configuration & matching", "Résultats"],
)

if config_step < 1:
    workspace_header(
        partner=partner or "—",
        reco_type=reco_type,
        status="ready",
        pmt_name=getattr(data_file, "name", "") or "",
        partner_name=getattr(partenaire_file, "name", "") or "",
        user_email=user_email,
    )
    st.success(f"Fichiers prêts — **{reco_type}** / **{partner}**")
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        if st.button("Continuer → Configuration", type="primary", use_container_width=True, key="btn_suivant"):
            # Pré-chargement des en-têtes (colonnes matching) avant l'écran config
            try:
                from utils.data_loader import get_file_columns

                _ck = f"_match_cols::{upload_sig}"
                st.session_state[_ck] = (
                    get_file_columns(data_file),
                    get_file_columns(partenaire_file),
                )
                st.session_state["_match_cols_sig"] = upload_sig
            except Exception:
                pass
            st.session_state["config_step"] = 1
            sync_step_to_url(1)
            st.rerun()
    st.caption("Étape suivante : période de réconciliation + colonnes de matching + lancement.")
    st.stop()

# ---------- Corps : étape 2 = config OU résultats ----------
already = st.session_state.get("already_processed", False)
_today = date.today()
_default_start = _today - timedelta(days=1)
_default_pmt, _default_partner = get_default_match_keys(reco_type, partner or "")

def _idx(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0

def _fmt_d(d):
    return d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)

# ------------------------------------------------------------------
# MODE RÉSULTATS : config entièrement masquée
# ------------------------------------------------------------------
if already:
    reco_start = st.session_state.get("saved_reco_start", _default_start)
    reco_end = st.session_state.get("saved_reco_end", _today)
    match_col_pmt = st.session_state.get("saved_match_col_pmt", _default_pmt)
    match_col_partner = st.session_state.get("saved_match_col_partner", _default_partner)
    range_ok = True
    run_btn = False

    results_banner(
        partner=partner or "—",
        reco_type=reco_type,
        duration_sec=st.session_state.get("reco_elapsed_sec"),
        match_pmt=match_col_pmt or "",
        match_partner=match_col_partner or "",
    )
    col_r1, col_r2, col_r3 = st.columns([1, 1.2, 1])
    with col_r2:
        if st.button("🔄 Relancer / Modifier la configuration", type="secondary", use_container_width=True, key="rerun_btn"):
            st.session_state["already_processed"] = False
            st.session_state.pop("pending_run", None)
            st.session_state.pop("excel_report_bytes", None)
            st.session_state.pop("excel_report_name", None)
            st.session_state.pop("excel_report_cache_key", None)
            st.session_state.pop("reco_results", None)
            st.session_state.pop("reco_elapsed_sec", None)
            st.rerun()

# ------------------------------------------------------------------
# MODE CONFIG : visible uniquement AVANT le lancement
# ------------------------------------------------------------------
else:
    workspace_header(
        partner=partner or "—",
        reco_type=reco_type,
        status="config",
        pmt_name=getattr(data_file, "name", "") or "",
        partner_name=getattr(partenaire_file, "name", "") or "",
        user_email=user_email,
    )
    st.markdown("#### Période de réconciliation")
    # Date début | Date fin | Plage — même niveau (3 colonnes égales)
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        reco_start = st.date_input(
            "Date début",
            value=st.session_state.get("saved_reco_start", _default_start),
            key="reco_start_input",
        )
    with col_d2:
        reco_end = st.date_input(
            "Date fin",
            value=st.session_state.get("saved_reco_end", _today),
            key="reco_end_input",
        )
    with col_d3:
        # Label invisible pour aligner verticalement avec les date_input
        st.markdown(
            "<div style='font-size:0.875rem;margin-bottom:0.25rem;opacity:0;'>Plage</div>",
            unsafe_allow_html=True,
        )
        ok_range, msg_range = validate_date_range(reco_start, reco_end)
        if not ok_range:
            st.error(msg_range)
            range_ok = False
        else:
            range_ok = True
            st.info(f"Plage : {_fmt_d(reco_start)} → {_fmt_d(reco_end)}")

    # Colonnes de matching : lecture en-têtes uniquement + cache session (pas de full load)
    _cols_cache_key = f"_match_cols::{upload_sig}"
    if (
        _cols_cache_key not in st.session_state
        or st.session_state.get("_match_cols_sig") != upload_sig
    ):
        try:
            from utils.data_loader import get_file_columns

            _cols_pmt = get_file_columns(data_file)
            _cols_part = get_file_columns(partenaire_file)
        except Exception:
            _cols_pmt, _cols_part = [], []
        st.session_state[_cols_cache_key] = (_cols_pmt, _cols_part)
        st.session_state["_match_cols_sig"] = upload_sig
    else:
        _cols_pmt, _cols_part = st.session_state[_cols_cache_key]

    _pmt_std = [
        "Transaction ID", "ID Opérateur", "External Transaction Id",
        "transaction_id", "id_operator", "external_transaction_id",
    ]
    _opts_pmt = list(dict.fromkeys(
        ([_default_pmt] if _default_pmt else []) + _pmt_std + list(_cols_pmt or [])
    ))
    _opts_part = list(dict.fromkeys(
        ([_default_partner] if _default_partner else []) + list(_cols_part or [])
    ))

    _prev_pmt = st.session_state.get("saved_match_col_pmt", _default_pmt)
    _prev_part = st.session_state.get("saved_match_col_partner", _default_partner)

    st.markdown("#### Colonnes de matching")
    st.caption(
        f"Défaut historique : **{_default_pmt}** ↔ **{_default_partner}**. "
        "Les colonnes PMT sont conservées telles quelles (V1.2.0) — choisissez la clé réellement présente dans le fichier."
    )
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        match_col_pmt = st.selectbox(
            "Colonne matching — Paymetrust (PMT)",
            options=_opts_pmt if _opts_pmt else [_default_pmt],
            index=_idx(_opts_pmt if _opts_pmt else [_default_pmt], _prev_pmt),
            key="match_col_pmt_select",
            help="Clé côté fichier PMT (défaut = comportement historique V1.0).",
        )
    with col_m2:
        match_col_partner = st.selectbox(
            "Colonne matching — Partenaire",
            options=_opts_part if _opts_part else [_default_partner],
            index=_idx(_opts_part if _opts_part else [_default_partner], _prev_part),
            key="match_col_partner_select",
            help="Clé côté fichier partenaire (défaut = comportement historique V1.0).",
        )

    match_preview(
        match_col_pmt,
        match_col_partner,
        default_pmt=_default_pmt,
        default_partner=_default_partner,
    )

    file_sig = (
        upload_sig,
        str(reco_start),
        str(reco_end),
        match_col_pmt,
        match_col_partner,
    )
    if st.session_state.get("file_sig") != file_sig:
        st.session_state["file_sig"] = file_sig
        st.session_state.pop("excel_report_bytes", None)
        st.session_state.pop("excel_report_name", None)
        st.session_state.pop("excel_report_cache_key", None)
        st.session_state.pop("reco_results", None)
        st.session_state.pop("reco_elapsed_sec", None)

    # Validation colonnes de matching
    ok_m1, msg_m1 = validate_match_column(match_col_pmt, "colonne PMT")
    ok_m2, msg_m2 = validate_match_column(match_col_partner, "colonne Partenaire")
    match_ok = ok_m1 and ok_m2
    if not ok_m1:
        st.error(msg_m1)
    if not ok_m2:
        st.error(msg_m2)

    if not range_ok or not match_ok:
        st.warning(
            "Corrigez les erreurs de configuration (période et/ou colonnes de matching) "
            "avant de lancer la réconciliation."
        )
        st.stop()

    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns([1, 1.4, 1])
    with col_b1:
        if st.button("⬅️ Retour", use_container_width=True, key="btn_retour"):
            st.session_state["config_step"] = 0
            st.session_state["already_processed"] = False
            sync_step_to_url(0)
            st.rerun()
    with col_b2:
        run_btn = st.button(
            "🚀 Lancer la réconciliation",
            type="primary",
            use_container_width=True,
            key="run_main",
        )


def _format_duration(seconds: float) -> str:
    """Formate une durée en secondes en texte lisible."""
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes} min {secs:.0f} s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours} h {minutes} min {secs:.0f} s"


def _run_processor():
    processor = get_processor(
        reco_type=reco_type,
        partner=partner,
        data_file=data_file,
        partner_file=partenaire_file,
        reco_start=reco_start,
        reco_end=reco_end,
        match_col_pmt=match_col_pmt,
        match_col_partner=match_col_partner,
    )
    processor.process()


def _run_with_progress():
    """Exécute le processeur avec barre de progression et mesure du temps."""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    timer_placeholder = st.empty()

    progress_bar = progress_placeholder.progress(0, text="Initialisation…")
    status_placeholder.info(
        f"🔄 Traitement en cours… (**{reco_type}** / **{partner}**) — "
        f"Période : {reco_start.strftime('%d/%m/%Y')} → {reco_end.strftime('%d/%m/%Y')}"
    )

    t0 = time.perf_counter()
    # Étapes visuelles légères (sans sleep artificiel → plus rapide)
    progress_bar.progress(15, text="Chargement des fichiers (cache)…")
    progress_bar.progress(35, text="Préparation des données…")
    progress_bar.progress(55, text="Réconciliation en cours…")

    audit.reconciliation_started(user_email, reco_type, partner or "")

    try:
        _run_processor()
        elapsed = time.perf_counter() - t0
        st.session_state["reco_elapsed_sec"] = elapsed
        progress_bar.progress(100, text="Réconciliation terminée")
        status_placeholder.success(
            f"✅ Réconciliation terminée en **{_format_duration(elapsed)}** "
            f"({reco_type} / {partner})"
        )
        timer_placeholder.caption(
            f"⏱️ Temps de traitement : {_format_duration(elapsed)} — Utilisateur : {user_email}"
        )
        audit.reconciliation_completed(user_email, reco_type, partner or "", elapsed)
        try:
            from utils.notifications import push_notification
            push_notification(
                user_email,
                title=f"Réconciliation terminée — {partner or reco_type}",
                body=f"{reco_type} · durée {_format_duration(elapsed)}",
                kind="success",
            )
        except Exception:
            pass
        try:
            append_run(
                user=user_email,
                reco_type=reco_type,
                partner=partner or "",
                status="completed",
                duration_sec=elapsed,
                pmt_file=getattr(data_file, "name", "") or "",
                partner_file=getattr(partenaire_file, "name", "") or "",
                match_col_pmt=str(st.session_state.get("saved_match_col_pmt") or ""),
                match_col_partner=str(st.session_state.get("saved_match_col_partner") or ""),
                reco_start=str(st.session_state.get("saved_reco_start") or ""),
                reco_end=str(st.session_state.get("saved_reco_end") or ""),
            )
        except Exception:
            pass
        return True
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        st.session_state["reco_elapsed_sec"] = elapsed
        progress_bar.progress(100, text="Erreur durant le traitement")
        status_placeholder.empty()
        timer_placeholder.caption(
            f"⏱️ Arrêt après {_format_duration(elapsed)}"
        )
        audit.reconciliation_failed(user_email, reco_type, partner or "", str(exc))
        try:
            from utils.notifications import push_notification
            push_notification(
                user_email,
                title=f"Échec réconciliation — {partner or reco_type}",
                body=str(exc)[:180],
                kind="warning",
            )
        except Exception:
            pass
        try:
            append_run(
                user=user_email,
                reco_type=reco_type,
                partner=partner or "",
                status="failed",
                pmt_file=getattr(data_file, "name", "") or "",
                partner_file=getattr(partenaire_file, "name", "") or "",
                error=str(exc)[:200],
            )
        except Exception:
            pass
        raise


if run_btn:
    # Enregistrer la config puis rerun immédiat → la config disparaît avant le traitement
    st.session_state["already_processed"] = True
    st.session_state["pending_run"] = True
    sync_step_to_url(1)
    st.session_state["saved_reco_start"] = reco_start
    st.session_state["saved_reco_end"] = reco_end
    st.session_state["saved_match_col_pmt"] = match_col_pmt
    st.session_state["saved_match_col_partner"] = match_col_partner
    st.session_state.pop("excel_report_bytes", None)
    st.session_state.pop("excel_report_name", None)
    st.session_state.pop("excel_report_cache_key", None)
    st.session_state.pop("reco_elapsed_sec", None)
    st.rerun()

elif already:
    # Premier passage après clic Lancer → traitement avec barre de progression
    if st.session_state.pop("pending_run", False):
        try:
            _run_with_progress()
        except ValueError as e:
            st.error(f"❌ Configuration non reconnue : {e}")
            st.info(
                "Vérifiez que le couple **Type de réconciliation + Partenaire** "
                "est bien supporté par l'application."
            )
            st.session_state["already_processed"] = False
        except KeyError as e:
            col = e.args[0] if e.args else e
            st.error(
                f"❌ Erreur de traitement : colonne introuvable **{col}**.\n\n"
                "Causes fréquentes :\n"
                "- la colonne de matching choisie n'existe pas dans le fichier filtré ;\n"
                "- le processeur partenaire attend encore une colonne historique.\n\n"
                "Action : vérifiez les colonnes sélectionnées (matching PMT / Partenaire) "
                "ou revenez aux colonnes par défaut."
            )
            if user_role == "ADMIN":
                with st.expander("Détails techniques (ADMIN)"):
                    st.code(traceback.format_exc())
            st.session_state["already_processed"] = False
        except Exception as e:
            # Message utilisateur propre (pas de stack trace complète)
            st.error(f"❌ Erreur de traitement : {e}")
            # Détails techniques uniquement pour les ADMIN
            if user_role == "ADMIN":
                with st.expander("Détails techniques (ADMIN)"):
                    st.code(traceback.format_exc())
            st.session_state["already_processed"] = False
    else:
        # Rechargement / navigation : rejouer le processeur (cache fichiers)
        elapsed = st.session_state.get("reco_elapsed_sec")
        if elapsed is not None:
            st.caption(
                f"⏱️ Dernière réconciliation : **{_format_duration(elapsed)}** — "
                f"Utilisateur : {user_email} · *rechargement accéléré (cache fichiers)*"
            )
        try:
            _run_processor()
        except Exception as e:
            st.error(f"❌ Erreur de traitement : {e}")
            if user_role == "ADMIN":
                with st.expander("Détails techniques (ADMIN)"):
                    st.code(traceback.format_exc())
            st.session_state["already_processed"] = False

st.markdown("---")
st.markdown(f"""
<div class="pmt-footer">
    <p><strong>RecoTrust V3.0</strong> · Réconciliation Revenue Assurance · PayMeTrust</p>
    <p>© 2026 RecoTrust / PayMeTrust. Tous droits réservés.</p>
    <p style="font-size: 0.8rem; margin-top: 8px;">
        Support : revenu.assurance@paymetrust.net
        {" · Connecté : <strong>" + user_email + "</strong> (" + user_role + ")" if user_email else ""}
    </p>
</div>
""", unsafe_allow_html=True)
