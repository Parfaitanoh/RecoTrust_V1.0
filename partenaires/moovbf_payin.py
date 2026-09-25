import pandas as pd
import streamlit as st
import csv
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
from itertools import combinations
from collections import Counter
import zipfile
import io
import os
from streamlit_extras.stylable_container import stylable_container
import plotly.figure_factory as ff
from utils.data_loader import load_dataframe
from utils.pmt_schema import prepare_pmt_dataframe
from utils.helpers import metric_card, safe_show, filter_succes_abs_by_reco_date

class MoovbfPayinProcessor:
    def __init__(self, data_file, partner_file, reco_start=None, reco_end=None,
                 match_col_pmt=None, match_col_partner=None):
        self.data_file = data_file
        self.partner_file = partner_file
        self.reco_start = reco_start
        self.reco_end = reco_end
        self.match_col_pmt = match_col_pmt
        self.match_col_partner = match_col_partner
        self._partner_label = "MOOV BF PAYIN"


    def load_file(self, file, skiprows=0, **kwargs):
        """Chargement optimisé (cache Streamlit par contenu). Compatible skiprows (Moov, etc.)."""
        return load_dataframe(file, skiprows=skiprows, **kwargs)

    def process(self):
        # Charger les données
        pmt = self.load_file(self.data_file)
        dfop = self.load_file(self.partner_file, skiprows=12)
        


        # V1.1 — colonnes de matching (surcharge utilisateur ou défaut V1.0)
        match_key_pmt = self.match_col_pmt or 'Transaction ID'
        match_key_partner = self.match_col_partner or 'ThirdPartyTransactionId'
        # traitement  pour PMT
        # V1.2.0 — colonnes PMT conservées telles quelles (+ alias standard si besoin)
        dfpmt = prepare_pmt_dataframe(pmt)
        # --- Nettoyage & transformation CHEZ LE PARTENAIRE-------------------------------

        
        dfop['DateCourte'] = dfop['Initiation Time'].astype(str).apply(lambda x: x.split(' ')[0])
        payin = dfop[(dfop['Transaction Status'] == 'Completed') & (dfop['Details'] == 'Merchant API Payment')]

        payin["Paid In"] = pd.to_numeric(payin["Paid In"], errors="coerce")
        payin["Fee"] = pd.to_numeric(payin["Fee"], errors="coerce")
        payin['Taux(%)'] = (payin["Fee"] / payin["Paid In"]) * 100

        select_taux = payin.groupby(['Details']).agg(
                Taux=('Taux(%)', 'mean')
            )

         # Calcul des KPI------------------------------------
        
         # Calcul des KPI-----------------------------------------
       
        dfop_unique = payin.drop_duplicates(subset=match_key_partner)
        dfop_unique['Nombre'] = dfop_unique['Paid In']
        dfpmt['Nombre'] = dfpmt['Montant']

        #MISE EN PLACE DE RECHERCHE X POUR RECUPERATION CHEZ LE PARTENAIRE
        
        
        # Vérification des correspondances entre A1 et B1
        correspondance_statut_op = dfop_unique.set_index(match_key_partner)['Transaction Status']
        correspondance_date_op = dfop_unique.set_index(match_key_partner)['DateCourte']
        correspondance_idoperator = dfop_unique.set_index(match_key_partner)['Receipt No.']

        # Utilisation de map pour ajouter les colonnes correspondantes à dfpmt
        dfpmt['DATEOP'] = dfpmt[match_key_pmt].map(correspondance_date_op)
        dfpmt['STATUTOP'] = dfpmt[match_key_pmt].map(correspondance_statut_op)
        dfpmt['IDOPERATOR'] = dfpmt[match_key_pmt].map(correspondance_idoperator)
        
        #NBSI PMT &CINETPAY
        dfpmt['MOOV'] = dfpmt[match_key_pmt].isin(dfop_unique[match_key_partner]).astype(int)
        dfop_unique['PMT'] = dfop_unique[match_key_partner].isin(dfpmt[match_key_pmt]).astype(int)

        # --- Création des onglets ---

        tabs = st.tabs(["📊 Vue Globale", "👥 Rapport Reconciliation", "🔄 Rapport", "📈 Analytics Avancés"])
    
            # ==================================
               # Onglet 1 : Vue Globale
           # ==================================
        with tabs[0]:
            st.subheader("Vue Globale")
            #Nouveau: Sélecteur de période

            montant_total = dfpmt["Montant"].sum()
            nombre_transaction = dfpmt[match_key_pmt].count()
            taux_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'].shape[0] / nombre_transaction) * 100
            trx_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'])
            select = trx_succes['Transaction ID'].count()

            # Affichage dans des metric cards améliorées
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(metric_card("Transactions", nombre_transaction, "#3070F0", "🔄"), unsafe_allow_html=True)
            col2.markdown(metric_card("Transactions Succès", select, "#3070F0", "🔄"), unsafe_allow_html=True)
            col3.markdown(metric_card("Montant Total", f"{montant_total:,.2f}", "#3070F0", "💰"), unsafe_allow_html=True)
            col4.markdown(metric_card("Taux de Succès", f"{taux_succes:.1f}%", "#3070F0", "✅"), unsafe_allow_html=True)
            
            # Nouveau: Graphique combiné montant/nombre de transactions
            st.subheader("Évolution Journalière")
            daily_data = dfpmt.groupby('Date').agg(
                Montant=('Montant', 'sum'),
                Transactions=('Transaction ID', 'count')
            ).reset_index()
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                px.line(daily_data, x='Date', y='Montant').data[0],
                secondary_y=False,
            )
            fig.add_trace(
                px.bar(daily_data, x='Date', y='Transactions').data[0],
                secondary_y=True,
            )
            fig.update_layout(
                title="Volume et Nombre de Transactions",
                yaxis_title="Montant (XOF)",
                yaxis2_title="Nombre de Transactions",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # ================================
    # Onglet 2  : Opérations
# ================================
        df_filteredpmt = dfpmt[dfpmt['MOOV'] == 1]   
        with tabs[1]:
            st.subheader("Rapport Reconciliation Moov BF Payin")
            matched = df_filteredpmt['MOOV'].sum()
            unmatched = len(dfpmt) - matched
            try:
                matched_part = int(dfop_unique['PMT'].sum())
            except Exception:
                matched_part = int((dfop_unique['PMT'] == 1).sum()) if hasattr(dfop_unique, '__len__') else 0
            reconciliation_rate = (matched / len(dfpmt)) * 100
            maj = df_filteredpmt[(df_filteredpmt['Statut'] == 'FAILED') | (df_filteredpmt['Statut'] == 'PENDING')]
            nbre_maj = maj['Transaction ID'].count()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Transactions Matchées PMT", matched, delta=f"{reconciliation_rate:.1f}%")
            col2.metric("Total Transactions", len(dfpmt))
            col3.metric("Nombre transaction MAJ", nbre_maj)
            col4.metric("Transactions Matchées Part", matched_part)
            # Création du tableau croisé dynamique
            df_filtered = dfop_unique[(dfop_unique['PMT'] == 1) | (dfop_unique['PMT'] == 0)]

        # Création du tableau croisé dynamique
            df_filteredpmt = dfpmt[dfpmt['MOOV'] == 1] 
            tcdpmt = pd.pivot_table(
            df_filteredpmt,
            values=['Montant', 'Nombre'],
            index=['DATEOP', 'Statut'],
            aggfunc={'Nombre': 'count', 'Montant': 'sum'},
            fill_value=0,
            margins=True,
            margins_name='Total'
        )

            tcdpartner = pd.pivot_table(
            df_filtered,
            values=['Nombre', 'Paid In'],
            index=['DateCourte', 'Transaction Status'],
            aggfunc={'Nombre': 'count', 'Paid In': 'sum'},
            fill_value=0,
            margins=True,
            margins_name='Total'
                
        )
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Données PMT", "Données Partenaire", "TCD PMT", "TCD Partenaire", "Taux"])
            
            with tab1:
                safe_show(dfpmt)
                
            with tab2:
                st.write(dfop)
                
            with tab3:
                safe_show(tcdpmt)
                
            with tab4:
                st.write(tcdpartner)

            with tab5:
                st.write(select_taux)
    
            # LES TRANSACTIONS A METTRE A JOUR
            
            maj_failed_a_succes = dfpmt.loc[(dfpmt['Statut'] != 'SUCCESS') & (dfpmt['MOOV'] == 1)]
            #maj_pending_a_succes = dfpmt.loc[(dfpmt['Statut'] == 'PENDING') & (dfpmt['MOOV'] == 1)]
            trx_succes_abs = dfpmt.loc[(dfpmt['Statut'] == 'SUCCESS') & (dfpmt['MOOV'] == 0)]
            trx_succes_abs, _n_before_date = filter_succes_abs_by_reco_date(
                trx_succes_abs,
                reco_start=getattr(self, 'reco_start', None),
                reco_end=getattr(self, 'reco_end', None),
                date_col='Date',
            )
            trx_en_attente_abs = dfpmt.loc[(dfpmt['Statut'] == 'PENDING') & (dfpmt['MOOV'] == 0)]
            trx_succes_cinetpay_abs_pmt = dfop_unique.loc[(dfop_unique['Transaction Status'] == 'Completed') & (dfop_unique['PMT'] == 0)]
            select_marchand = df_filteredpmt.groupby(['Pays', 'Merchant Name', 'Operator']).agg(
                Nombre=('Montant', 'count'),
                Volume_transaction=('Montant', 'sum')
            )
            
            select_country_marchand_statut = df_filteredpmt.groupby(['Pays']).agg(
                Nombre=('Montant', 'count'),
                Volume=('Montant', 'sum'))

            
            
            st.subheader("🔴 Transactions mettre à jour en SUCCESS")
            safe_show(maj_failed_a_succes)
            
            #st.subheader("🟡 Transactions PENDING à mettre à jour en SUCCESS")
            #safe_show(maj_pending_a_succes)
            
            st.subheader("🔵 Transactions en attente PMT absentes chez partenaire")
            safe_show(trx_en_attente_abs)
            
            st.subheader("🟠 Transactions SUCCES partenaire absentes PMT")
            safe_show(trx_succes_cinetpay_abs_pmt)
            
            st.subheader("🟢 Transactions SUCCES absentes chez partenaire")
            if getattr(self, 'reco_start', None) is not None or getattr(self, 'reco_end', None) is not None:
                _ds = self.reco_start.strftime('%d/%m/%Y') if getattr(self, 'reco_start', None) and hasattr(self.reco_start, 'strftime') else (self.reco_start or '…')
                _de = self.reco_end.strftime('%d/%m/%Y') if getattr(self, 'reco_end', None) and hasattr(self.reco_end, 'strftime') else (self.reco_end or '…')
                st.caption(
                    f"Filtrées sur la période de réconciliation : {_ds} → {_de}"
                    f" — {len(trx_succes_abs):,} ligne(s)"
                )
            safe_show(trx_succes_abs)

            st.subheader("🟤 TRANSACTION PAR OPERATEUR ET MARCHAND")
            safe_show(select_marchand)

            
            st.subheader("📊🔵 TRANSACTION PAR OPERATEUR ET PAYS")
            safe_show(select_country_marchand_statut)
        
        with tabs[2]:
            c_title1, c_title2 = st.columns(2)
            with c_title1:
                st.subheader("Vue globale par Statut")
            with c_title2:
                st.subheader("Vue globale par Pays")
            chart1, chart2 = st.columns(2)
            with chart1:
                # Agrégation obligatoire : évite RangeError Plotly sur gros volumes

                _pie_statut = dfpmt.groupby("Statut", as_index=False)["Montant"].sum()

                fig = px.pie(_pie_statut, values="Montant", names="Statut", template="plotly_white",
                             color_discrete_sequence=["#3070F0", "#5B9DFF", "#94B8F5", "#1A4FC4"])
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                                  paper_bgcolor="white", font=dict(color="#000000", size=12),
                                  showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5))
                fig.update_traces(textposition="inside", textfont_color="#000000")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with chart2:
                monthly_statut = dfpmt.groupby("Pays")["Montant"].sum().reset_index()
                fig_month = px.bar(monthly_statut, x="Pays", y="Montant", text_auto=True,
                                   color="Montant",
                                   color_continuous_scale=["#5B9DFF", "#3070F0"],
                                   template="plotly_white")
                fig_month.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                                        paper_bgcolor="white", plot_bgcolor="white",
                                        font=dict(color="#000000", size=12),
                                        coloraxis_showscale=False)
                st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})

        
        with tabs[3]:
            st.subheader("Analytics Avancés")
            

            # Analyse temporelle (défensive)
            try:
                # Analyse temporelle avancée
                st.subheader("Analyse Temporelle")
                dfpmt['Date'] = pd.to_datetime(dfpmt['Date'])
                #dfpmt['Jour'] = dfpmt['Date'].dt.day_name(locale='fr')
                dfpmt['Jour'] = dfpmt['Date'].dt.day_name().map({
                            'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                            'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
                 })


                dfpmt['Heure'] = pd.to_datetime(dfpmt['Created Date']).dt.hour
            
                col1, col2 = st.columns(2)
                with col1:
                    day_order = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                    by_day = dfpmt.groupby('Jour').agg({'Montant': 'sum', 'Transaction ID': 'count'}).reindex(day_order)
                    fig = px.line(by_day, x=by_day.index, y='Montant', 
                                 title="Volume par Jour de la Semaine",
                                 labels={'x': 'Jour', 'y': 'Montant'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    by_hour = dfpmt.groupby('Heure').agg({'Montant': 'sum', 'Transaction ID': 'count'})
                    fig = px.area(by_hour, x=by_hour.index, y='Montant', 
                                 title="Volume par Heure de la Journée",
                                 labels={'x': 'Heure', 'y': 'Montant'})
                    st.plotly_chart(fig, use_container_width=True)
        

        
            except Exception as _tmp_err:
                st.info(f"Analyse temporelle indisponible : {_tmp_err}")

            # --- V2.0 : modules RA (uniquement dans Analytics Avancés) ---
            try:
                from utils.ra_modules import render_ra_extra_modules
                render_ra_extra_modules(dfpmt, key_prefix="ra")
            except Exception as _ra_err:
                st.warning(f"Modules RA V2.0 non disponibles : {_ra_err}")

        # ========== RAPPORT FINAL EXCEL ==========
        try:
            from utils.report_helper import save_and_offer_report
            _loc = locals()

            def _safe_df(name):
                obj = _loc.get(name)
                if isinstance(obj, pd.DataFrame) and not obj.empty:
                    return obj
                return None

            _dfpmt = _safe_df("dfpmt")
            _filtered = _safe_df("df_filteredpmt")
            _total = int(_dfpmt.shape[0]) if _dfpmt is not None else 0
            _matched = int(_filtered.shape[0]) if _filtered is not None else 0
            _rate = round((_matched / _total * 100), 1) if _total else 0
            _montant = float(_dfpmt["Montant"].sum()) if _dfpmt is not None and "Montant" in _dfpmt.columns else 0.0

            _metrics = {
                "Total transactions PMT": _total,
                "Transactions Matchées PMT": _matched,
                "Taux de réconciliation (%)": _rate,
                "Date début": str(getattr(self, "reco_start", "") or ""),
                "Date fin": str(getattr(self, "reco_end", "") or ""),
                "Montant total": f"{_montant:,.2f}",
            }

            _sheets = {}
            for _name, _var in [
                ("TCD_PMT", "tcdpmt"),
                ("TCD_Partenaire", "tcdwave"),
                ("TCD_Partenaire", "tcdpartner"),
                ("TCD_Partenaire", "tcdcinetpay"),
                ("TCD_Partenaire", "tcdmoovci"),
                ("TCD_Partenaire", "tcdmtnci"),
                ("TCD_Partenaire", "tcdmtncm"),
                ("TCD_Partenaire", "tcdombf"),
                ("TCD_Partenaire", "tcdomci"),
                ("TCD_Partenaire", "tcdop"),
                ("MAJ_FAILED_to_SUCCESS", "maj_failed_a_succes"),
                ("MAJ_PENDING_to_SUCCESS", "maj_pending_a_succes"),
                ("SUCCESS_absents_partenaire", "trx_succes_abs"),
                ("PENDING_absents_partenaire", "trx_en_attente_abs"),
                ("SUCCESS_partenaire_absents_PMT", "trx_succes_cinetpay_abs_pmt"),
                ("Par_Marchand", "select_marchand"),
                ("Par_Pays", "select_country_marchand_statut"),
                ("Refound", "refound"),
                ("Recouvrement", "recouvrement"),
            ]:
                df = _safe_df(_var)
                if df is not None and _name not in _sheets:
                    # Limiter les très gros onglets pour Excel (max 100k lignes)
                    _sheets[_name] = df.head(100000)

            save_and_offer_report(
                partner_name=getattr(self, "_partner_label", "RECONCILIATION"),
                metrics=_metrics,
                sheets=_sheets,
                key_suffix=getattr(self, "_partner_label", "default").replace(" ", "_"),
                reco_start=getattr(self, "reco_start", None),
                reco_end=getattr(self, "reco_end", None),
            )
        except Exception as _e:
            st.warning(f"Rapport Excel non généré : {_e}")


        #Processed Cinetpay payin fin-