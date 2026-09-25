"""
RecoTrust V3.0 — Registre centralisé des utilisateurs autorisés et des rôles.

Source unique de vérité pour :
  - Liste des emails autorisés
  - Rôles (USER | ADMIN)
  - Statut actif / désactivé
  - Mot de passe (hash PBKDF2 — jamais en clair)

Persistance : fichier JSON (data/authorized_users.json).
Les modifications via l'écran ADMIN survivent aux redémarrages.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import string
import threading
from pathlib import Path
from typing import Dict, List, Optional, TypedDict


class UserRecord(TypedDict, total=False):
    role: str          # "USER" | "ADMIN"
    active: bool
    display_name: str
    password_hash: str  # format: pbkdf2$iterations$salt_hex$hash_hex


VALID_ROLES = ("USER", "ADMIN")

# Hash parameters
_PBKDF2_ITERATIONS = 120_000
_SALT_BYTES = 16

# ---------------------------------------------------------------------------
# Valeurs par défaut (seed initial — mots de passe générés au premier load)
# ---------------------------------------------------------------------------
_DEFAULT_USERS_META = {
    "parfait.ngoran@paymetrust.net": {
        "role": "ADMIN",
        "active": True,
        "display_name": "Parfait Ngoran",
    },
    "eliezer.tanoh@paymetrust.net": {
        "role": "USER",
        "active": True,
        "display_name": "Eliezer Tanoh",
    },
    "niamkey.nguessan@paymetrust.net": {
        "role": "USER",
        "active": True,
        "display_name": "Niamkey Nguessan",
    },
    "pegard.kouadja@paymetrust.net": {
        "role": "USER",
        "active": True,
        "display_name": "Pegard Kouadja",
    },
    "joel.nando@paymetrust.net": {
        "role": "USER",
        "active": True,
        "display_name": "Joel Nando",
    },
    "franck.ouraga@paymetrust.net": {
        "role": "USER",
        "active": True,
        "display_name": "Franck Ouraga",
    },
}

# Mot de passe initial commun pour le seed (à changer via l'admin)
_SEED_PASSWORD = "RecoTrust2026!"

# Répertoire data absolu (racine application = parent de auth/)
_APP_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = Path(os.environ.get("RECOTRUST_DATA_DIR", str(_APP_ROOT / "data")))
_USERS_FILE = _DATA_DIR / "authorized_users.json"

_lock = threading.Lock()
AUTHORIZED_USERS: Dict[str, UserRecord] = {}
_loaded = False


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash un mot de passe avec PBKDF2-HMAC-SHA256 + salt aléatoire."""
    if not password:
        raise ValueError("Mot de passe vide")
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie un mot de passe contre le hash stocké."""
    if not password or not stored_hash:
        return False
    try:
        parts = stored_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return secrets.compare_digest(dk, expected)
    except Exception:
        return False


def generate_password(length: int = 12) -> str:
    """
    Génère un mot de passe aléatoire sécurisé.
    Mélange majuscules, minuscules, chiffres (sans caractères ambigus).
    """
    length = max(8, min(length, 32))
    alphabet = (
        string.ascii_uppercase.replace("O", "").replace("I", "")
        + string.ascii_lowercase.replace("l", "").replace("o", "")
        + string.digits.replace("0", "").replace("1", "")
    )
    # Garantir au moins un de chaque type
    pwd = [
        secrets.choice(string.ascii_uppercase.replace("O", "").replace("I", "")),
        secrets.choice(string.ascii_lowercase.replace("l", "").replace("o", "")),
        secrets.choice(string.digits.replace("0", "").replace("1", "")),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(length - 3)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def _ensure_loaded() -> None:
    global _loaded, AUTHORIZED_USERS
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        AUTHORIZED_USERS = _load_from_disk()
        _loaded = True


def _load_from_disk() -> Dict[str, UserRecord]:
    try:
        if _USERS_FILE.is_file():
            with open(_USERS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            users: Dict[str, UserRecord] = {}
            for email, rec in (raw or {}).items():
                email_n = normalize_email(email)
                if not email_n or not isinstance(rec, dict):
                    continue
                role = rec.get("role", "USER")
                if role not in VALID_ROLES:
                    role = "USER"
                entry: UserRecord = {
                    "role": role,
                    "active": bool(rec.get("active", True)),
                    "display_name": str(rec.get("display_name") or email_n.split("@")[0]),
                }
                ph = rec.get("password_hash") or ""
                if ph:
                    entry["password_hash"] = str(ph)
                else:
                    # Migration : utilisateur sans hash → seed password
                    entry["password_hash"] = hash_password(_SEED_PASSWORD)
                users[email_n] = entry
            if users:
                # Persister les hash migrés
                _save_to_disk(users)
                return users
    except Exception:
        pass

    # Seed initial avec mot de passe par défaut
    users = {}
    seed_hash = hash_password(_SEED_PASSWORD)
    for email, meta in _DEFAULT_USERS_META.items():
        users[email] = {
            "role": meta["role"],
            "active": meta["active"],
            "display_name": meta["display_name"],
            "password_hash": seed_hash,
        }
    _save_to_disk(users)
    return users


def _save_to_disk(users: Dict[str, UserRecord]) -> bool:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _USERS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2, sort_keys=True)
        tmp.replace(_USERS_FILE)
        return True
    except Exception:
        return False


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def get_user(email: str) -> Optional[UserRecord]:
    _ensure_loaded()
    return AUTHORIZED_USERS.get(normalize_email(email))


def is_authorized(email: str) -> bool:
    user = get_user(email)
    return bool(user and user.get("active", False))


def get_role(email: str) -> Optional[str]:
    user = get_user(email)
    if not user or not user.get("active", False):
        return None
    return user.get("role")


def is_admin(email: str) -> bool:
    return get_role(email) == "ADMIN"


def authenticate(email: str, password: str) -> bool:
    """Vérifie email + mot de passe. True si compte actif et mdp correct."""
    user = get_user(email)
    if not user or not user.get("active", False):
        return False
    stored = user.get("password_hash") or ""
    return verify_password(password, stored)


def list_authorized_emails(active_only: bool = True) -> List[str]:
    _ensure_loaded()
    if active_only:
        return sorted(
            email
            for email, rec in AUTHORIZED_USERS.items()
            if rec.get("active", False)
        )
    return sorted(AUTHORIZED_USERS.keys())


def list_all_users() -> Dict[str, UserRecord]:
    """Copie du registre (sans exposer les hash dans l'UI si non nécessaire)."""
    _ensure_loaded()
    return {k: dict(v) for k, v in AUTHORIZED_USERS.items()}


def add_user(
    email: str,
    role: str = "USER",
    display_name: str = "",
    password: Optional[str] = None,
) -> Optional[str]:
    """
    Ajoute un utilisateur.
    Si password est None, un mot de passe est généré automatiquement.
    Retourne le mot de passe en clair (à communiquer une seule fois), ou None si échec.
    """
    email = normalize_email(email)
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return None
    if role not in VALID_ROLES:
        role = "USER"
    plain = password if password else generate_password(12)
    _ensure_loaded()
    with _lock:
        AUTHORIZED_USERS[email] = {
            "role": role,
            "active": True,
            "display_name": (display_name or email.split("@")[0]).strip(),
            "password_hash": hash_password(plain),
        }
        if not _save_to_disk(AUTHORIZED_USERS):
            return None
    return plain


def set_password(email: str, password: Optional[str] = None) -> Optional[str]:
    """
    Définit / réinitialise le mot de passe d'un utilisateur.
    Si password est None, génère un nouveau mot de passe.
    Retourne le mot de passe en clair (à communiquer), ou None si échec.
    """
    email = normalize_email(email)
    _ensure_loaded()
    with _lock:
        if email not in AUTHORIZED_USERS:
            return None
        plain = password if password else generate_password(12)
        AUTHORIZED_USERS[email]["password_hash"] = hash_password(plain)
        if not _save_to_disk(AUTHORIZED_USERS):
            return None
    return plain


def update_user(
    email: str,
    role: Optional[str] = None,
    active: Optional[bool] = None,
    display_name: Optional[str] = None,
) -> bool:
    email = normalize_email(email)
    _ensure_loaded()
    with _lock:
        if email not in AUTHORIZED_USERS:
            return False
        rec = AUTHORIZED_USERS[email]
        if role is not None and role in VALID_ROLES:
            rec["role"] = role
        if active is not None:
            rec["active"] = bool(active)
        if display_name is not None:
            rec["display_name"] = display_name.strip() or rec.get("display_name", "")
        return _save_to_disk(AUTHORIZED_USERS)


def disable_user(email: str) -> bool:
    return update_user(email, active=False)


def enable_user(email: str) -> bool:
    return update_user(email, active=True)


def remove_user(email: str) -> bool:
    email = normalize_email(email)
    _ensure_loaded()
    with _lock:
        if email not in AUTHORIZED_USERS:
            return False
        target = AUTHORIZED_USERS[email]
        if target.get("role") == "ADMIN" and target.get("active"):
            other_admins = [
                e
                for e, r in AUTHORIZED_USERS.items()
                if e != email and r.get("role") == "ADMIN" and r.get("active")
            ]
            if not other_admins:
                return False
        del AUTHORIZED_USERS[email]
        return _save_to_disk(AUTHORIZED_USERS)


def count_admins(active_only: bool = True) -> int:
    _ensure_loaded()
    return sum(
        1
        for r in AUTHORIZED_USERS.values()
        if r.get("role") == "ADMIN" and (not active_only or r.get("active"))
    )


def get_stats() -> Dict[str, int]:
    """Statistiques pour le dashboard admin."""
    _ensure_loaded()
    total = len(AUTHORIZED_USERS)
    active = sum(1 for r in AUTHORIZED_USERS.values() if r.get("active"))
    admins = sum(
        1
        for r in AUTHORIZED_USERS.values()
        if r.get("role") == "ADMIN" and r.get("active")
    )
    users = sum(
        1
        for r in AUTHORIZED_USERS.values()
        if r.get("role") == "USER" and r.get("active")
    )
    disabled = total - active
    return {
        "total": total,
        "active": active,
        "disabled": disabled,
        "admins": admins,
        "users": users,
    }
