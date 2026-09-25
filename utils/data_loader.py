"""
Chargeur de fichiers ultra-rapide avec cache Streamlit.

- Cache basé sur le contenu (hash) → relecture instantanée après le 1er chargement
- Compatible CSV (détection auto du séparateur + retry anti-collapse), Excel (.xlsx) et Excel 97-2003 (.xls)
- Aucune base de données, purement en mémoire / session
- V5.1 mémoire : caches DataFrame limités (gros fichiers multi-Go), purge des
  uploads obsolètes en session, libération à la déconnexion / changement de fichiers
"""
from __future__ import annotations

import hashlib
import io
from typing import Optional, Union

import pandas as pd
import streamlit as st


def _content_hash(data: bytes) -> str:
    """Hash rapide (blake2b) du contenu binaire."""
    return hashlib.blake2b(data, digest_size=16).hexdigest()


def _detect_csv_encoding(content: bytes) -> str:
    """Détecte un encodage raisonnable (BOM UTF-8 prioritaire)."""
    if content.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
        return "utf-16"
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            content.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _count_fields(line: str, delimiter: str) -> int:
    """Compte les champs d'une ligne en respectant les guillemets."""
    in_quotes = False
    n = 1
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                i += 2
                continue
            in_quotes = not in_quotes
        elif ch == delimiter and not in_quotes:
            n += 1
        i += 1
    return n


def _score_delimiter(sample_lines, delimiter: str) -> float:
    """
    Score un séparateur candidat :
    - header avec >= 2 colonnes
    - stabilité du nombre de colonnes sur les lignes suivantes
    - pénalité si beaucoup de lignes à 1 seule colonne
    """
    if not sample_lines:
        return -1e9

    counts = [_count_fields(ln, delimiter) for ln in sample_lines]
    header_cols = counts[0]
    if header_cols < 2:
        return -1e9

    stable = sum(1 for c in counts if c == header_cols)
    single = sum(1 for c in counts if c == 1)
    # bonus léger si le header contient des noms PMT connus
    header = sample_lines[0].lower()
    pmt_hints = (
        "transaction_id",
        "created_at",
        "merchant_name",
        "phone_number",
        "id_operator",
        "statut",
        "amount",
    )
    hint_bonus = sum(2 for h in pmt_hints if h in header)

    return stable * 10 + header_cols + hint_bonus - single * 5


def _detect_csv_delimiter(text: str) -> str:
    """Choisit le meilleur séparateur parmi ; , tab |."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    sample = lines[:40] if lines else [","]
    candidates = [";", ",", "\t", "|"]
    best = ";"
    best_score = float("-inf")
    for d in candidates:
        score = _score_delimiter(sample, d)
        if score > best_score:
            best_score = score
            best = d
    if best_score <= 0:
        first = sample[0]
        best = ";" if first.count(";") >= first.count(",") else ","
    return best


def _csv_looks_collapsed(df: pd.DataFrame) -> bool:
    """
    True si le parse a probablement échoué :
    - 1 seule colonne, ou
    - 1ère colonne contient encore le séparateur et les autres sont quasi vides
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return False
    if df.shape[1] == 1:
        return True
    first = df.iloc[:, 0].astype(str)
    sep_hits = first.str.contains(r"[,;|\t]", regex=True, na=False).mean()
    other_null = float(df.iloc[:, 1:].isna().mean().mean()) if df.shape[1] > 1 else 1.0
    if sep_hits > 0.4 and other_null > 0.6:
        return True
    return False


