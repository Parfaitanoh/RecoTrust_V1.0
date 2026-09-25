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
from datetime import datetime

class CinetpayPayoutProcessor:
    def __init__(self, data_file, partner_file, reco_start=None, reco_end=None,
                 match_col_pmt=None, match_col_partner=None):
        self.data_file = data_file
        self.partner_file = partner_file
        self.reco_start = reco_start
        self.reco_end = reco_end
        self.match_col_pmt = match_col_pmt
        self.match_col_partner = match_col_partner
        self._partner_label = "CINETPAY PAYOUT"


    def load_file(self, file, skiprows=0, **kwargs):
        """Chargement optimisé (cache Streamlit par contenu). Compatible skiprows (Moov, etc.)."""
        return load_dataframe(file, skiprows=skiprows, **kwargs)

    def process(self):
        # Charger les données
        pmt = self.load_file(self.data_file)
        dfop = self.load_file(self.partner_file)
        

        # V1.1 — colonnes de matching (surcharge utilisateur ou défaut V1.0)
        match_key_pmt = self.match_col_pmt or 'Transaction ID'
        match_key_partner = self.match_col_partner or 'ID Marchand'
        # Votre code de traitement existant pour Cinetpay
        # V1.2.0 — colonnes PMT conservées telles quelles (+ alias standard si besoin)
        dfpmt = prepare_pmt_dataframe(pmt)
        #Traitement partenaire----------------------------------------------
        dfop['Date'] = dfop['Date Création (GMT)'].apply(lambda x: x.split(' ')[0])
        new_rec= dfop.loc[(dfop['Statut'] == 'NEW') |(dfop['Statut'] == 'REC') ]
        rej= dfop.loc[(dfop['Statut'] == 'REJ')]
        
         #Traitement partenaire----------------------------------------------
        
        #MISE EN PLACE DE RECHERCHE X POUR RECUPERATION CHEZ LE PARTENAIRE
        correspondance_statut_op= dfop.set_index(match_key_partner)['Statut']
        correspondance_date_op = dfop.set_index(match_key_partner)['Date']
        correspondance_op = dfop.set_index(match_key_partner)['Opérateur']
        correspondance_idoperator = dfop.set_index(match_key_partner)['ID Operateur']
        
        dfpmt['DATEOP'] = dfpmt[match_key_pmt].map(correspondance_date_op)
        dfpmt['STATUTOP'] = dfpmt[match_key_pmt].map(correspondance_statut_op)
        dfpmt['OPERATOROP'] = dfpmt[match_key_pmt].map(correspondance_op)
        dfpmt['IDOPERATOR'] = dfpmt[match_key_pmt].map(correspondance_idoperator)
        
        # Définir les taux de commission pour chaque opérateur
        commission_rates = {
        'AIRTELCD' : 0.018,
        'MPESACD': 0.028,
        'MOOVBF': 0.01,
        'OMCD':	0.01,
        'OMML':	0.008,
        'MOOVML': 0.008,
        'OMBF':	0.01,
        'OM': 0.008,
        'FLOOZ': 0.007,
        'FLOOZTG': 0.0080,
        'TMONEYTG': 0.0080,
        'MOMO':	0.0050,
        'MLTEL': 0.0080
         

}
# Fonction pour calculer les frais d'opérateur
        def calculate_frais_op(row):
            operator = row['OPERATOROP']
            montant = row['Montant']
            commission_rate = commission_rates.get(operator, 0)
            return montant * commission_rate
        
        # Ajouter une colonne 'frais_op' avec les frais d'opérateur calculés
        dfpmt['frais_op'] = dfpmt.apply(calculate_frais_op, axis=1)
        val= dfop.loc[(dfop['Statut'] == 'VAL')]
        
        # Ajouter une colonne 'frais_op' avec les frais d'opérateur calculés
        dfpmt['Frais_pmt'] = dfpmt['Fee amount'] - dfpmt['frais_op']
        dfpmt['Nombre']= dfpmt['Montant']
        val['Nombre']=val['Montant Envoyé']
        #NBSI PMT &CINETPAY
        dfpmt['CINETPAY'] = dfpmt[match_key_pmt].isin(val[match_key_partner]).astype(int)
        val['PMT'] = val[match_key_partner].isin(dfpmt[match_key_pmt]).astype(int)
        dfpmt['NEW_REC'] = dfpmt[match_key_pmt].isin(new_rec[match_key_partner]).astype(int)
        dfpmt['REJ'] = dfpmt[match_key_pmt].isin(rej[match_key_partner]).astype(int)
        # --- Création des onglets ---

        tabs = st.tabs(["📊 Vue Globale", "👥 Rapport Reconciliation", "🔄 Rapport", "📈 Analytics Avancés"])
    
            # ==================================
               # Onglet 1 : Vue Globale
           # ==================================
        with tabs[0]:
            st.subheader("Vue Globale")
            #Nouveau: Sélecteur de période

            # Calcul des KPI
            montant_total = dfpmt["Montant"].sum()
            nombre_transaction = dfpmt[match_key_pmt].count()
            taux_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'].shape[0] / nombre_transaction) * 100
            trx_succes = (dfpmt[dfpmt['Statut'] == 'SUCCESS'])
            select=trx_succes['Transaction ID'].count()

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
    # Onglet 2  : Rapport Reconciliation CINETPAY PAYOUT
