import streamlit as st
from styles.assets_b64 import FOND_B64, LOGO_B64

# Palette logo PayMeTrust
PRIMARY = "#3070F0"
PRIMARY_DARK = "#1A4FC4"
PRIMARY_DEEP = "#0B2A6B"
NAVY = "#061428"
NAVY_SOFT = "#0A1F3D"
ACCENT = "#5B9DFF"
TEXT_ON_DARK = "#0F172A"
TEXT_MUTED = "#334155"
TEXT_DARK = "#0F172A"
# Anciennes valeurs clair-sur-sombre (sidebar / hero uniquement)
TEXT_LIGHT = "#F8FAFC"
TEXT_LIGHT_MUTED = "#E2E8F0"

def load_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
        }}

        /* ===== FOND IMAGE + DÉGRADÉ SOMBRE ===== */
        .stApp {{
            background:
                linear-gradient(
                    165deg,
                    rgba(6, 20, 40, 0.88) 0%,
                    rgba(10, 31, 61, 0.90) 40%,
                    rgba(11, 42, 107, 0.92) 70%,
                    rgba(6, 20, 40, 0.94) 100%
                ),
                url("data:image/jpeg;base64,{FOND_B64}")
                center center / cover no-repeat fixed !important;
        }}
        .main .block-container {{
            padding-top: 0.6rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}
        [data-testid="stAppViewContainer"] > .main {{
            background: transparent !important;
        }}
        [data-testid="stHeader"] {{
            background: rgba(6, 20, 40, 0.75) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(91, 157, 255, 0.15);
        }}

        /* ===== TEXTES LISIBLES SUR FOND SOMBRE ===== */
        .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        .main .stHeading,
        .main [data-testid="stHeadingWithActionElements"] h1,
        .main [data-testid="stHeadingWithActionElements"] h2,
        .main [data-testid="stHeadingWithActionElements"] h3 {{
            color: {TEXT_ON_DARK} !important;
            -webkit-text-fill-color: {TEXT_ON_DARK} !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.35) !important;
        }}
        /* Titres DANS composants clairs */
        .main .rw-title, .main .rw-guide-title, .main .rw-match-title,
        .main .rt-page-title, .main .rt-panel-title, .main .rt-kpi-value {{
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            text-shadow: none !important;
        }}

        /* Texte général sur fond image sombre */
        .main p, .main span, .main li, .main label,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaption"],
        .stCaption,
        div[data-testid="stText"],
        .main [data-testid="stCaptionContainer"] p,
        .main .stCaption,
        section[data-testid="stMain"] [data-testid="stCaption"] {{
            color: {TEXT_MUTED} !important;
            -webkit-text-fill-color: {TEXT_MUTED} !important;
            opacity: 1 !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.25);
        }}
        /* Cartes blanches / panels : texte FONCÉ (surcharge) */
        .main .rt-kpi p, .main .rt-kpi span, .main .rt-kpi div,
        .main .rw-header, .main .rw-header *,
        .main .rw-sum-card, .main .rw-sum-card *,
        .main .rw-guide, .main .rw-guide *,
        .main .rw-match-box, .main .rw-match-box *,
        .main .rw-file, .main .rw-file *,
        .main .rt-panel, .main .rt-panel *,
        .main .rt-stepper, .main .rt-stepper * {{
            text-shadow: none !important;
        }}

        /* Alertes : fond clair pour lisibilité */
        .main [data-testid="stAlert"] {{
            background: rgba(255, 255, 255, 0.95) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(48,112,240,0.3) !important;
        }}
        .main [data-testid="stAlert"] p,
        .main [data-testid="stAlert"] span,
        .main [data-testid="stAlert"] div {{
            color: {TEXT_DARK} !important;
            text-shadow: none !important;
        }}

        .main [data-testid="stExpander"] {{
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
        }}
        .main [data-testid="stExpander"] summary,
        .main [data-testid="stExpander"] summary span,
        .main [data-testid="stExpander"] p {{
            color: {TEXT_DARK} !important;
            -webkit-text-fill-color: {TEXT_DARK} !important;
            opacity: 1 !important;
            text-shadow: none !important;
            font-weight: 700 !important;
        }}

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(175deg, {NAVY} 0%, {NAVY_SOFT} 40%, {PRIMARY_DEEP} 100%) !important;
            border-right: 1px solid rgba(91, 157, 255, 0.18);
        }}
        section[data-testid="stSidebar"] > div {{
            background: transparent !important;
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {{
            color: #ffffff !important;
        }}
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] small,
        section[data-testid="stSidebar"] [data-testid="stCaption"] {{
            color: #A8C8F0 !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stDateInput"] input,
        section[data-testid="stSidebar"] input[type="text"] {{
            background: rgba(255,255,255,0.95) !important;
            color: {TEXT_DARK} !important;
            border: 1px solid rgba(91,157,255,0.45) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stDateInput"] label,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{
            color: #ffffff !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
            background: rgba(48, 112, 240, 0.12) !important;
            border: 1px solid rgba(91, 157, 255, 0.35) !important;
            border-radius: 14px !important;
            padding: 0.55rem !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1.5px dashed rgba(91, 157, 255, 0.45) !important;
            border-radius: 12px !important;
            color: #e8f0ff !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="baseButton-secondary"] {{
            background: rgba(48, 112, 240, 0.35) !important;
            color: #ffffff !important;
            border: 1px solid rgba(91, 157, 255, 0.5) !important;
            border-radius: 10px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] svg {{
            fill: #ffffff !important;
            color: #ffffff !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] label {{
            color: #E2E8F0 !important;
        }}
        /* Exception : pastille fichier chargée = texte foncé */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] p,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] span,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] small,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] label {{
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"],
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] {{
            background: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #94A3B8 !important;
            border-radius: 8px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] span,
        section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] small {{
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            font-weight: 700 !important;
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 6px 18px rgba(48, 112, 240, 0.35) !important;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: linear-gradient(135deg, {ACCENT} 0%, {PRIMARY} 100%) !important;
        }}

        /* ===== HEADER ===== */
        .pmt-header {{
            background: linear-gradient(120deg, rgba(6,20,40,0.95) 0%, rgba(26,79,196,0.90) 55%, rgba(48,112,240,0.85) 100%);
            border: 1px solid rgba(91, 157, 255, 0.4);
            border-radius: 20px;
            padding: 1.4rem 1.8rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(12px);
        }}
        .pmt-header img {{
            width: 72px;
            height: 72px;
            object-fit: contain;
            filter: drop-shadow(0 4px 12px rgba(48,112,240,0.45));
        }}
        .pmt-header-text h1 {{
            margin: 0;
            font-weight: 800;
            font-size: 1.55rem;
            color: #ffffff !important;
            letter-spacing: -0.02em;
            text-shadow: none !important;
        }}
        .pmt-header-text p {{
            margin: 0.25rem 0 0 0;
            color: #C5DCFF !important;
            font-weight: 400;
            font-size: 0.95rem;
        }}
        .pmt-badge {{
            margin-left: auto;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.3);
            color: #fff !important;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.4rem;
            background: rgba(6, 20, 40, 0.55);
            padding: 0.4rem;
            border-radius: 14px;
            border: 1px solid rgba(91, 157, 255, 0.25);
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 10px !important;
            color: {TEXT_MUTED} !important;
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK}) !important;
            color: #ffffff !important;
        }}

        /* Cartes / graphiques / tableaux : fond clair pour le contenu data */
        /* Cartes HTML metric_card — texte NOIR, fond blanc, accent bleu logo */
        .main .pmt-metric-card {{
            background: #FFFFFF !important;
            border: 1px solid rgba(48,112,240,0.18) !important;
            box-shadow: 0 4px 16px rgba(48,112,240,0.12) !important;
        }}
        .main .pmt-metric-card,
        .main .pmt-metric-card h3,
        .main .pmt-metric-card p,
        .main .pmt-metric-card span {{
            color: #000000 !important;
            text-shadow: none !important;
        }}
        .main .pmt-metric-card h3 {{
            color: #000000 !important;
            font-weight: 600 !important;
        }}
        .main .pmt-metric-card p {{
            color: #000000 !important;
            font-weight: 800 !important;
        }}

        /* st.metric natifs — fond blanc, texte NOIR GRAS, hauteur égale */
        div[data-testid="stMetric"] {{
            background: #FFFFFF !important;
            border-radius: 14px !important;
            padding: 0.85rem 1rem 0.75rem 1rem !important;
            border: 1px solid rgba(48,112,240,0.18) !important;
            border-left: 4px solid #3070F0 !important;
            box-shadow: 0 4px 16px rgba(48,112,240,0.12) !important;
            min-height: 120px !important;
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }}
        /* Force NOIR GRAS sur tout le contenu des cartes metric (sauf delta) */
        div[data-testid="stMetric"],
        div[data-testid="stMetric"] * {{
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            text-shadow: none !important;
            opacity: 1 !important;
        }}
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] span {{
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            text-shadow: none !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] > div,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] * {{
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            text-shadow: none !important;
            font-weight: 900 !important;
            font-size: 1.55rem !important;
            opacity: 1 !important;
        }}
        /* Delta : vert (succès) ou rouge (baisse) — pas de bleu */
        div[data-testid="stMetric"] [data-testid="stMetricDelta"],
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] * {{
            color: #166534 !important;
            -webkit-text-fill-color: #166534 !important;
            text-shadow: none !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricDelta"][data-testid="stMetricDelta"] svg {{
            fill: #166534 !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            display: flex !important;
            flex-direction: column !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] > div {{
            flex: 1 1 auto !important;
        }}

        /* Graphiques Rapport — taille harmonisée */
        .stPlotlyChart {{
            background: #FFFFFF;
            border-radius: 16px;
            padding: 0.4rem;
            box-shadow: 0 4px 16px rgba(48,112,240,0.10);
            border: 1px solid rgba(48, 112, 240, 0.12);
            min-height: 320px !important;
            max-height: 340px !important;
        }}
        .stPlotlyChart > div {{
            min-height: 300px !important;
            max-height: 320px !important;
        }}
        [data-testid="stHorizontalBlock"] {{
            align-items: stretch !important;
        }}
        /* Deux colonnes graphiques : largeurs égales */
        [data-testid="stHorizontalBlock"] {{
            align-items: stretch !important;
        }}

        .stDataFrame, [data-testid="stDataFrame"] {{
            border-radius: 14px !important;
            overflow: hidden;
            box-shadow: 0 6px 18px rgba(0,0,0,0.15);
            background: rgba(255,255,255,0.97) !important;
        }}

        .stButton > button {{
            border-radius: 12px;
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK});
            color: white !important;
            border: none;
            font-weight: 600;
            box-shadow: 0 4px 14px rgba(48, 112, 240, 0.3);
        }}
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
        }}

        .main [data-testid="stSpinner"] > div {{
            color: {TEXT_ON_DARK} !important;
        }}

        .pmt-footer {{
            text-align: center;
            padding: 1.5rem;
            color: {TEXT_MUTED} !important;
            font-size: 0.88rem;
            border-top: 1px solid rgba(91, 157, 255, 0.22);
            margin-top: 1rem;
        }}
        .pmt-footer strong, .pmt-footer p {{
            color: {TEXT_MUTED} !important;
        }}

        .sidebar-logo {{
            text-align: center;
            padding: 0.5rem 0 1rem 0;
        }}
        .sidebar-logo img {{
            width: 88px;
            height: 88px;
            object-fit: contain;
            filter: drop-shadow(0 4px 14px rgba(48,112,240,0.55));
        }}
        .sidebar-logo .brand {{
            color: #fff !important;
            font-weight: 700;
            font-size: 0.95rem;
            margin-top: 0.4rem;
            letter-spacing: 0.04em;
        }}

        .main [data-testid="stWidgetLabel"] p,
        .main [data-testid="stWidgetLabel"] span {{
            color: {TEXT_ON_DARK} !important;
        }}
    
        /* ===== FORCE NOIR sur metric cards Vue Globale (spécificité max) ===== */
        section[data-testid="stMain"] .pmt-metric-card,
        section[data-testid="stMain"] div.pmt-metric-card,
        [data-testid="stMarkdownContainer"] .pmt-metric-card,
        [data-testid="stMarkdownContainer"] div.pmt-metric-card {{
            background: #FFFFFF !important;
            color: #000000 !important;
        }}
        section[data-testid="stMain"] .pmt-metric-card h3,
        section[data-testid="stMain"] .pmt-metric-card p,
        section[data-testid="stMain"] .pmt-metric-card span,
        section[data-testid="stMain"] .pmt-metric-card *,
        [data-testid="stMarkdownContainer"] .pmt-metric-card h3,
        [data-testid="stMarkdownContainer"] .pmt-metric-card p,
        [data-testid="stMarkdownContainer"] .pmt-metric-card span,
        [data-testid="stMarkdownContainer"] .pmt-metric-card * {{
            color: #000000 !important;
            text-shadow: none !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #000000 !important;
        }}

    </style>
    """, unsafe_allow_html=True)


def render_header(
    title: str = "RecoTrust",
    subtitle: str = "Plateforme de réconciliation des flux partenaires",
    user_email: str = "",
    user_role: str = "",
    notif_count: int = 0,
):
    """
    En-tête SaaS interactif :
    - gauche : logo + titre
    - droite : cloche cliquable (notifications) + badge + avatar
    """
    display = ""
    if user_email and "@" in user_email:
        display = user_email.split("@")[0].replace(".", " ").title()
    elif user_email:
        display = user_email
    role_label = (user_role or "").strip() or "USER"
    initial = (display[:1] or "U").upper()
    n = int(notif_count or 0)

    # Conteneur visuel
    st.markdown('<div class="rt-topbar rt-topbar-interactive">', unsafe_allow_html=True)
    c_left, c_bell, c_badge, c_user = st.columns([3.2, 0.7, 0.55, 1.35])
    with c_left:
        st.markdown(
            f'<div class="rt-topbar-left">'
            f'<img class="rt-topbar-logo" src="data:image/png;base64,{LOGO_B64}" alt="RecoTrust" />'
            f"<div>"
            f'<div class="rt-topbar-title">{title}</div>'
            f'<div class="rt-topbar-sub">{subtitle}</div>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with c_bell:
        label = f"🔔 {n}" if n else "🔔"
        if st.button(label, key="btn_header_notif", help="Voir les notifications", use_container_width=True):
            st.session_state["show_notifications"] = not st.session_state.get(
                "show_notifications", False
            )
    with c_badge:
        st.markdown(
            '<div class="rt-topbar-badge" style="margin-top:0.35rem;text-align:center;">V1.0</div>',
            unsafe_allow_html=True,
        )
    with c_user:
        if display:
            st.markdown(
                f'<div class="rt-topbar-user" style="border:none;margin-top:0.15rem;">'
                f'<div class="rt-topbar-avatar">{initial}</div>'
                f'<div class="rt-topbar-user-meta">'
                f'<div class="rt-topbar-user-name">{display}</div>'
                f'<div class="rt-topbar-user-role">{role_label}</div>'
                f"</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # Panneau déroulant sous l'en-tête (uniquement si cloche cliquée)
    if st.session_state.get("show_notifications"):
        try:
            from utils.notifications import (
                list_notifications,
                mark_all_read,
                delete_notification,
                clear_all_notifications,
            )
        except Exception:
            list_notifications = lambda *_a, **_k: []
            mark_all_read = lambda *_a, **_k: None
            delete_notification = lambda *_a, **_k: None
            clear_all_notifications = lambda *_a, **_k: None
        notifs = list_notifications(user_email)
        st.markdown(
            '<div class="rt-notif-panel"><div class="rt-notif-panel-title">Notifications</div>',
            unsafe_allow_html=True,
        )
        if not notifs:
            st.caption("Aucune notification pour le moment.")
        else:
            for item in notifs[:12]:
                nid = str(item.get("id") or "")
                icon = (
                    "✅"
                    if item.get("kind") == "success"
                    else ("⚠️" if item.get("kind") == "warning" else "ℹ️")
                )
                c_msg, c_del = st.columns([11, 1])
                with c_msg:
                    st.markdown(
                        f"**{icon} {item.get('title', '')}** — "
                        f"<span style='color:#64748B;font-size:0.85rem;'>"
                        f"{item.get('body', '')} · {item.get('ts', '')}</span>",
                        unsafe_allow_html=True,
                    )
                with c_del:
                    st.markdown('<div class="rt-notif-del">', unsafe_allow_html=True)
                    if st.button(
                        "✕",
                        key=f"del_notif_{nid}",
                        help="Supprimer cette notification",
                        use_container_width=True,
                    ):
                        delete_notification(user_email, nid)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Tout marquer comme lu", key="mark_notifs_read_hdr", use_container_width=True):
                    mark_all_read(user_email)
                    st.rerun()
            with b2:
                if st.button("Tout supprimer", key="clear_all_notifs_hdr", use_container_width=True):
                    clear_all_notifications(user_email)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar_logo():
    st.sidebar.markdown(f"""
    <div class="sidebar-logo">
        <img src="data:image/png;base64,{LOGO_B64}" alt="PayMeTrust" />
        <div class="brand">Paymetrust</div></br>
        <p>Paiement rapide et sécurisé</p>
    </div>
    """, unsafe_allow_html=True)



# ---------------------------------------------------------------------------
# Design system V3.1 — inspiration fintech (header sombre, cartes blanches)
# Couche purement visuelle — aucun impact métier
# ---------------------------------------------------------------------------
_V3_CSS = """
<style>
/* ----- Fond application (zone principale claire) ----- */
[data-testid="stAppViewContainer"] > .main {
  background: #F4F6FB !important;
}
.main .block-container {
  padding-top: 0.6rem !important;
  padding-bottom: 2rem !important;
  max-width: 1200px !important;
}

