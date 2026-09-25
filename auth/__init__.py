"""
RecoTrust V3.0 — Package d'authentification et d'autorisation.

- Authentification e-mail + mot de passe (liste blanche)
- Rôles USER / ADMIN (registre persisté JSON)
- Mots de passe générés / gérés par les administrateurs
- Journalisation des événements de sécurité
- Écran d'administration (ADMIN uniquement)
"""

from auth.users import (
    AUTHORIZED_USERS,
    VALID_ROLES,
    add_user,
    authenticate,
    count_admins,
    disable_user,
    enable_user,
    generate_password,
    get_role,
    get_stats,
    get_user,
    hash_password,
    is_admin,
    is_authorized,
    list_all_users,
    list_authorized_emails,
    normalize_email,
    remove_user,
    set_password,
    update_user,
    verify_password,
)
from auth.session import (
    get_authenticated_email,
    get_current_user_info,
    logout_user,
    require_auth,
)
from auth import audit

__all__ = [
    "AUTHORIZED_USERS",
    "VALID_ROLES",
    "add_user",
    "authenticate",
    "count_admins",
    "disable_user",
    "enable_user",
    "generate_password",
    "get_role",
    "get_stats",
    "get_user",
    "hash_password",
    "is_admin",
    "is_authorized",
    "list_all_users",
    "list_authorized_emails",
    "normalize_email",
    "remove_user",
    "set_password",
    "update_user",
    "verify_password",
    "get_authenticated_email",
    "get_current_user_info",
    "logout_user",
    "require_auth",
    "audit",
]