# ================================

        with tabs[1]:
            st.subheader("Rapport Reconciliation CINETPAY PAYOUT")
            df_filteredpmt = dfpmt[dfpmt['CINETPAY'] == 1]
            maj=df_filteredpmt[df_filteredpmt['Statut']=='PENDING']
            # Nouveau: Métriques de réconciliation
            matched = df_filteredpmt['CINETPAY'].sum()
            nbre_maj=maj['Transaction ID'].count()
            unmatched = len(dfpmt) - matched
            try:
                matched_part = int(val['PMT'].sum())
            except Exception:
                matched_part = int((val['PMT'] == 1).sum()) if hasattr(val, '__len__') else 0
            reconciliation_rate = (matched / len(dfpmt)) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Transactions Matchées PMT", matched, delta=f"{reconciliation_rate:.1f}%")
            col2.metric("Total Transactions", len(dfpmt))
            col3.metric("Nombre transaction MAJ", nbre_maj)
            col4.metric("Transactions Matchées Part", matched_part)

            

# Création du tableau croisé dynamique
            tcdpmt = pd.pivot_table(
            df_filteredpmt,
            values=['Montant', 'Nombre','frais_op', 'Frais_pmt'],
            index=['Date', 'OPERATOROP','Statut'],
            aggfunc={'Nombre': 'count','Montant': 'sum' ,'frais_op': 'sum', 'Frais_pmt': 'sum' },
            fill_value=0,
            margins=True,
            margins_name='Total')
            
