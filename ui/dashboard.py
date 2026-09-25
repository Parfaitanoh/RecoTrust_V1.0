"""Dashboard / Historique V3 — isolation par utilisateur (ADMIN voit tout)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from ui.components import hero_header, render_kpi_row
from ui.history_store import aggregate_stats, list_runs


def _display_name(email: str) -> str:
    if not email or "@" not in email:
        return email or "utilisateur"
    return email.split("@")[0].replace(".", " ").title()


def _load_runs_for_viewer(
    user_email: str,
    user_role: str = "USER",
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """USER → uniquement ses runs ; ADMIN → tous."""
    role = (user_role or "USER").upper()
    if role == "ADMIN":
        return list_runs(limit=limit)
    return list_runs(limit=limit, user=user_email or "")


def render_dashboard(user_email: str = "", user_role: str = "USER") -> None:
    name = _display_name(user_email)
    is_admin = (user_role or "").upper() == "ADMIN"
    scope = "toutes les instances (vue ADMIN)" if is_admin else "vos réconciliations uniquement"

    hero_header(
        title=f"Welcome back, {name} !",
        subtitle=f"Vue consolidée — {scope}.",
        kicker="RecoTrust · Revenue Assurance",
        tabs=["Overview", "Payment", "Transfer", "Statistics"],
        active_tab="Overview",
    )

    if is_admin:
        st.caption("Mode **ADMIN** : vous voyez les réconciliations de tous les utilisateurs.")
    else:
        st.caption("Vous ne voyez que **vos** réconciliations. L’administrateur voit l’ensemble.")

    runs = _load_runs_for_viewer(user_email, user_role, limit=300)

    st.markdown('<div class="rt-panel"><div class="rt-panel-title">Filtres</div></div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([1.3, 1.2, 1.0, 0.85])
    partners = sorted({r.get("partner") or "—" for r in runs})
    types = sorted({r.get("reco_type") or "—" for r in runs})
    with f1:
        fp = st.selectbox("🏢 Partenaire", ["Tous"] + partners, key="dash_partner")
    with f2:
        ft = st.selectbox("📂 Type", ["Tous"] + types, key="dash_type")
    with f3:
        fs = st.selectbox("📌 Statut", ["Tous", "completed", "failed"], key="dash_status")
    with f4:
        st.markdown("<div style='height:1.55rem'></div>", unsafe_allow_html=True)
        if st.button("Reset filtres", use_container_width=True, key="dash_reset"):
            for k in ("dash_partner", "dash_type", "dash_status"):
                st.session_state.pop(k, None)
            st.rerun()

    # Filtre optionnel par utilisateur (ADMIN seulement)
    fu = "Tous"
    if is_admin:
        users = sorted({r.get("user") or "—" for r in runs})
        fu = st.selectbox("👤 Utilisateur", ["Tous"] + users, key="dash_user")

    filtered = runs
    if fp != "Tous":
        filtered = [r for r in filtered if r.get("partner") == fp]
    if ft != "Tous":
        filtered = [r for r in filtered if r.get("reco_type") == ft]
    if fs != "Tous":
        filtered = [r for r in filtered if r.get("status") == fs]
    if is_admin and fu != "Tous":
        filtered = [r for r in filtered if r.get("user") == fu]
    fstats = aggregate_stats(filtered)

    render_kpi_row(
        [
            ("Réconciliations", f"{fstats['total']:,}", "Sur la sélection", "info", "📊"),
            (
                "Terminées",
                f"{fstats['completed']:,}",
                f"{fstats['success_rate']}% de succès",
                "success",
                "✓",
                "up" if fstats["success_rate"] >= 80 else "",
            ),
            (
                "Échecs",
                f"{fstats['failed']:,}",
                "Nécessitent une action",
                "danger" if fstats["failed"] else "neutral",
                "!",
                "down" if fstats["failed"] else "",
            ),
            (
                "Durée moyenne",
                f"{fstats['avg_duration_sec']}s" if fstats["avg_duration_sec"] is not None else "—",
                "Temps de traitement",
                "neutral",
                "⏱",
            ),
        ]
    )

    st.markdown("")
    left, right = st.columns([1.05, 1.55])
    with left:
        st.markdown('<div class="rt-panel">', unsafe_allow_html=True)
        st.markdown('<div class="rt-panel-title">Répartition</div>', unsafe_allow_html=True)
        render_kpi_row(
            [
                ("Payment", f"{fstats['payin']:,}", "Payin", "info", "↓"),
                ("Transfer", f"{fstats['payout']:,}", "Payout", "info", "↑"),
            ]
        )
        if fstats["top_partners"]:
            st.markdown("")
            st.caption("Top partenaires")
            for name_p, cnt in fstats["top_partners"][:5]:
                pct = int(100 * cnt / max(fstats["total"], 1))
                st.markdown(
                    f"**{name_p}** · {cnt} "
                    f"<span style='color:#94A3B8'>({pct}%)</span>",
                    unsafe_allow_html=True,
                )
                st.progress(min(pct / 100.0, 1.0))
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="rt-panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="rt-panel-title">Transactions History</div>',
            unsafe_allow_html=True,
        )
        if not filtered:
            st.info(
                "Aucune réconciliation enregistrée dans votre périmètre. "
                "Lancez une **Nouvelle réconciliation** pour alimenter le tableau."
            )
        else:
            import pandas as pd

            rows = []
            for r in filtered[:40]:
                st_status = r.get("status", "")
                badge = (
                    "Completed"
                    if st_status == "completed"
                    else ("Failed" if st_status == "failed" else st_status)
                )
                row = {
                    "Name": r.get("partner") or "—",
                    "Type": r.get("reco_type") or "—",
                    "Date": (r.get("ts") or "")[:16].replace("T", " "),
                    "Duration": (
                        f"{r.get('duration_sec')}s"
                        if r.get("duration_sec") is not None
                        else "—"
                    ),
                    "Status": badge,
                    "Ref": r.get("id", ""),
                }
                if is_admin:
                    row["User"] = (r.get("user") or "")[:28]
                rows.append(row)
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                height=min(420, 48 + 36 * len(rows)),
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if fstats["top_partners"] and len(fstats["top_partners"]) > 1:
        st.markdown('<div class="rt-panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="rt-panel-title">Volume par partenaire</div>',
            unsafe_allow_html=True,
        )
        try:
            import pandas as pd
            import plotly.express as px

            pdf = pd.DataFrame(
                fstats["top_partners"], columns=["Partenaire", "Réconciliations"]
            )
            fig = px.bar(
                pdf,
                x="Partenaire",
                y="Réconciliations",
                template="plotly_white",
                color_discrete_sequence=["#6366F1"],
            )
            fig.update_layout(
                height=300,
                margin=dict(l=8, r=8, t=20, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0F172A", size=11),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            pass
        st.markdown("</div>", unsafe_allow_html=True)


def render_history(user_email: str = "", user_role: str = "USER") -> None:
    is_admin = (user_role or "").upper() == "ADMIN"
    hero_header(
        title="Historique",
        subtitle=(
            "Toutes les instances de tous les utilisateurs."
            if is_admin
            else "Vos traitements uniquement."
        ),
        kicker="RecoTrust · History",
        tabs=["All", "Completed", "Failed"],
        active_tab="All",
    )
    if is_admin:
        st.caption("Mode **ADMIN** : historique global.")
    else:
        st.caption("Périmètre restreint à **votre compte**.")

    runs = _load_runs_for_viewer(user_email, user_role, limit=500)

    c1, c2, c3 = st.columns(3)
    with c1:
        q = st.text_input("🔍 Recherche (partenaire, fichier, utilisateur)", key="hist_q")
    with c2:
        partners = sorted({r.get("partner") or "" for r in runs if r.get("partner")})
        fp = st.selectbox("🏢 Partenaire", ["Tous"] + partners, key="hist_partner")
    with c3:
        fs = st.selectbox("📌 Statut", ["Tous", "completed", "failed"], key="hist_status")

    fu = "Tous"
    if is_admin:
        users = sorted({r.get("user") or "" for r in runs if r.get("user")})
        fu = st.selectbox("👤 Utilisateur", ["Tous"] + users, key="hist_user")

    filtered: List[Dict[str, Any]] = []
    ql = (q or "").strip().lower()
    for r in runs:
        if fp != "Tous" and r.get("partner") != fp:
            continue
        if fs != "Tous" and r.get("status") != fs:
            continue
        if is_admin and fu != "Tous" and r.get("user") != fu:
            continue
        if ql:
            blob = " ".join(
                str(r.get(k, ""))
                for k in ("partner", "pmt_file", "partner_file", "user", "id", "reco_type")
            ).lower()
            if ql not in blob:
                continue
        filtered.append(r)

    st.caption(f"{len(filtered)} résultat(s)")
    if not filtered:
        st.info("Aucun élément d'historique dans votre périmètre.")
        return

    import pandas as pd

    st.markdown('<div class="rt-panel">', unsafe_allow_html=True)
    cols_base = {
        "Date (UTC)": lambda r: (r.get("ts") or "")[:19].replace("T", " "),
        "Réf.": lambda r: r.get("id", ""),
        "Partenaire": lambda r: r.get("partner", ""),
        "Type": lambda r: r.get("reco_type", ""),
        "Status": lambda r: (
            "Completed"
            if r.get("status") == "completed"
            else ("Failed" if r.get("status") == "failed" else r.get("status"))
        ),
        "Durée (s)": lambda r: r.get("duration_sec", ""),
        "Matching PMT": lambda r: r.get("match_col_pmt", ""),
        "Matching Part.": lambda r: r.get("match_col_partner", ""),
    }
    rows = []
    for r in filtered[:200]:
        row = {k: fn(r) for k, fn in cols_base.items()}
        if is_admin:
            row["Utilisateur"] = r.get("user", "")
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
