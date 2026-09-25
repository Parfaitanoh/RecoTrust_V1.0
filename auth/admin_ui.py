"""
RecoTrust V3.0 — Écran d'administration professionnel (rôle ADMIN).

- Dashboard KPI + visualisations
- Gestion utilisateurs (CRUD, rôles, activation)
- Génération / réinitialisation des mots de passe
- Consultation des journaux d'activité
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False

from auth.users import (
    VALID_ROLES,
    add_user,
    count_admins,
    disable_user,
    enable_user,
    generate_password,
    get_stats,
    list_all_users,
    normalize_email,
    remove_user,
    set_password,
    update_user,
)
from auth.validators import (
    password_strength_hint,
    validate_display_name,
    validate_email,
    validate_password,
    validate_role,
)
from auth import audit


def render_admin_page(current_user_email: str) -> None:
    """Point d'entrée de l'écran d'administration."""
    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                    padding:1.1rem 1.4rem;margin-bottom:1.2rem;
                    box-shadow:0 4px 16px rgba(15,23,42,0.05);">
            <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;
                 font-weight:800;font-size:1.25rem;">
                🛡️ Administration RecoTrust
            </div>
            <div style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;
                 font-size:0.92rem;margin-top:0.3rem;font-weight:600;">
                Tableau de bord · Gestion des utilisateurs · Mots de passe · Journaux d'activité
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_dash, tab_users, tab_audit = st.tabs(
        ["📊 Tableau de bord", "👥 Utilisateurs", "📋 Journaux"]
    )

    with tab_dash:
        _render_dashboard()

    with tab_users:
        _render_users_tab(current_user_email)

    with tab_audit:
        _render_audit_tab()