# Création du tableau croisé dynamique partenaire
            df_filtered = val[(val['PMT'] == 1) | (val['PMT'] == 0)]
            tcdcinetpay = pd.pivot_table(
            df_filtered,
            values=['Montant Envoyé', 'Nombre'],
            index=['Date', 'Opérateur','Statut'],
            aggfunc={'Nombre': 'count','Montant Envoyé': 'sum' },
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
            
            # Affichage avec onglets
            tab1, tab2, tab3, tab4 = st.tabs(["Données PMT", "Données Partenaire", "TCD PMT", "TCD Partenaire"])
            
            with tab1:
                safe_show(dfpmt)
                
            with tab2:
                st.write(dfop)
                
            with tab3:
                safe_show(tcdpmt)
                
            with tab4:
                st.write(tcdcinetpay)
            
            # LES TRANSACTIONS A METTRE A JOUR
            
            pertes = dfpmt.loc[(dfpmt['Statut'] == 'FAILED') & (dfpmt['CINETPAY'] == 1)]
            maj_pending_a_succes = dfpmt.loc[(dfpmt['Statut'] == 'PENDING') & (dfpmt['CINETPAY'] == 1)]
            majp=maj_pending_a_succes[['Transaction ID','Phone Number','Statut','STATUTOP','IDOPERATOR']]
            trx_succes_abs = dfpmt.loc[(dfpmt['Statut'] == 'SUCCESS') & (dfpmt['CINETPAY'] == 0)]
            trx_succes_abs, _n_before_date = filter_succes_abs_by_reco_date(
                trx_succes_abs,
                reco_start=getattr(self, 'reco_start', None),
                reco_end=getattr(self, 'reco_end', None),
                date_col='Date',
            )
            trx_en_attente_abs= dfpmt.loc[(dfpmt['Statut']=='PENDING') & (dfpmt['CINETPAY'] == 0)]
            trx_succes_cinetpay_abs_pmt = val.loc[(val['Statut']=='ACCEPTED') & (val['PMT'] == 0)]
            
            select_marchand=df_filteredpmt.groupby(['Pays','Merchant Name','Operator']).agg(
                Nombre=('Montant', 'count'),
                Volume_transaction=('Montant','sum')
            )
            
            select_country_marchand_statut = df_filteredpmt.groupby(['Pays']).agg(
                Nombre=('Montant', 'count'),
                Volume=('Montant', 'sum')
            )
            # Affichage avec expanders
            with st.expander("🔴 Pertes", expanded=False):
                st.dataframe(pertes)
                st.download_button(
                    label="Télécharger ces données",
                    data=pertes.to_csv(index=False).encode('utf-8'),
                    file_name='failed_to_success.csv',
                    mime='text/csv'
                )
                
            with st.expander("🟡 Transactions PENDING à mettre à jour en SUCCESS"):
                st.dataframe(maj_pending_a_succes)
                
            with st.expander("🔵 Transactions en attente PMT absentes chez partenaire"):
                st.dataframe(trx_en_attente_abs)
                
            with st.expander("🟢 Transactions SUCCES absentes chez partenaire"):
                if getattr(self, 'reco_start', None) is not None or getattr(self, 'reco_end', None) is not None:
                    _ds = self.reco_start.strftime('%d/%m/%Y') if getattr(self, 'reco_start', None) and hasattr(self.reco_start, 'strftime') else (self.reco_start or '…')
                    _de = self.reco_end.strftime('%d/%m/%Y') if getattr(self, 'reco_end', None) and hasattr(self.reco_end, 'strftime') else (self.reco_end or '…')
                    st.caption(
                        f"Filtrées sur la période de réconciliation : {_ds} → {_de}"
                        f" — {len(trx_succes_abs):,} ligne(s)"
                    )
                st.dataframe(trx_succes_abs)

            with st.expander("🟠 Transactions SUCCES partenaire absentes PMT"):
                st.dataframe(trx_succes_cinetpay_abs_pmt)
            
            # Analyse par marchand et pays
            st.subheader("Analyse par Segment")
            select_marchand=df_filteredpmt.groupby(['Pays','Merchant Name','Operator']).agg(
                Nombre=('Montant', 'count'),
                Volume_transaction=('Montant','sum')
            ).reset_index()
            
            select_country_marchand_statut = df_filteredpmt.groupby(['Pays']).agg(
                Nombre=('Montant', 'count'),
                Volume=('Montant', 'sum')
            ).reset_index()
            
            # Graphiques interactifs
            col1, col2 = st.columns(2)
            with col1:
                fig = px.treemap(select_marchand, 
                                path=['Pays', 'Operator', 'Merchant Name'], 
                                values='Volume_transaction',
                                title='Répartition par Pays/Opérateur/Marchand')
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                fig = px.bar(select_country_marchand_statut, 
                            x='Pays', y='Volume',
                            text='Volume',
                            title='Volume par Pays')
                fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)



            # ================================
        # Onglet 3 : Rapport
        # ================================
        with tabs[2]:
            st.subheader('Analyse par Statut et Pays')
            
            col1, col2 = st.columns(2)
            with col1:
                # Agrégation obligatoire : évite RangeError Plotly sur gros volumes

                _pie_statut = dfpmt.groupby("Statut", as_index=False)["Montant"].sum()

                fig = px.pie(_pie_statut, values="Montant", names="Statut", 
                           template="plotly_white", hole=0.4,
                           title="Répartition par Statut")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="white", font=dict(color="#000000", size=12))
                fig.update_traces(textinfo='percent+label', pull=[0.1, 0, 0])
                st.plotly_chart(fig,use_container_width=True)
                
            with col2:
                monthly_statut = dfpmt.groupby("Pays")["Montant"].sum().reset_index()
                fig_month = px.bar(monthly_statut, x="Pays", y="Montant",
                                  text_auto='.2s',
                                  color="Montant",
                                  color_continuous_scale=["#1E90FF", "#4682B4"],
                                  title="Volume par Pays")
                fig_month.update_layout(height=400)
                fig_month.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
                st.plotly_chart(fig_month, use_container_width=True)
            
            # Heatmap des transactions
            st.subheader("Heatmap des Transactions")
            heatmap_data = dfpmt.groupby(['Operator', 'Statut']).size().unstack().fillna(0)
            fig = px.imshow(heatmap_data,
                          labels=dict(x="Statut", y="Opérateur", color="Nombre"),
                          aspect="auto",
                          color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)


            # ================================
        # Onglet 4 : Analytics Avancés
        # ================================
        with tabs[3]:
            st.subheader("Analytics Avancés")
            
            # Analyse des frais
            
            
            # Analyse temporelle (défensive)
            try:
                # Analyse temporelle avancée
                st.subheader("Analyse Temporelle")
                dfpmt['Date'] = pd.to_datetime(dfpmt['Date'])
                dfpmt['Jour'] = dfpmt['Date'].dt.day_name(locale='fr')
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
            
                # Nouveau: Téléchargement des rapports

        
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