@st.cache_data(show_spinner=False, max_entries=4, ttl=1800)
def _parse_csv_cached(content: bytes, filename: str) -> pd.DataFrame:
    """
    Parse CSV robuste :
    - détection encodage (utf-8-sig / cp1252…)
    - détection séparateur sur plusieurs lignes (; , tab |)
    - engine python (quotes / lignes irrégulières)
    - retry auto si résultat « collapsé » (toute la ligne dans une colonne)
    """
    encoding = _detect_csv_encoding(content)
    try:
        text = content.decode(encoding, errors="ignore")
    except Exception:
        text = content.decode("utf-8", errors="ignore")
        encoding = "utf-8"

    # Excel FR ajoute parfois une 1ère ligne "sep=;" ou "sep=,"
    excel_sep = None
    lines_raw = text.splitlines()
    if lines_raw:
        first_stripped = lines_raw[0].strip().lower().replace(" ", "")
        if first_stripped.startswith("sep=") and len(first_stripped) >= 5:
            excel_sep = first_stripped.split("=", 1)[1][:1]
            if excel_sep == "\t":
                excel_sep = "\t"
            # retirer la ligne sep= du contenu pour le parse
            content_wo = "\n".join(lines_raw[1:]).encode(encoding, errors="ignore")
        else:
            content_wo = content
    else:
        content_wo = content

    delimiter = excel_sep or _detect_csv_delimiter(
        content_wo.decode(encoding, errors="ignore") if isinstance(content_wo, (bytes, bytearray)) else text
    )

    def _read(delim: str, enc: str, data: bytes = content_wo) -> pd.DataFrame:
        kwargs = dict(
            delimiter=delim,
            encoding=enc,
            engine="python",
            quotechar='"',
            doublequote=True,
        )
        try:
            return pd.read_csv(io.BytesIO(data), on_bad_lines="warn", **kwargs)
        except TypeError:
            return pd.read_csv(io.BytesIO(data), **kwargs)

    df = _read(delimiter, encoding, content_wo)

    if _csv_looks_collapsed(df):
        for alt in [";", ",", "\t", "|"]:
            if alt == delimiter:
                continue
            try:
                df2 = _read(alt, encoding, content_wo)
            except Exception:
                continue
            if not _csv_looks_collapsed(df2) and df2.shape[1] > max(df.shape[1], 1):
                df = df2
                break

    # Nettoyage noms de colonnes (BOM résiduel / espaces)
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    return df


@st.cache_data(show_spinner=False, max_entries=4, ttl=1800)
def _parse_excel_xlsx_cached(content: bytes, filename: str) -> pd.DataFrame:
    """Parse Excel moderne (.xlsx) depuis bytes — openpyxl."""
    return pd.read_excel(io.BytesIO(content), engine="openpyxl")


@st.cache_data(show_spinner=False, max_entries=4, ttl=1800)
def _parse_excel_xlsx_skiprows_cached(content: bytes, filename: str, skiprows: int) -> pd.DataFrame:
    """Parse Excel .xlsx avec skiprows (certains partenaires)."""
    return pd.read_excel(io.BytesIO(content), engine="openpyxl", skiprows=skiprows)


@st.cache_data(show_spinner=False, max_entries=4, ttl=1800)
def _parse_excel_xls_cached(content: bytes, filename: str) -> pd.DataFrame:
    """Parse Excel 97-2003 (.xls) depuis bytes — xlrd."""
    return pd.read_excel(io.BytesIO(content), engine="xlrd")


@st.cache_data(show_spinner=False, max_entries=4, ttl=1800)
def _parse_excel_xls_skiprows_cached(content: bytes, filename: str, skiprows: int) -> pd.DataFrame:
    """Parse Excel .xls avec skiprows."""
    return pd.read_excel(io.BytesIO(content), engine="xlrd", skiprows=skiprows)


def _file_bytes_key(file) -> str:
    """Clé session stable pour les bytes d'un upload (nom + taille)."""
    name = getattr(file, "name", "upload.bin") or "upload.bin"
    size = getattr(file, "size", 0) or 0
    return f"_file_bytes::{name}::{size}"


def materialize_upload(file) -> Optional[bytes]:
    """
    Lit le contenu d'un UploadedFile une seule fois et le stocke en session_state.
    Retourne les bytes (ou None).

    Les bytes restent en session pour survivre aux reruns Streamlit (l'objet
    UploadedFile n'est pas stable). Utiliser prune_stale_file_bytes() lors d'un
    changement de fichiers pour éviter d'accumuler plusieurs Go en session.
    """
    if file is None:
        return None
    key = _file_bytes_key(file)
    if key not in st.session_state:
        try:
            st.session_state[key] = file.getvalue()
        except Exception:
            pos = file.tell() if hasattr(file, "tell") else 0
            file.seek(0)
            st.session_state[key] = file.read()
            try:
                file.seek(pos)
            except Exception:
                pass
    return st.session_state[key]