# =============================================================================
# DASHBOARD
# =============================================================================
def _render_dashboard() -> None:
    stats = get_stats()
    users = list_all_users()

    # --- KPI cards ---
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Utilisateurs", stats["total"])
    with c2:
        st.metric("Actifs", stats["active"])
    with c3:
        st.metric("Désactivés", stats["disabled"])
    with c4:
        st.metric("Administrateurs", stats["admins"])
    with c5:
        st.metric("Utilisateurs (USER)", stats["users"])

    st.markdown("<br/>", unsafe_allow_html=True)

    if not users:
        st.info("Aucun utilisateur dans le registre.")
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Répartition par rôle")
        if _HAS_PLOTLY:
            role_counts = {"ADMIN": 0, "USER": 0}
            for rec in users.values():
                if rec.get("active"):
                    r = rec.get("role", "USER")
                    role_counts[r] = role_counts.get(r, 0) + 1
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(role_counts.keys()),
                        values=list(role_counts.values()),
                        hole=0.45,
                        marker=dict(colors=["#023e8a", "#48cae4"]),
                        textinfo="label+value+percent",
                    )
                ]
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E8EEF5"),
                showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(
                f"ADMIN actifs : **{stats['admins']}** · "
                f"USER actifs : **{stats['users']}**"
            )

    with col_right:
        st.subheader("Statut des comptes")
        if _HAS_PLOTLY:
            status_counts = {
                "Actifs": stats["active"],
                "Désactivés": stats["disabled"],
            }
            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=list(status_counts.keys()),
                        y=list(status_counts.values()),
                        marker_color=["#2a9d8f", "#e76f51"],
                        text=list(status_counts.values()),
                        textposition="auto",
                    )
                ]
            )
            fig2.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E8EEF5"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write(
                f"Actifs : **{stats['active']}** · "
                f"Désactivés : **{stats['disabled']}**"
            )

    st.markdown("---")
    st.subheader("Synthèse des comptes")
    rows = []
    for email, rec in sorted(users.items()):
        rows.append(
            {
                "Email": email,
                "Nom": rec.get("display_name", ""),
                "Rôle": rec.get("role", "USER"),
                "Statut": "Actif" if rec.get("active") else "Désactivé",
                "Mot de passe": "Défini" if rec.get("password_hash") else "Non défini",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


# =============================================================================
# UTILISATEURS
# =============================================================================
def _render_users_tab(current_user_email: str) -> None:
    users = list_all_users()

    # ----- Ajouter -----
    with st.expander("➕ Ajouter un utilisateur", expanded=False):
        with st.form("form_add_user", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_email = st.text_input(
                    "Adresse e-mail *",
                    placeholder="prenom.nom@paymetrust.net",
                )
                new_role = st.selectbox("Rôle", options=list(VALID_ROLES), index=0)
            with col2:
                new_name = st.text_input("Nom affiché", placeholder="Prénom Nom")
                gen_pwd = st.checkbox(
                    "Générer un mot de passe automatiquement",
                    value=True,
                    help="Si décoché, vous pourrez saisir un mot de passe manuellement.",
                )
            custom_pwd = ""
            if not gen_pwd:
                custom_pwd = st.text_input(
                    "Mot de passe personnalisé",
                    type="password",
                    help="Minimum 8 caractères recommandé.",
                )
            submitted = st.form_submit_button(
                "Créer l'utilisateur", type="primary", use_container_width=True
            )

            if submitted:
                errors = []
                email_clean = normalize_email(new_email)

                ok_e, msg_e = validate_email(email_clean, required=True)
                if not ok_e:
                    errors.append(msg_e)
                elif email_clean in users:
                    errors.append(f"L'utilisateur « {email_clean} » existe déjà.")

                ok_r, msg_r = validate_role(new_role)
                if not ok_r:
                    errors.append(msg_r)

                ok_n, msg_n = validate_display_name(new_name or "", required=False)
                if not ok_n:
                    errors.append(msg_n)

                pwd_arg = None
                if not gen_pwd:
                    ok_p, msg_p = validate_password(
                        custom_pwd, required=True, check_strength=True
                    )
                    if not ok_p:
                        errors.append(msg_p)
                    else:
                        pwd_arg = custom_pwd

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    plain = add_user(
                        email_clean,
                        role=new_role,
                        display_name=new_name or "",
                        password=pwd_arg,
                    )
                    if plain:
                        audit.log_event(
                            "USER_ADDED",
                            user=current_user_email,
                            details={"target": email_clean, "role": new_role},
                        )
                        st.success(
                            f"Utilisateur **{email_clean}** créé (rôle {new_role})."
                        )
                        st.warning(
                            "⚠️ **Communiquez ce mot de passe à l'utilisateur "
                            "(il ne sera plus affiché) :**"
                        )
                        st.code(plain, language=None)
                        st.session_state["_last_generated_pwd"] = {
                            "email": email_clean,
                            "pwd": plain,
                        }
                    else:
                        st.error(
                            "Échec de la création. Vérifiez les droits "
                            "d'écriture du dossier `data/`."
                        )

    # Afficher le dernier mdp généré si encore en session (après rerun partiel)
    last = st.session_state.get("_last_generated_pwd")
    if last:
        st.info(
            f"Dernier mot de passe généré pour **{last['email']}** "
            f"(copiez-le maintenant si besoin) :"
        )
        st.code(last["pwd"], language=None)
        if st.button("Masquer ce mot de passe", key="hide_last_pwd"):
            st.session_state.pop("_last_generated_pwd", None)
            st.rerun()

    st.markdown("---")
    st.subheader("Gestion des comptes existants")

    if not users:
        st.info("Aucun utilisateur.")
        return

    emails = sorted(users.keys())
    target = st.selectbox(
        "Sélectionner un utilisateur",
        options=emails,
        format_func=lambda e: (
            f"{e}  ·  {users[e].get('role')}  ·  "
            f"{'✅ Actif' if users[e].get('active') else '⛔ Désactivé'}"
        ),
        key="admin_target_user",
    )
    if not target:
        return

    rec = users[target]
    is_self = normalize_email(target) == normalize_email(current_user_email)
    is_last_admin = (
        rec.get("role") == "ADMIN"
        and rec.get("active")
        and count_admins(active_only=True) <= 1
    )

    # Infos compte
    st.markdown(
        f"""
        <div style="background:rgba(48,112,240,0.10);border:1px solid rgba(91,157,255,0.28);
                    border-radius:10px;padding:0.85rem 1rem;margin:0.5rem 0 1rem 0;">
            <div style="color:#0F172A !important;-webkit-text-fill-color:#0F172A !important;font-weight:800;">{rec.get('display_name') or target}</div>
            <div style="color:#334155 !important;-webkit-text-fill-color:#334155 !important;font-size:0.88rem;margin-top:0.2rem;font-weight:600;">
                {target} &nbsp;·&nbsp; Rôle : <strong>{rec.get('role')}</strong>
                &nbsp;·&nbsp; {'✅ Actif' if rec.get('active') else '⛔ Désactivé'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Actions principales
    a1, a2, a3, a4 = st.columns(4)

    with a1:
        if rec.get("active"):
            if st.button(
                "⛔ Désactiver",
                use_container_width=True,
                disabled=is_self or is_last_admin,
                key="btn_disable",
            ):
                if disable_user(target):
                    audit.log_event(
                        "USER_DISABLED",
                        user=current_user_email,
                        details={"target": target},
                    )
                    st.success(f"**{target}** désactivé.")
                    st.rerun()
                else:
                    st.error("Échec.")
        else:
            if st.button("✅ Réactiver", use_container_width=True, key="btn_enable"):
                if enable_user(target):
                    audit.log_event(
                        "USER_ENABLED",
                        user=current_user_email,
                        details={"target": target},
                    )
                    st.success(f"**{target}** réactivé.")
                    st.rerun()
                else:
                    st.error("Échec.")

    with a2:
        new_role = "USER" if rec.get("role") == "ADMIN" else "ADMIN"
        if st.button(
            f"Passer en {new_role}",
            use_container_width=True,
            disabled=is_last_admin and new_role == "USER",
            key="btn_toggle_role",
        ):
            if update_user(target, role=new_role):
                audit.log_event(
                    "USER_ROLE_CHANGED",
                    user=current_user_email,
                    details={"target": target, "new_role": new_role},
                )
                st.success(f"**{target}** → **{new_role}**")
                st.rerun()
            else:
                st.error("Échec.")

    with a3:
        if st.button(
            "🗑️ Supprimer",
            use_container_width=True,
            disabled=is_self or is_last_admin,
            key="btn_remove",
        ):
            if remove_user(target):
                audit.log_event(
                    "USER_REMOVED",
                    user=current_user_email,
                    details={"target": target},
                )
                st.success(f"**{target}** supprimé.")
                st.rerun()
            else:
                st.error("Échec (dernier ADMIN ou erreur disque).")

    with a4:
        st.caption("Actions protégées")

    # ----- Mot de passe -----
    st.markdown("#### 🔑 Mot de passe")
    st.caption(
        "Générez un nouveau mot de passe et communiquez-le à l'utilisateur. "
        "L'ancien mot de passe est immédiatement invalidé."
    )

    p1, p2 = st.columns([1, 1])
    with p1:
        if st.button(
            "🎲 Générer un nouveau mot de passe",
            type="primary",
            use_container_width=True,
            key="btn_reset_pwd",
        ):
            plain = set_password(target, password=None)
            if plain:
                audit.log_event(
                    "USER_PASSWORD_RESET",
                    user=current_user_email,
                    details={"target": target},
                )
                st.session_state["_pwd_reset_result"] = {
                    "email": target,
                    "pwd": plain,
                }
                st.rerun()
            else:
                st.error("Échec de la réinitialisation.")

    with p2:
        with st.form("form_set_custom_pwd"):
            custom = st.text_input(
                "Ou définir un mot de passe manuel",
                type="password",
                key="custom_pwd_input",
            )
            if st.form_submit_button("Enregistrer ce mot de passe", use_container_width=True):
                ok_p, msg_p = validate_password(
                    custom, required=True, check_strength=True
                )
                if not ok_p:
                    st.error(msg_p)
                else:
                    plain = set_password(target, password=custom)
                    if plain:
                        audit.log_event(
                            "USER_PASSWORD_SET",
                            user=current_user_email,
                            details={"target": target},
                        )
                        st.success("Mot de passe mis à jour.")
                        st.session_state["_pwd_reset_result"] = {
                            "email": target,
                            "pwd": plain,
                        }
                        st.rerun()
                    else:
                        st.error("Échec de l'enregistrement du mot de passe.")

    pwd_result = st.session_state.get("_pwd_reset_result")
    if pwd_result and pwd_result.get("email") == target:
        st.warning(
            "⚠️ **Nouveau mot de passe** (à communiquer à l'utilisateur, "
            "puis masquez-le) :"
        )
        st.code(pwd_result["pwd"], language=None)
        if st.button("Masquer le mot de passe", key="hide_pwd_result"):
            st.session_state.pop("_pwd_reset_result", None)
            st.rerun()

    # Nom affiché
    with st.form("form_edit_name"):
        new_display = st.text_input(
            "Modifier le nom affiché",
            value=rec.get("display_name", ""),
            key="edit_display_name",
        )
        if st.form_submit_button("Enregistrer le nom", use_container_width=True):
            ok_n, msg_n = validate_display_name(new_display, required=False)
            if not ok_n:
                st.error(msg_n)
            elif update_user(target, display_name=new_display):
                st.success("Nom mis à jour.")
                st.rerun()
            else:
                st.error("Échec de la mise à jour du nom.")


# =============================================================================
# JOURNAUX
# =============================================================================
def _render_audit_tab() -> None:
    st.subheader("Journaux d'activité")
    st.caption(
        "Événements de sécurité et d'activité. "
        "Les mots de passe et données sensibles ne sont jamais enregistrés."
    )

    log_dir = Path(
        __import__("os").environ.get("RECOTRUST_LOG_DIR", "logs")
    )
    log_file = log_dir / "recotrust_audit.log"

    if not log_file.is_file():
        st.info(
            "Aucun journal pour le moment. Les événements apparaîtront après "
            f"les premières actions (chemin : `{log_file}`)."
        )
        return

    try:
        max_lines = st.slider("Nombre de lignes", 20, 500, 100, 20)
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        recent = lines[-max_lines:] if len(lines) > max_lines else lines
        recent.reverse()
        st.code("".join(recent) if recent else "(vide)", language="text")
        st.caption(f"`{log_file}` · {len(lines)} ligne(s) au total")
    except Exception as e:
        st.warning(f"Impossible de lire le journal : {e}")