/* ----- Header bienvenue type Fincan ----- */
.rt-hero {
  background: linear-gradient(135deg, #0B1220 0%, #151E33 55%, #1A2450 100%);
  border-radius: 16px;
  padding: 1.25rem 1.5rem 1rem 1.5rem;
  margin: 0 0 1.15rem 0;
  color: #F8FAFC !important;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
  position: relative;
  overflow: hidden;
}
.rt-hero::after {
  content: "";
  position: absolute;
  right: -40px; top: -40px;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(99,102,241,0.35) 0%, transparent 70%);
  pointer-events: none;
}
.rt-hero-kicker {
  font-size: 0.78rem;
  font-weight: 600;
  color: #A5B4FC !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin: 0 0 0.35rem 0;
}
.rt-hero-title {
  font-size: 1.55rem !important;
  font-weight: 800 !important;
  color: #FFFFFF !important;
  margin: 0 !important;
  letter-spacing: -0.02em;
}
.rt-hero-sub {
  color: #CBD5E1 !important;
  font-size: 0.9rem !important;
  margin: 0.35rem 0 0 0 !important;
}
.rt-hero-tabs {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.9rem;
  flex-wrap: wrap;
}
.rt-hero-tab {
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #94A3B8 !important;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
}
.rt-hero-tab.active {
  color: #FFFFFF !important;
  background: rgba(99,102,241,0.35);
  border-color: rgba(129,140,248,0.5);
}