def prune_stale_file_bytes(keep_files=None) -> int:
    """
    Supprime les entrées ``_file_bytes::*`` et ``_match_cols::*`` qui ne
    correspondent plus aux fichiers courants.

    Parameters
    ----------
    keep_files : iterable d'UploadedFile | None
        Fichiers à conserver. Si None, purge tout.

    Returns
    -------
    int
        Nombre de clés session supprimées.
    """
    keep_keys = set()
    if keep_files:
        for f in keep_files:
            if f is not None:
                try:
                    keep_keys.add(_file_bytes_key(f))
                except Exception:
                    pass

    removed = 0
    for k in list(st.session_state.keys()):
        ks = str(k)
        if ks.startswith("_file_bytes::"):
            if ks not in keep_keys:
                try:
                    del st.session_state[k]
                    removed += 1
                except Exception:
                    pass
        elif ks.startswith("_match_cols::") or ks.startswith("_cols::"):
            # Colonnes de matching liées à d'anciens uploads
            if not keep_keys:
                try:
                    del st.session_state[k]
                    removed += 1
                except Exception:
                    pass
    return removed


def release_heavy_session_artifacts() -> None:
    """
    Libère les artefacts lourds en session (rapport Excel, résultats, timers)
    sans toucher à l'auth ni à la navigation.
    Appeler lors d'un changement de fichiers ou avant un nouveau traitement.
    """
    for key in (
        "excel_report_bytes",
        "excel_report_name",
        "excel_report_cache_key",
        "reco_results",
        "reco_elapsed_sec",
        "pending_run",
    ):
        st.session_state.pop(key, None)


def load_dataframe(
    file,
    skiprows: int = 0,
    **kwargs,
) -> Optional[pd.DataFrame]:
    """
    Charge un CSV, Excel (.xlsx) ou Excel 97-2003 (.xls) de façon optimisée (cache par contenu).

    Accepte un UploadedFile Streamlit, un BytesIO, des bytes, ou un objet file-like.
    Compatible avec les signatures existantes des processeurs (skiprows, **kwargs).
    """
    if file is None:
        return None

    try:
        if isinstance(file, (bytes, bytearray)):
            content = bytes(file)
            filename = kwargs.get("filename", "data.bin")
        elif hasattr(file, "getvalue"):
            content = materialize_upload(file)
            filename = getattr(file, "name", "upload.bin") or "upload.bin"
        elif hasattr(file, "read"):
            pos = file.tell() if hasattr(file, "tell") else 0
            file.seek(0)
            content = file.read()
            try:
                file.seek(pos)
            except Exception:
                pass
            filename = getattr(file, "name", "file.bin") or "file.bin"
        else:
            st.error("Type de fichier non supporté pour le chargement.")
            return None

        if not content:
            st.error("Fichier vide.")
            return None

        name_lower = filename.lower()

        if name_lower.endswith(".csv"):
            return _parse_csv_cached(content, filename)

        if name_lower.endswith(".xlsx"):
            if skiprows and skiprows > 0:
                return _parse_excel_xlsx_skiprows_cached(content, filename, int(skiprows))
            return _parse_excel_xlsx_cached(content, filename)

        if name_lower.endswith(".xls"):
            if skiprows and skiprows > 0:
                return _parse_excel_xls_skiprows_cached(content, filename, int(skiprows))
            return _parse_excel_xls_cached(content, filename)

        if content[:4] == b"PK\x03\x04":
            if skiprows and skiprows > 0:
                return _parse_excel_xlsx_skiprows_cached(content, filename, int(skiprows))
            return _parse_excel_xlsx_cached(content, filename)
        if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            if skiprows and skiprows > 0:
                return _parse_excel_xls_skiprows_cached(content, filename, int(skiprows))
            return _parse_excel_xls_cached(content, filename)

        st.error(f"Format non supporté : {filename}. Formats acceptés : CSV, XLSX, XLS (Excel 97-2003).")
        return None

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return None


