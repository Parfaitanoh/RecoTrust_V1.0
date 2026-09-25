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

class WaveciPayinProcessor:
    def __init__(self, data_file, partner_file, reco_start=None, reco_end=None,
                 match_col_pmt=None, match_col_partner=None):
        self.data_file = data_file
        self.partner_file = partner_file
        self.reco_start = reco_start
        self.reco_end = reco_end
        self.match_col_pmt = match_col_pmt
        self.match_col_partner = match_col_partner
        self._partner_label = "WAVE CI PAYIN"


    def load_file(self, file, skiprows=0, **kwargs):
        """Chargement optimisé (cache Streamlit par contenu). Compatible skiprows (Moov, etc.)."""
        return load_dataframe(file, skiprows=skiprows, **kwargs)

    def process(self):
        # Charger les données
        pmt = self.load_file(self.data_file)
        dfop = self.load_file(self.partner_file)
        

        # V1.1 — colonnes de matching (surcharge utilisateur ou défaut V1.0)
        match_key_pmt = self.match_col_pmt or 'Transaction ID'
        match_key_partner = self.match_col_partner or 'Référence client'
        # traitement mtnci payin
        
        # V1.2.0 — colonnes PMT conservées telles quelles (+ alias standard si besoin)
        dfpmt = prepare_pmt_dataframe(pmt)
        # --- Nettoyage & transformation CHEZ LE PARTENAIRE-------------------------------
        def extractdays(dateds):
            parts=dateds.split('T')
            return parts[0]
        dfop['DateCourte']= dfop['Horodatage'].apply(extractdays)
        
        
        payin= dfop.loc[(dfop['Type de transaction'] == 'api_checkout')]

        
         # Calcul des KPI------------------------------------
        
         # Calcul des KPI-----------------------------------------
        
        #MISE EN PLACE DE RECHERCHE X POUR RECUPERATION CHEZ LE PARTENAIRE
        # Supprimer les doublons en conservant la première occurrence
        payin = payin.drop_duplicates(subset=match_key_partner)
        
        # Vérification des correspondances entre A1 et B1
        #correspondance_statut_op= payin.set_index('Externalid')['Status']
        correspondance_date_op = payin.set_index(match_key_partner)['DateCourte']
        correspondance_idoperator = payin.set_index(match_key_partner)['Identifiant de session API']
        
        
        dfpmt['DATEOP'] = dfpmt[match_key_pmt].map(correspondance_date_op)
        #dfpmt['STATUTOP'] = dfpmt[match_key_pmt].map(correspondance_statut_op)
        dfpmt['IDOPERATOR'] = dfpmt[match_key_pmt].map(correspondance_idoperator)
                
        
        # Définir les taux de commission pour chaque opérateur
        dfpmt['Fraisop'] = dfpmt['Montant'] * 0.01
        dfpmt['FraisPmt'] = dfpmt['Fee amount'] - dfpmt['Fraisop']
        dfpmt['Tauxop']=dfpmt['Fraisop'] / dfpmt['Montant']
        payin['Tauxop']=payin['Frais'] / payin['Montant']

        payin['Net']=payin['Montant'] + payin['Frais']
        payin['Taux(%)']=payin['Frais'] / payin['Net']
        select_taux=payin.groupby(['Type de transaction']).agg(
            Taux=('Taux(%)', 'mean')
        )

        #NBSI PMT &CINETPAY
        dfpmt['WAVE'] = dfpmt[match_key_pmt].isin(payin[match_key_partner]).astype(int)
        payin['PMT'] = payin[match_key_partner].isin(dfpmt[match_key_pmt]).astype(int)

        dfpmt['Nombre']= dfpmt['Montant']
        payin['Nombre']= payin['Montant']

        # --- Création des onglets ---

        tabs = st.tabs(["📊 Vue Globale", "👥 Rapport Reconciliation", "🔄 Rapport", "📈 Analytics Avancés"])
    
            # ==================================
               # Onglet 1 : Vue Globale
           # ==================================
        with tabs[0]:
            st.subheader("Vue Globale")
            #Sélecteur de période
            montant_total = dfpmt["Montant"].sum()
            nombre_transaction = dfpmt[match_key_pmt].count()
            taux_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'].shape[0] / nombre_transaction) * 100
            trx_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'])
            select=trx_succes['Transaction ID'].count()

            # Affichage dans des metric cards améliorées
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(metric_card("Transactions", nombre_transaction, "#3070F0", "🔄"), unsafe_allow_html=True)
            col2.markdown(metric_card("Transactions Succès", select, "#3070F0", "🔄"), unsafe_allow_html=True)
            col3.markdown(metric_card("Montant Total", f"{montant_total:,.1f}", "#3070F0", "💰"), unsafe_allow_html=True)
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

        with tabs[1]:
            
            st.subheader("Rapport Reconciliation WAVE CI PAYIN")
            df_filteredpmt = dfpmt[dfpmt['WAVE'] == 1]
            
            # Nouveau: Métriques de réconciliation
            matched = df_filteredpmt['WAVE'].sum()
            unmatched = len(dfpmt) - matched
            try:
                matched_part = int(payin['PMT'].sum())
            except Exception:
                matched_part = int((payin['PMT'] == 1).sum()) if hasattr(payin, '__len__') else 0
            reconciliation_rate = (matched / len(dfpmt)) * 100
            maj=df_filteredpmt[(df_filteredpmt['Statut']=='FAILED') | (df_filteredpmt['Statut']=='PENDING')]
            nbre_maj=maj['Transaction ID'].count()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Transactions Matchées PMT", matched, delta=f"{reconciliation_rate:.1f}%")
            col2.metric("Total Transactions", len(dfpmt))
            col3.metric("Nombre transaction MAJ", nbre_maj)
            col4.metric("Transactions Matchées Part", matched_part)
            # Création du tableau croisé dynamique
            df_filteredpmt = dfpmt[dfpmt['WAVE'] == 1]
        # Création du tableau croisé dynamique
            tcdpmt = pd.pivot_table(
            df_filteredpmt,
            values=['Montant', 'Nombre'],
            index=['DATEOP','Statut'],
            aggfunc={'Nombre': 'count','Montant': 'sum' },
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
            # Création du tableau croisé dynamique
            df_filtered = payin[(payin['PMT'] == 1) | (payin['PMT'] == 0)]

        # Création du tableau croisé dynamique
            tcdwave = pd.pivot_table(
            df_filtered,
            values=['Nombre', 'Net'],
            index=['DateCourte'],
            aggfunc={'Nombre': 'count','Net': 'sum' },
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
            tab1, tab2, tab3, tab4,tab5 = st.tabs(["Données PMT", "Données Partenaire", "TCD PMT", "TCD Partenaire","Taux(%)"])
            
            with tab1:
                safe_show(dfpmt)
                
            with tab2:
                safe_show(payin)
                
            with tab3:
                safe_show(tcdpmt)
                
            with tab4:
                safe_show(tcdwave)

            with tab5:
                safe_show(select_taux)
            
            # LES TRANSACTIONS A METTRE A JOUR
            
            maj_failed_a_succes = dfpmt.loc[(dfpmt['Statut'] != 'SUCCESS') & (dfpmt['WAVE'] == 1)]
            #maj_pending_a_succes = dfpmt.loc[(dfpmt['Statut'] == 'PENDING') & (dfpmt['WAVE'] == 1)]
            trx_succes_abs = dfpmt.loc[(dfpmt['Statut'] == 'SUCCESS') & (dfpmt['WAVE'] == 0)]
            trx_succes_abs, _n_before_date = filter_succes_abs_by_reco_date(
                trx_succes_abs,
                reco_start=getattr(self, 'reco_start', None),
                reco_end=getattr(self, 'reco_end', None),
                date_col='Date',
            )
            trx_en_attente_abs= dfpmt.loc[(dfpmt['Statut']=='PENDING') & (dfpmt['WAVE'] == 0)]
            trx_succes_cinetpay_abs_pmt = payin.loc[(payin['PMT'] == 0)]
            select_marchand=df_filteredpmt.groupby(['Pays','Merchant Name','Operator']).agg(
                Nombre=('Montant', 'count'),
                Volume_transaction=('Montant','sum')
            )
            
            select_country_marchand_statut = df_filteredpmt.groupby(['Pays']).agg(
                Nombre=('Montant', 'count'),
                Volume=('Montant', 'sum')
            )
            

            refound=dfop[dfop['Type de transaction']=='api_payout_reversal']
            recouvrement=dfop[dfop['Type de transaction']=='agent_transaction']
            
            st.subheader("🔴 Transactions à mettre à jour en SUCCESS")
            safe_show(maj_failed_a_succes)
            
            #st.subheader("🟡 Transactions PENDING à mettre à jour en SUCCESS")
            #safe_show(maj_pending_a_succes)
            
            st.subheader("🔵 Transactions en attente PMT absentes chez partenaire")
            safe_show(trx_en_attente_abs)
            
            st.subheader("🟢 Transactions SUCCES partenaire absentes chez PMT ")
            safe_show(trx_succes_cinetpay_abs_pmt)
            
            st.subheader("🟠 Transactions SUCCES PMT absentes chez partenaire")
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

            st.subheader("🟩 RETOUR DE FONDS (REFOUND)")
            safe_show(refound)
            
            st.subheader("📊🔵 RECOUVREMENT")
            safe_show(recouvrement)
            
            st.subheader("🔵 TRANSACTION PAR OPERATEUR ET PAYS")
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