/* ----- Cartes KPI ----- */
.rt-kpi {
  background: #FFFFFF;
  border: 1px solid #E8ECF4;
  border-radius: 16px;
  padding: 1.05rem 1.15rem;
  min-height: 110px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  position: relative;
}
.rt-kpi-info { border-top: 3px solid #6366F1; }
.rt-kpi-success { border-top: 3px solid #22C55E; }
.rt-kpi-warning { border-top: 3px solid #F59E0B; }
.rt-kpi-danger { border-top: 3px solid #EF4444; }
.rt-kpi-neutral { border-top: 3px solid #94A3B8; }
.rt-kpi-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748B !important;
  margin-bottom: 0.45rem;
}
.rt-kpi-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0F172A !important;
  line-height: 1.15;
  letter-spacing: -0.02em;
}
.rt-kpi-hint {
  font-size: 0.78rem;
  color: #64748B !important;
  margin-top: 0.4rem;
}
.rt-kpi-hint.up { color: #16A34A !important; font-weight: 600; }
.rt-kpi-hint.down { color: #DC2626 !important; font-weight: 600; }
.rt-kpi-icon {
  position: absolute;
  top: 14px; right: 14px;
  width: 34px; height: 34px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  background: #EEF2FF;
}

/* ----- Stepper ----- */
.rt-stepper {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin: 0.25rem 0 1rem 0;
  padding: 12px 14px;
  background: #FFFFFF;
  border: 1px solid #E8ECF4;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(15,23,42,0.03);
}
.rt-step {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94A3B8;
  font-size: 0.82rem;
  font-weight: 600;
}
.rt-step-num {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #E2E8F0;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 800;
}
.rt-step.active { color: #4F46E5; }
.rt-step.active .rt-step-num { background: #6366F1; color: #fff; }
.rt-step.done { color: #15803D; }
.rt-step.done .rt-step-num { background: #22C55E; color: #fff; }
.rt-step-sep {
  width: 20px; height: 2px;
  background: #E2E8F0;
  border-radius: 1px;
}

/* ----- Badges statut ----- */
.rt-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}
.rt-badge-ok { background: #DCFCE7; color: #166534; }
.rt-badge-err { background: #FEE2E2; color: #991B1B; }
.rt-badge-run { background: #E0E7FF; color: #3730A3; }
.rt-badge-muted { background: #F1F5F9; color: #475569; }

/* ----- Panel / carte section ----- */
.rt-panel {
  background: #FFFFFF;
  border: 1px solid #E8ECF4;
  border-radius: 16px;
  padding: 1rem 1.15rem;
  margin: 0.75rem 0 1rem 0;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}
.rt-panel-title {
  font-size: 1rem;
  font-weight: 700;
  color: #0F172A !important;
  margin: 0 0 0.75rem 0;
}

/* ----- Page titles (fallback) ----- */
.rt-page-header { margin: 0 0 0.75rem 0; }
.rt-page-title {
  font-size: 1.4rem !important;
  font-weight: 800 !important;
  color: #0F172A !important;
  margin: 0 !important;
}
.rt-page-sub {
  color: #64748B !important;
  margin: 0.25rem 0 0 0 !important;
  font-size: 0.9rem !important;
}

/* ----- Sidebar fintech ----- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0B1220 0%, #111827 100%) !important;
}
section[data-testid="stSidebar"] {
  color: #E2E8F0;
}
/* Ne PAS forcer la couleur sur les pastilles fichiers (fond clair) */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] .stRadio label {
  color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: rgba(255,255,255,0.04);
  border-radius: 10px;
  padding: 0.35rem 0.5rem !important;
  margin-bottom: 0.25rem;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: rgba(99,102,241,0.28) !important;
  border: 1px solid rgba(129,140,248,0.35);
}

/* Boutons primaires */
.stButton > button[kind="primary"],
.stButton > button {
  border-radius: 10px !important;
}
div[data-testid="stMetric"] {
  background: #FFFFFF !important;
  border: 1px solid #E8ECF4 !important;
  border-radius: 14px !important;
  padding: 0.75rem 1rem !important;
}

/* Dataframes plus soft */
[data-testid="stDataFrame"] {
  border: 1px solid #E8ECF4;
  border-radius: 12px;
  overflow: hidden;
}
</style>
"""



_V3_CONTRAST_CSS = """
<style>
/* ===== CORRECTIFS LISIBILITÉ / CONTRASTE (selectbox, stepper, expanders) ===== */

/* Selectbox / dropdown dans la SIDEBAR : fond clair + texte FONCÉ */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  border-radius: 10px !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] span,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] p,
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
}
/* Labels des widgets sidebar */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] label span {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
  opacity: 1 !important;
  font-weight: 600 !important;
}
/* Placeholder selectbox */
section[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="placeholder"],
section[data-testid="stSidebar"] [data-baseweb="select"] div[aria-disabled="true"] {
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
}

/* Menu déroulant (portal) — texte foncé lisible */
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] li *,
div[data-baseweb="menu"] li,
div[data-baseweb="menu"] li *,
ul[role="listbox"] li,
ul[role="listbox"] li * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
}

/* Stepper : labels toujours bien contrastés */
.rt-stepper {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
}
.rt-step,
.rt-step .rt-step-label {
  color: #334155 !important;
  -webkit-text-fill-color: #334155 !important;
  opacity: 1 !important;
  font-weight: 700 !important;
}
.rt-step.active,
.rt-step.active .rt-step-label {
  color: #3730A3 !important;
  -webkit-text-fill-color: #3730A3 !important;
}
.rt-step.done,
.rt-step.done .rt-step-label {
  color: #166534 !important;
  -webkit-text-fill-color: #166534 !important;
}
.rt-step-num {
  opacity: 1 !important;
}

/* Expanders / titres dans la zone principale : texte FONCÉ */
.main [data-testid="stExpander"],
.main [data-testid="stExpander"] > details,
.main [data-testid="stExpander"] summary,
.main [data-testid="stExpander"] summary span,
.main [data-testid="stExpander"] summary p,
.main [data-testid="stExpander"] summary svg,
.main [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
.main [data-testid="stExpander"] [data-testid="stMarkdownContainer"] span {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
.main [data-testid="stExpander"] {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 12px !important;
}
.main [data-testid="stExpander"] summary {
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

/* Sous-titres / captions zone principale */
.main [data-testid="stCaption"],
.main [data-testid="stCaption"] p,
.main .stCaption {
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
  opacity: 1 !important;
}

/* Titres de section dans le main (éviter texte lavé sur fond clair) */
.main h1, .main h2, .main h3, .main h4,
.main [data-testid="stMarkdownContainer"] h1,
.main [data-testid="stMarkdownContainer"] h2,
.main [data-testid="stMarkdownContainer"] h3 {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
</style>
"""



_V3_UPLOADER_CSS = """
<style>
/* Fichiers uploadés sidebar : pastille claire + texte FONCÉ lisible */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 10px !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] *,
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"],
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] *,
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] span,
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] small,
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] p,
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  text-shadow: none !important;
  font-weight: 600 !important;
}
/* taille fichier un peu plus douce mais lisible */
section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] small {
  color: #334155 !important;
  -webkit-text-fill-color: #334155 !important;
  font-weight: 500 !important;
}
/* zone drop labels */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] section span,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] section p {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
  opacity: 1 !important;
}
/* titres 1 / 2 Fichier */
section[data-testid="stSidebar"] .stMarkdown p strong,
section[data-testid="stSidebar"] .stMarkdown strong {
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
}
</style>
"""




_RW_CSS = """
<style>
/* ===== Reconciliation Workspace — contraste élevé ===== */
.rw-header, .rw-results-banner, .rw-guide, .rw-match-box, .rw-sum-card, .rw-file {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 14px !important;
}
.rw-header, .rw-results-banner {
  padding: 1.1rem 1.25rem !important;
  margin: 0 0 1rem 0 !important;
  box-shadow: 0 2px 10px rgba(15,23,42,0.06) !important;
}
.rw-header-top {
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-start !important;
  gap: 1rem !important;
  flex-wrap: wrap !important;
}
.rw-kicker {
  font-size: 0.75rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: #3730A3 !important;
  -webkit-text-fill-color: #3730A3 !important;
  opacity: 1 !important;
  margin-bottom: 0.3rem !important;
}
.rw-title {
  font-size: 1.35rem !important;
  font-weight: 800 !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  letter-spacing: -0.02em !important;
  line-height: 1.25 !important;
  text-shadow: none !important;
}
.rw-meta {
  margin-top: 0.3rem !important;
  color: #334155 !important;
  -webkit-text-fill-color: #334155 !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  opacity: 1 !important;
}
.rw-status {
  display: inline-flex !important;
  align-items: center !important;
  padding: 0.4rem 0.8rem !important;
  border-radius: 999px !important;
  font-size: 0.8rem !important;
  font-weight: 800 !important;
  opacity: 1 !important;
}
.rw-files {
  display: grid !important;
  grid-template-columns: 1fr 1fr !important;
  gap: 0.65rem !important;
  margin-top: 0.9rem !important;
}
.rw-file {
  background: #F8FAFC !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 12px !important;
  padding: 0.7rem 0.85rem !important;
}
.rw-file-label {
  display: block !important;
  font-size: 0.72rem !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  opacity: 1 !important;
  margin-bottom: 0.25rem !important;
}
.rw-file-name {
  font-size: 0.88rem !important;
  font-weight: 700 !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  word-break: break-all !important;
}
.rw-sum-card {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 12px !important;
  padding: 0.8rem 0.95rem !important;
  margin-bottom: 0.5rem !important;
  min-height: 76px !important;
  box-shadow: 0 1px 4px rgba(15,23,42,0.04) !important;
}
.rw-sum-label {
  font-size: 0.72rem !important;
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  opacity: 1 !important;
  margin-bottom: 0.35rem !important;
}
.rw-sum-value {
  font-size: 0.95rem !important;
  font-weight: 800 !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  word-break: break-word !important;
}
.rw-match-box {
  padding: 1rem 1.15rem !important;
  margin: 0.75rem 0 1rem 0 !important;
}
.rw-match-title {
  font-weight: 800 !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  margin-bottom: 0.75rem !important;
  font-size: 1rem !important;
  opacity: 1 !important;
}
.rw-match-row {
  display: flex !important;
  align-items: center !important;
  gap: 0.75rem !important;
  flex-wrap: wrap !important;
}
.rw-match-col { flex: 1 !important; min-width: 160px !important; }
.rw-match-key {
  font-size: 1.05rem !important;
  font-weight: 800 !important;
  color: #312E81 !important;
  -webkit-text-fill-color: #312E81 !important;
  opacity: 1 !important;
}
.rw-match-arrow {
  font-size: 1.2rem !important;
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
  font-weight: 800 !important;
}
.rw-match-hint {
  margin-top: 0.65rem !important;
  font-size: 0.82rem !important;
  color: #334155 !important;
  -webkit-text-fill-color: #334155 !important;
  font-weight: 600 !important;
  opacity: 1 !important;
}
.rw-guide {
  padding: 1.15rem 1.35rem !important;
  margin-top: 0.75rem !important;
}
.rw-guide-title {
  font-weight: 800 !important;
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  margin-bottom: 0.55rem !important;
  font-size: 1.05rem !important;
  opacity: 1 !important;
}
.rw-guide-list,
.rw-guide-list li {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  margin: 0.25rem 0 0 1.1rem !important;
  line-height: 1.6 !important;
  font-size: 0.95rem !important;
  font-weight: 500 !important;
  opacity: 1 !important;
}
.rw-guide-list strong {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-weight: 800 !important;
}
.rw-metric {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-left: 4px solid #4F46E5 !important;
  border-radius: 14px !important;
  padding: 14px 16px !important;
  min-height: 96px !important;
}
.rw-metric-title {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  font-size: 0.8rem !important;
  font-weight: 700 !important;
  margin-bottom: 6px !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
.rw-metric-value {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-size: 1.35rem !important;
  font-weight: 800 !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
</style>
"""


_ULTIMATE_CONTRAST_CSS = """
<style>
/* ===== Contraste SCOPÉ (pas de forçage global destructeur) ===== */

/* HERO sombre → texte CLAIR */
.rt-hero, .rt-hero * {
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
.rt-hero-kicker { color: #C7D2FE !important; -webkit-text-fill-color: #C7D2FE !important; }
.rt-hero-title { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
.rt-hero-sub { color: #E2E8F0 !important; -webkit-text-fill-color: #E2E8F0 !important; }

/* Cartes blanches / workspace → texte FONCÉ */
.rt-kpi, .rt-kpi * ,
.rw-header, .rw-header *:not(.rw-status),
.rw-results-banner, .rw-results-banner *:not(.rw-status),
.rw-sum-card, .rw-sum-card *,
.rw-guide, .rw-guide *,
.rw-match-box, .rw-match-box *,
.rw-file, .rw-file *,
.rt-panel, .rt-panel *,
.rt-stepper, .rt-stepper * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
.rw-kicker { color: #3730A3 !important; -webkit-text-fill-color: #3730A3 !important; }
.rw-sum-label, .rw-file-label, .rt-kpi-label {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  font-weight: 800 !important;
}
.rw-match-key { color: #312E81 !important; -webkit-text-fill-color: #312E81 !important; }

/* Expanders blancs → texte FONCÉ */
.main [data-testid="stExpander"] {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
  border-radius: 12px !important;
}
.main [data-testid="stExpander"] summary,
.main [data-testid="stExpander"] summary *,
.main [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
.main [data-testid="stExpander"] [data-testid="stMarkdownContainer"] span {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  text-shadow: none !important;
  font-weight: 700 !important;
}

/* Alertes / info boxes Streamlit : texte foncé sur fond clair */
.main [data-testid="stAlert"] p,
.main [data-testid="stAlert"] span,
.main [data-testid="stAlert"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  text-shadow: none !important;
}

/* Dataframes restent lisibles */
.main [data-testid="stDataFrame"] {
  color: #0F172A !important;
}

/* Pastilles fichiers sidebar */
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] {
  background: #FFFFFF !important;
  border: 1px solid #64748B !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] span,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] small,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] p,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  font-weight: 700 !important;
}

/* Selectbox sidebar valeur */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: #FFFFFF !important;
  color: #0F172A !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}
</style>
"""



_PREMIUM_CSS = """
<style>
/* =========================================================
   RecoTrust V3 Premium — direction FinTech
   Sidebar sombre · zone principale claire · composants unifiés
   ========================================================= */

/* Zone principale claire (lisibilité maximale) */
.stApp, [data-testid="stAppViewContainer"] {
  background: #F5F7FB !important;
}
[data-testid="stAppViewContainer"] > .main,
section.main, .main {
  background: #F5F7FB !important;
}
.main .block-container {
  padding-top: 0.6rem !important;
  padding-bottom: 2.5rem !important;
  max-width: 1180px !important;
}

/* Texte par défaut sur fond clair */
.main p, .main span, .main li, .main label,
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] span,
.main [data-testid="stMarkdownContainer"] li,
.main [data-testid="stCaption"],
.main .stCaption,
.main [data-testid="stWidgetLabel"] p,
.main [data-testid="stWidgetLabel"] span {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  text-shadow: none !important;
  opacity: 1 !important;
}
.main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  text-shadow: none !important;
}

/* Header application */
.pmt-header {
  background: linear-gradient(135deg, #312E81 0%, #4338CA 45%, #6366F1 100%) !important;
  border: none !important;
  border-radius: 16px !important;
  box-shadow: 0 10px 28px rgba(67, 56, 202, 0.28) !important;
  padding: 1rem 1.35rem !important;
  margin-bottom: 1.1rem !important;
}
.pmt-header h1, .pmt-header p, .pmt-header * {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  text-shadow: none !important;
}
.pmt-header p { opacity: 0.9 !important; font-weight: 500 !important; }
.pmt-badge {
  background: rgba(255,255,255,0.2) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(255,255,255,0.35) !important;
  font-weight: 700 !important;
}

/* Hero sombre (dashboard welcome) — exception texte clair */
.rt-hero, .rt-hero * {
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  text-shadow: none !important;
}
.rt-hero-kicker { color: #C7D2FE !important; -webkit-text-fill-color: #C7D2FE !important; }
.rt-hero-title { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
.rt-hero-sub { color: #E2E8F0 !important; -webkit-text-fill-color: #E2E8F0 !important; }

/* Panels / cartes */
.rt-panel, .rt-kpi, .rw-header, .rw-results-banner, .rw-guide, .rw-match-box, .rw-sum-card {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 14px !important;
  box-shadow: 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04) !important;
}
.rt-panel { padding: 1.1rem 1.2rem !important; margin-bottom: 1rem !important; }
.rt-panel-title, .rt-page-title {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-weight: 800 !important;
}
.rt-kpi-label { color: #64748B !important; -webkit-text-fill-color: #64748B !important; font-weight: 600 !important; }
.rt-kpi-value { color: #0F172A !important; -webkit-text-fill-color: #0F172A !important; font-weight: 800 !important; }
.rt-kpi-hint { color: #475569 !important; -webkit-text-fill-color: #475569 !important; }

/* Workspace */
.rw-title, .rw-sum-value, .rw-file-name, .rw-guide-title, .rw-match-title {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}
.rw-kicker { color: #4338CA !important; -webkit-text-fill-color: #4338CA !important; }
.rw-meta, .rw-sum-label, .rw-file-label, .rw-match-hint, .rw-guide-list, .rw-guide-list li {
  color: #334155 !important;
  -webkit-text-fill-color: #334155 !important;
}
.rw-match-key { color: #3730A3 !important; -webkit-text-fill-color: #3730A3 !important; }

/* Expanders */
.main [data-testid="stExpander"] {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
}
.main [data-testid="stExpander"] summary,
.main [data-testid="stExpander"] summary * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-weight: 700 !important;
  opacity: 1 !important;
  text-shadow: none !important;
}

/* Tabs */
.main [data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: #EEF2FF !important;
  padding: 0.3rem !important;
  border-radius: 12px !important;
  gap: 0.25rem !important;
}
.main [data-testid="stTabs"] [data-baseweb="tab"] {
  color: #475569 !important;
  border-radius: 9px !important;
  font-weight: 600 !important;
}
.main [data-testid="stTabs"] [aria-selected="true"] {
  background: #FFFFFF !important;
  color: #0F172A !important;
  box-shadow: 0 1px 3px rgba(15,23,42,0.08) !important;
}

/* Inputs main */
.main [data-baseweb="select"] > div,
.main [data-testid="stTextInput"] input,
.main [data-testid="stNumberInput"] input,
.main [data-testid="stDateInput"] input {
  background: #FFFFFF !important;
  color: #0F172A !important;
  border-radius: 10px !important;
}
.main [data-baseweb="select"] span,
.main [data-baseweb="select"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}

/* Alertes */
.main [data-testid="stAlert"] {
  background: #FFFFFF !important;
  border-radius: 12px !important;
  border: 1px solid #E2E8F0 !important;
}
.main [data-testid="stAlert"] * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  text-shadow: none !important;
}

/* Boutons */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 14px rgba(79,70,229,0.28) !important;
}
.stButton > button[kind="secondary"] {
  background: #FFFFFF !important;
  color: #312E81 !important;
  border: 1px solid #C7D2FE !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}
.stDownloadButton > button {
  background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
  color: #FFFFFF !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0B1220 0%, #111827 100%) !important;
  border-right: 1px solid rgba(148,163,184,0.12) !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: #FFFFFF !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] {
  background: #FFFFFF !important;
  border: 1px solid #94A3B8 !important;
  border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] span,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] small,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] p,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderFile"] div {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-weight: 700 !important;
  opacity: 1 !important;
}

/* Stepper */
.rt-stepper {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 12px !important;
  padding: 0.75rem 1rem !important;
  margin-bottom: 1rem !important;
}

/* Dataframe */
.main [data-testid="stDataFrame"] {
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 1px solid #E2E8F0 !important;
}

/* Footer */
.pmt-footer {
  color: #64748B !important;
  border-top: 1px solid #E2E8F0 !important;
}
.pmt-footer strong, .pmt-footer p {
  color: #64748B !important;
}

/* Metric cards legacy */
.rw-metric, .pmt-metric-card {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 14px !important;
}
.rw-metric-title, .pmt-metric-card div:first-child {
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
}
.rw-metric-value, .pmt-metric-card div:last-child {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
}

/* ===== LISIBILITÉ fond clair (hors hero / header) ===== */
section[data-testid="stMain"] p,
section[data-testid="stMain"] span,
section[data-testid="stMain"] li,
section[data-testid="stMain"] label,
section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] p,
section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] span,
section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] li,
section[data-testid="stMain"] [data-testid="stCaption"],
section[data-testid="stMain"] [data-testid="stCaption"] *,
section[data-testid="stMain"] .stCaption,
section[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
section[data-testid="stMain"] [data-testid="stWidgetLabel"] span,
section[data-testid="stMain"] [data-testid="stWidgetLabel"] label {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] h4,
section[data-testid="stMain"] h5,
section[data-testid="stMain"] h6,
section[data-testid="stMain"] [data-testid="stHeadingWithActionElements"] * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  text-shadow: none !important;
  font-weight: 800 !important;
}
section[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
section[data-testid="stMain"] [data-testid="stWidgetLabel"] span {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  font-weight: 700 !important;
}
section[data-testid="stMain"] [data-testid="stAlert"],
section[data-testid="stMain"] [data-testid="stAlert"] * {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  opacity: 1 !important;
  text-shadow: none !important;
}

/* PRIORITÉ MAX — Header violet : texte BLANC */
section[data-testid="stMain"] .pmt-header,
section[data-testid="stMain"] .pmt-header *,
section[data-testid="stMain"] .pmt-header h1,
section[data-testid="stMain"] .pmt-header p,
section[data-testid="stMain"] .pmt-header span,
section[data-testid="stMain"] .pmt-header div {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
section[data-testid="stMain"] .pmt-header p {
  color: #EDE9FE !important;
  -webkit-text-fill-color: #EDE9FE !important;
}

/* PRIORITÉ MAX — Hero sombre : texte CLAIR */
section[data-testid="stMain"] .rt-hero,
section[data-testid="stMain"] .rt-hero *,
section[data-testid="stMain"] .rt-hero h1,
section[data-testid="stMain"] .rt-hero p,
section[data-testid="stMain"] .rt-hero span,
section[data-testid="stMain"] .rt-hero div {
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
section[data-testid="stMain"] .rt-hero .rt-hero-kicker {
  color: #C7D2FE !important;
  -webkit-text-fill-color: #C7D2FE !important;
}
section[data-testid="stMain"] .rt-hero .rt-hero-title {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-size: 1.55rem !important;
  font-weight: 800 !important;
}
section[data-testid="stMain"] .rt-hero .rt-hero-sub {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
}
section[data-testid="stMain"] .rt-hero .rt-hero-tab {
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
}
section[data-testid="stMain"] .rt-hero .rt-hero-tab.active {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}

/* Onglets Streamlit — barre claire + texte foncé lisible */
section[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: #EEF2FF !important;
  border-radius: 12px !important;
  padding: 0.3rem !important;
  gap: 0.25rem !important;
}
section[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab"],
section[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab"] * {
  color: #1E293B !important;
  -webkit-text-fill-color: #1E293B !important;
  font-weight: 600 !important;
  opacity: 1 !important;
}
section[data-testid="stMain"] [data-testid="stTabs"] [aria-selected="true"],
section[data-testid="stMain"] [data-testid="stTabs"] [aria-selected="true"] * {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  background: #3B82F6 !important;
  border-radius: 9px !important;
  font-weight: 700 !important;
}
/* Sidebar : texte clair (fond sombre) */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #F1F5F9 !important;
  -webkit-text-fill-color: #F1F5F9 !important;
  text-shadow: none !important;
}
</style>
"""


_SIDEBAR_NAV_CSS = """
<style>

/* Bouton X rouge — suppression notification (:has pour sibling Streamlit) */
div[data-testid="stVerticalBlock"]:has(.rt-notif-del) .stButton > button,
.rt-notif-del + div .stButton > button,
.rt-notif-del .stButton > button {
  background: #DC2626 !important;
  background-color: #DC2626 !important;
  background-image: none !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 800 !important;
  border: 1px solid #B91C1C !important;
  border-radius: 8px !important;
  min-height: 2rem !important;
  padding: 0.15rem 0.4rem !important;
  box-shadow: none !important;
}
div[data-testid="stVerticalBlock"]:has(.rt-notif-del) .stButton > button:hover,
.rt-notif-del .stButton > button:hover {
  background: #B91C1C !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
div[data-testid="stVerticalBlock"]:has(.rt-notif-del) .stButton > button p,
div[data-testid="stVerticalBlock"]:has(.rt-notif-del) .stButton > button span,
.rt-notif-del .stButton > button p,
.rt-notif-del .stButton > button span {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 800 !important;
}


/* Pastilles multiselect (marchands, etc.) — bleu logo + texte blanc gras */
span[data-baseweb="tag"],
div[data-baseweb="tag"],
[data-baseweb="tag"] {
  background-color: #3B82F6 !important;
  background-image: none !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 700 !important;
  border-radius: 999px !important;
  border: 1px solid #2563EB !important;
}
[data-baseweb="tag"] span,
span[data-baseweb="tag"] span {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 700 !important;
}
/* croix de suppression sur pastille */
[data-baseweb="tag"] svg,
span[data-baseweb="tag"] svg {
  fill: #FFFFFF !important;
  color: #FFFFFF !important;
}


/* ===== Boutons couleur LOGO (#3B82F6) + texte blanc gras ===== */
:root {
  --rt-logo-blue: #3B82F6;
  --rt-logo-blue-dark: #2563EB;
}
section[data-testid="stMain"] .stButton > button,
section[data-testid="stMain"] .stDownloadButton > button,
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stMain"] div[data-testid="stDownloadButton"] button,
section[data-testid="stMain"] .stButton > button[kind="primary"],
section[data-testid="stMain"] .stButton > button[kind="secondary"],
section[data-testid="stMain"] .stButton > button[data-testid="baseButton-primary"],
section[data-testid="stMain"] .stButton > button[data-testid="baseButton-secondary"],
section[data-testid="stMain"] .rt-topbar-interactive .stButton > button {
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
  background-color: #3B82F6 !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 700 !important;
  border: 1px solid #2563EB !important;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
}
section[data-testid="stMain"] .stButton > button:hover,
section[data-testid="stMain"] .stDownloadButton > button:hover,
section[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
section[data-testid="stMain"] .stButton > button p,
section[data-testid="stMain"] .stButton > button span,
section[data-testid="stMain"] .stDownloadButton > button p,
section[data-testid="stMain"] .stDownloadButton > button span,
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 700 !important;
}


/* Texte boutons BLANC lisible */
section[data-testid="stMain"] .stButton > button,
section[data-testid="stMain"] .stDownloadButton > button,
section[data-testid="stSidebar"] .stButton > button {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
section[data-testid="stMain"] .stButton > button[kind="primary"],
section[data-testid="stMain"] .stButton > button[data-testid="baseButton-primary"],
section[data-testid="stMain"] div[data-testid="stDownloadButton"] button {
  background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  border: none !important;
}
section[data-testid="stMain"] .stButton > button[kind="secondary"],
section[data-testid="stMain"] .stButton > button[data-testid="baseButton-secondary"] {
  background: #3B82F6 !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  border: 1px solid #4338CA !important;
}
/* Cloche header : fond indigo + texte blanc */
section[data-testid="stMain"] .rt-topbar-interactive .stButton > button {
  background: #3B82F6 !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  border: 1px solid #4338CA !important;
}


/* ===== Topbar type Dashboard SaaS ===== */
.rt-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #FFFFFF;
  border: 1px solid #E8ECF4;
  border-radius: 16px;
  padding: 0.85rem 1.25rem;
  margin: 0 0 1rem 0;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
}
.rt-topbar-left { display: flex; align-items: center; gap: 0.85rem; min-width: 0; }
.rt-topbar-logo { width: 40px; height: 40px; object-fit: contain; border-radius: 10px; }
.rt-topbar-title {
  color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;
  font-size: 1.2rem; font-weight: 800; margin: 0; line-height: 1.2;
}
.rt-topbar-sub {
  color: #64748B !important; -webkit-text-fill-color: #64748B !important;
  font-size: 0.82rem; font-weight: 500; margin-top: 0.15rem;
}
.rt-topbar-right { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.rt-topbar-search {
  display: flex; align-items: center; gap: 0.45rem;
  background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 999px;
  padding: 0.45rem 0.95rem; min-width: 160px;
}
.rt-topbar-search-icon { color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important; font-size: 1rem; }
.rt-topbar-search-ph { color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important; font-size: 0.85rem; font-weight: 500; }
.rt-topbar-badge {
  background: #EEF2FF; color: #4338CA !important; -webkit-text-fill-color: #4338CA !important;
  border: 1px solid #C7D2FE; border-radius: 999px; padding: 0.3rem 0.7rem;
  font-size: 0.75rem; font-weight: 800;
}
.rt-topbar-user {
  display: flex; align-items: center; gap: 0.55rem;
  padding-left: 0.35rem; border-left: 1px solid #E2E8F0;
}
.rt-topbar-avatar {
  width: 36px; height: 36px; border-radius: 999px;
  background: linear-gradient(135deg, #4F46E5, #6366F1);
  color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.95rem;
}
.rt-topbar-user-name {
  color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;
  font-weight: 700; font-size: 0.88rem; line-height: 1.15;
}
.rt-topbar-user-role {
  color: #64748B !important; -webkit-text-fill-color: #64748B !important;
  font-size: 0.72rem; font-weight: 600;
}
@media (max-width: 900px) {
  .rt-topbar-search { display: none; }
  .rt-topbar-sub { display: none; }
}


/* Réduction espace vide haut de page */
header[data-testid="stHeader"] {
  background: transparent !important;
  height: 2.5rem !important;
}
div[data-testid="stToolbar"] {
  display: none !important;
}
div[data-testid="stDecoration"] {
  display: none !important;
}
.main .block-container {
  padding-top: 0.6rem !important;
  padding-bottom: 1.5rem !important;
}
section[data-testid="stMain"] > div:first-child {
  padding-top: 0 !important;
}

/* ===== Sidebar menu style référence ===== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0B1220 0%, #0F172A 40%, #111827 100%) !important;
  border-right: 1px solid rgba(148,163,184,0.1) !important;
}
section[data-testid="stSidebar"] > div {
  padding-top: 0.75rem !important;
}

/* User chip */
.sb-user {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
  margin: 0.5rem 0 1rem 0;
}
.sb-user-label {
  color: #94A3B8 !important;
  -webkit-text-fill-color: #94A3B8 !important;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.2rem;
}
.sb-user-email {
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  font-weight: 700;
  font-size: 0.82rem;
  word-break: break-all;
}
.sb-user-role {
  color: #A5B4FC !important;
  -webkit-text-fill-color: #A5B4FC !important;
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.25rem;
}
.sb-section-label {
  color: #64748B !important;
  -webkit-text-fill-color: #64748B !important;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0.85rem 0 0.35rem 0.15rem;
  text-transform: uppercase;
}
.sb-spacer { height: 1.25rem; }

/* Radio nav = pills */
section[data-testid="stSidebar"] div[role="radiogroup"] {
  gap: 0.2rem !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: transparent !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.65rem 0.9rem !important;
  margin-bottom: 0.15rem !important;
  transition: background 0.15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: rgba(255,255,255,0.06) !important;
}
/* Masquer le cercle radio */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
  display: none !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p,
section[data-testid="stSidebar"] div[role="radiogroup"] label span,
section[data-testid="stSidebar"] div[role="radiogroup"] label div {
  color: #CBD5E1 !important;
  -webkit-text-fill-color: #CBD5E1 !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  opacity: 1 !important;
}
/* Item actif — pastille indigo */
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: #3B82F6 !important;
  box-shadow: 0 4px 14px rgba(79,70,229,0.35) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p,
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span,
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] div,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span,
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  font-weight: 700 !important;
}

/* Bouton logout */
section[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  color: #E2E8F0 !important;
  border: 1px solid rgba(148,163,184,0.25) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  margin-top: 0.5rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(239,68,68,0.15) !important;
  border-color: rgba(248,113,113,0.45) !important;
  color: #FECACA !important;
}

/* Titres sections sidebar */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #94A3B8 !important;
  -webkit-text-fill-color: #94A3B8 !important;
  font-size: 0.72rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
}
</style>
"""

def load_v3_css() -> None:
    """Design system V3 Premium — FinTech (sidebar dark + main light)."""
    import streamlit as st
    st.markdown(_V3_CSS, unsafe_allow_html=True)
    st.markdown(_V3_CONTRAST_CSS, unsafe_allow_html=True)
    st.markdown(_V3_UPLOADER_CSS, unsafe_allow_html=True)
    st.markdown(_RW_CSS, unsafe_allow_html=True)
    st.markdown(_ULTIMATE_CONTRAST_CSS, unsafe_allow_html=True)
    st.markdown(_PREMIUM_CSS, unsafe_allow_html=True)
    st.markdown(_SIDEBAR_NAV_CSS, unsafe_allow_html=True)