@st.cache_data(show_spinner=False, max_entries=32, ttl=3600)
def _headers_csv_cached(content: bytes, filename: str) -> tuple:
    """Lit uniquement la 1re ligne d'un CSV (rapide, sans charger tout le fichier)."""
    import csv as _csv

    enc = _detect_csv_encoding(content)
    # Assez pour le header même avec beaucoup de colonnes
    sample = content[:131072].decode(enc, errors="replace")
    if not sample.strip():
        return tuple()
    delim = _detect_csv_delimiter(sample)
    first = sample.splitlines()[0] if sample.splitlines() else ""
    try:
        row = next(_csv.reader([first], delimiter=delim))
    except Exception:
        row = first.split(delim)
    cols = tuple(str(c).replace("\ufeff", "").strip() for c in row if str(c).strip() != "")
    return cols


@st.cache_data(show_spinner=False, max_entries=16, ttl=3600)
def _headers_xlsx_cached(content: bytes, filename: str) -> tuple:
    """Lit uniquement la 1re ligne d'un XLSX via openpyxl read_only."""
    try:
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
        wb.close()
        if not row:
            return tuple()
        return tuple(str(c).replace("\ufeff", "").strip() for c in row if c is not None and str(c).strip() != "")
    except Exception:
        # Fallback : parse minimal via pandas (1 ligne)
        try:
            df = pd.read_excel(io.BytesIO(content), nrows=0, engine="openpyxl")
            return tuple(str(c).replace("\ufeff", "").strip() for c in df.columns)
        except Exception:
            return tuple()


@st.cache_data(show_spinner=False, max_entries=8, ttl=3600)
def _headers_xls_cached(content: bytes, filename: str) -> tuple:
    """Lit uniquement les en-têtes d'un XLS (Excel 97-2003)."""
    try:
        df = pd.read_excel(io.BytesIO(content), nrows=0, engine="xlrd")
        return tuple(str(c).replace("\ufeff", "").strip() for c in df.columns)
    except Exception:
        return tuple()


def get_file_columns(file) -> list:
    """
    Retourne la liste des colonnes d'un fichier **sans charger les données**.
    Utilisé pour peupler les selectbox de matching rapidement.
    """
    if file is None:
        return []
    try:
        if isinstance(file, (bytes, bytearray)):
            content = bytes(file)
            filename = "data.bin"
        elif hasattr(file, "getvalue"):
            content = materialize_upload(file)
            filename = getattr(file, "name", "upload.bin") or "upload.bin"
        elif hasattr(file, "read"):
            pos = file.tell() if hasattr(file, "tell") else 0
            file.seek(0)
            content = file.read()
            try:
                file.seek(pos)
            except Exception:
                pass
            filename = getattr(file, "name", "file.bin") or "file.bin"
        else:
            return []

        if not content:
            return []

        name_lower = filename.lower()
        if name_lower.endswith(".csv"):
            return list(_headers_csv_cached(content, filename))
        if name_lower.endswith(".xlsx") or content[:4] == b"PK\x03\x04":
            return list(_headers_xlsx_cached(content, filename))
        if name_lower.endswith(".xls") or content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return list(_headers_xls_cached(content, filename))
        # Tentative CSV par défaut
        cols = list(_headers_csv_cached(content, filename))
        return cols
    except Exception:
        return []


def clear_file_caches():
    """
    Vide les caches de parsing Streamlit et les bytes d'upload en session.
    À appeler à la déconnexion ou pour forcer une libération mémoire complète.
    """
    try:
        _parse_csv_cached.clear()
        _parse_excel_xlsx_cached.clear()
        _parse_excel_xlsx_skiprows_cached.clear()
        _parse_excel_xls_cached.clear()
        _parse_excel_xls_skiprows_cached.clear()
        _headers_csv_cached.clear()
        _headers_xlsx_cached.clear()
        _headers_xls_cached.clear()
    except Exception:
        pass
    # Purge totale des bytes et colonnes en session
    prune_stale_file_bytes(keep_files=None)
    release_heavy_session_artifacts()
    # Encourager le GC après libération de plusieurs Go
    try:
        import gc
        gc.collect()
    except Exception:
        pass
