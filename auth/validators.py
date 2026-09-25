"""
RecoTrust V3.0 — Validation centralisée des formulaires.

Retourne toujours (ok: bool, message: str).
Message vide si ok=True.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional, Tuple

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Domaines recommandés (avertissement si hors domaine, pas de blocage strict)
PREFERRED_DOMAINS = ("paymetrust.net", "paymetrustapp.com")

# Politique mot de passe
PWD_MIN_LENGTH = 8
PWD_MAX_LENGTH = 64

# Upload
ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls")
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024  # 4 Go (aligné config.toml V5.1 — fichiers partenaires ~3 Go)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_email(
    email: str,
    *,
    required: bool = True,
    require_preferred_domain: bool = False,
) -> Tuple[bool, str]:
    """Valide une adresse e-mail."""
    value = (email or "").strip()
    if not value:
        if required:
            return False, "L'adresse e-mail est obligatoire."
        return True, ""
    if len(value) > 254:
        return False, "L'adresse e-mail est trop longue."
    if not EMAIL_RE.match(value):
        return False, "Format d'e-mail invalide (ex. prenom.nom@paymetrust.net)."
    domain = value.rsplit("@", 1)[-1].lower()
    if require_preferred_domain and domain not in PREFERRED_DOMAINS:
        return (
            False,
            f"Seules les adresses @{PREFERRED_DOMAINS[0]} "
            f"(ou @{PREFERRED_DOMAINS[1]}) sont acceptées.",
        )
    return True, ""


def validate_password(
    password: str,
    *,
    required: bool = True,
    check_strength: bool = True,
) -> Tuple[bool, str]:
    """
    Valide un mot de passe.
    Si check_strength=True : longueur min, au moins une lettre et un chiffre.
    """
    value = password or ""
    if not value:
        if required:
            return False, "Le mot de passe est obligatoire."
        return True, ""
    if len(value) < PWD_MIN_LENGTH:
        return (
            False,
            f"Le mot de passe doit contenir au moins {PWD_MIN_LENGTH} caractères.",
        )
    if len(value) > PWD_MAX_LENGTH:
        return (
            False,
            f"Le mot de passe ne peut pas dépasser {PWD_MAX_LENGTH} caractères.",
        )
    if check_strength:
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        if not has_letter:
            return False, "Le mot de passe doit contenir au moins une lettre."
        if not has_digit:
            return False, "Le mot de passe doit contenir au moins un chiffre."
    return True, ""


def validate_display_name(name: str, *, required: bool = False) -> Tuple[bool, str]:
    value = (name or "").strip()
    if not value:
        if required:
            return False, "Le nom affiché est obligatoire."
        return True, ""
    if len(value) < 2:
        return False, "Le nom affiché doit contenir au moins 2 caractères."
    if len(value) > 80:
        return False, "Le nom affiché ne peut pas dépasser 80 caractères."
    if re.search(r"[<>\"\\]", value):
        return False, "Le nom affiché contient des caractères non autorisés."
    return True, ""


def validate_role(role: str) -> Tuple[bool, str]:
    if role not in ("USER", "ADMIN"):
        return False, "Rôle invalide (USER ou ADMIN attendu)."
    return True, ""


def validate_date_range(
    start: Optional[date],
    end: Optional[date],
    *,
    max_span_days: int = 366,
    allow_future: bool = True,
) -> Tuple[bool, str]:
    """Valide une période de réconciliation."""
    if start is None or end is None:
        return False, "Les dates de début et de fin sont obligatoires."
    if start > end:
        return False, "La date de début doit être antérieure ou égale à la date de fin."
    span = (end - start).days
    if span > max_span_days:
        return (
            False,
            f"La période ne peut pas dépasser {max_span_days} jours "
            f"(période sélectionnée : {span} jours).",
        )
    if not allow_future:
        today = date.today()
        if start > today or end > today:
            return False, "Les dates ne peuvent pas être dans le futur."
    # Date trop ancienne (garde-fou)
    min_date = date.today() - timedelta(days=365 * 5)
    if start < min_date:
        return (
            False,
            f"La date de début est trop ancienne (minimum : {min_date.strftime('%d/%m/%Y')}).",
        )
    return True, ""


def validate_match_column(col: Optional[str], label: str = "colonne") -> Tuple[bool, str]:
    value = (col or "").strip()
    if not value:
        return False, f"La {label} de matching est obligatoire."
    if len(value) > 120:
        return False, f"Le nom de la {label} est trop long."
    return True, ""


def validate_uploaded_file(
    file,
    *,
    label: str = "fichier",
    required: bool = True,
) -> Tuple[bool, str]:
    """Valide un fichier uploadé Streamlit (extension, taille, nom)."""
    if file is None:
        if required:
            return False, f"Le {label} est obligatoire."
        return True, ""

    name = getattr(file, "name", "") or ""
    size = getattr(file, "size", None)

    if not name.strip():
        return False, f"Le nom du {label} est invalide."

    # Path traversal / caractères dangereux
    if ".." in name or "/" in name or "\\" in name:
        return False, f"Le nom du {label} contient des caractères non autorisés."

    lower = name.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return (
            False,
            f"Format du {label} non supporté. "
            f"Extensions autorisées : {', '.join(ALLOWED_EXTENSIONS)}.",
        )

    if size is not None:
        if size <= 0:
            return False, f"Le {label} est vide."
        if size > MAX_UPLOAD_BYTES:
            return (
                False,
                f"Le {label} dépasse la taille maximale autorisée "
                f"({MAX_UPLOAD_BYTES // (1024**3)} Go).",
            )

    return True, ""


def password_strength_hint(password: str) -> str:
    """Retourne un libellé de force (Faible / Moyen / Fort) pour l'UI."""
    if not password:
        return ""
    score = 0
    if len(password) >= PWD_MIN_LENGTH:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c.islower() for c in password) and any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()-_=+[]{};:,.?/" for c in password):
        score += 1
    if score <= 2:
        return "Faible"
    if score <= 3:
        return "Moyen"
    return "Fort"
