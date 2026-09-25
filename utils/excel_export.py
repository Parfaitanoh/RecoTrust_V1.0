"""
Générateur de rapport Excel multi-onglets pour la réconciliation.
"""
import pandas as pd
import io
import re
from datetime import datetime
from typing import Dict, Optional, Any


class ExcelExporter:
    """Crée un rapport Excel professionnel à partir des résultats de réconciliation."""

    @staticmethod
    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
        """Prépare un DataFrame pour openpyxl — conversion agressive anti TRANSFER_DATE."""
        if not isinstance(df, pd.DataFrame):
            return pd.DataFrame(df)
        try:
            if not isinstance(df.index, pd.RangeIndex) or df.index.name is not None or getattr(df.index, "nlevels", 1) > 1:
                export_df = df.reset_index()
            else:
                export_df = df.copy()
        except Exception:
            export_df = df.copy()
            try:
                export_df = export_df.reset_index()
            except Exception:
                pass

        # Aplatir MultiIndex colonnes
        if isinstance(export_df.columns, pd.MultiIndex):
            export_df.columns = [
                "_".join(str(x) for x in tup if x is not None and str(x) != "")
                for tup in export_df.columns
            ]
        else:
            export_df.columns = [str(c) for c in export_df.columns]

        def _cell(v):
            try:
                if v is None:
                    return ""
                if isinstance(v, float) and pd.isna(v):
                    return ""
                if pd.isna(v):
                    return ""
            except Exception:
                pass
            if isinstance(v, pd.Timestamp):
                try:
                    return v.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return str(v)
            try:
                from datetime import date, datetime as dt
                if isinstance(v, (date, dt)):
                    return pd.Timestamp(v).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
            # bytes
            if isinstance(v, (bytes, bytearray)):
                try:
                    return v.decode("utf-8", errors="replace")
                except Exception:
                    return str(v)
            return str(v)

        # Forcer toutes les colonnes « date-like » ou object en str
        for col in list(export_df.columns):
            series = export_df[col]
            col_u = str(col).upper()
            force_str = (
                series.dtype == object
                or str(series.dtype) == "object"
                or pd.api.types.is_datetime64_any_dtype(series)
                or "DATE" in col_u
                or "TIME" in col_u
                or "JOUR" in col_u
            )
            if force_str:
                export_df[col] = series.map(_cell)
            elif pd.api.types.is_bool_dtype(series):
                export_df[col] = series.fillna(False).astype(int)
            elif isinstance(series.dtype, pd.CategoricalDtype):
                export_df[col] = series.astype(str)
            # sinon numérique laissé tel quel

        # Dernière ligne de défense : toute colonne encore object → str
        for col in list(export_df.columns):
            if export_df[col].dtype == object:
                export_df[col] = export_df[col].map(_cell)

        return export_df

    def _fmt_date(value) -> str:
        if value is None or value == "":
            return ""
        try:
            return pd.to_datetime(value).strftime("%Y%m%d")
        except Exception:
            s = str(value).replace("-", "").replace("/", "")[:8]
            return s if s.isdigit() else ""

    @staticmethod
    def _safe_partner(name: str) -> str:
        s = (name or "PARTENAIRE").strip().upper()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^A-Z0-9_]", "", s)
        return s or "PARTENAIRE"

    @staticmethod
    def build_filename(partner_name: str, reco_start=None, reco_end=None) -> str:
        """
        Format : {date_du_jour}_{partenaire}_{date_debut}_{date_fin}.xlsx
        Exemple : 20260730_WAVE_CI_PAYIN_20260729_20260730.xlsx
        """
        today = datetime.now().strftime("%Y%m%d")
        partner = ExcelExporter._safe_partner(partner_name)
        d_start = ExcelExporter._fmt_date(reco_start)
        d_end = ExcelExporter._fmt_date(reco_end)

        parts = [today, partner]
        if d_start:
            parts.append(d_start)
        if d_end and d_end != d_start:
            parts.append(d_end)

        return "_".join(parts) + ".xlsx"

    @staticmethod
    def create_report(partner_name: str, metrics: Dict[str, Any], sheets: Dict[str, pd.DataFrame]) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Extraire l'utilisateur pour l'afficher en tête du résumé
            metrics = dict(metrics) if metrics else {}
            user_email = metrics.pop("Utilisateur", None)

            summary_rows = [
                ["Rapport de Réconciliation", partner_name],
                ["Date de génération", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Version app", "V4"],
            ]
            if user_email:
                summary_rows.append(["Utilisateur", user_email])
            summary_rows.append(["", ""])
            for k, v in metrics.items():
                summary_rows.append([k, v])

            pd.DataFrame(summary_rows, columns=["Métrique", "Valeur"]).to_excel(
                writer, sheet_name="Résumé", index=False
            )

            # Origine opération (Payment / transfer) déduite du nom partenaire
            try:
                from utils.helpers import format_maj_sheet, infer_operation_origin
                _op_origin = infer_operation_origin(partner_name)
            except Exception:
                format_maj_sheet = None
                _op_origin = "Payment"

            for sheet_name, df in sheets.items():
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    continue
                safe_name = str(sheet_name)[:31]
                try:
                    export_df = df
                    if format_maj_sheet is not None and str(sheet_name).upper().startswith("MAJ"):
                        export_df = format_maj_sheet(df, operation_origin=_op_origin)
                    prepared = ExcelExporter._prepare_df(export_df)
                    try:
                        prepared.to_excel(writer, sheet_name=safe_name, index=False)
                    except Exception:
                        # Ultime recours : tout en texte
                        prepared2 = prepared.copy()
                        for _c in prepared2.columns:
                            prepared2[_c] = prepared2[_c].map(lambda v: "" if v is None else str(v))
                        prepared2.to_excel(writer, sheet_name=safe_name, index=False)
                except Exception as e:
                    pd.DataFrame({"Erreur": [str(e)]}).to_excel(
                        writer, sheet_name=safe_name, index=False
                    )
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def download_button(
        partner_name: str,
        metrics: Dict[str, Any],
        sheets: Dict[str, pd.DataFrame],
        label: str = None,
        key: str = "download_report",
        reco_start=None,
        reco_end=None,
    ):
        import streamlit as st

        try:
            filename = ExcelExporter.build_filename(
                partner_name, reco_start=reco_start, reco_end=reco_end
            )

            # Cache des bytes Excel : évite de régénérer à chaque clic / rerun
            cache_key = (
                partner_name,
                str(reco_start),
                str(reco_end),
                tuple(sorted(sheets.keys())),
                tuple((k, str(v)) for k, v in sorted(metrics.items())),
            )
            prev_key = st.session_state.get("excel_report_cache_key")
            if (
                prev_key == cache_key
                and st.session_state.get("excel_report_bytes")
                and st.session_state.get("excel_report_name") == filename
            ):
                data = st.session_state["excel_report_bytes"]
            else:
                data = ExcelExporter.create_report(partner_name, metrics, sheets)
                st.session_state["excel_report_bytes"] = data
                st.session_state["excel_report_name"] = filename
                st.session_state["excel_report_cache_key"] = cache_key

            st.info(f"**V4** — Fichier : `{filename}`")
            btn_label = label or f"📥 Télécharger {filename}"
            st.download_button(
                label=btn_label,
                data=data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=key,
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Impossible de générer le rapport : {e}")
