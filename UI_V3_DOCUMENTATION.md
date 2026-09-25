# RecoTrust V3 — Interface utilisateur

## Principe
Couche UI additive (`ui/`, styles V3). **Aucun** changement des processeurs `partenaires/*` ni des calculs.

## Navigation
- **Dashboard** : KPI et liste issus de `data/reco_history.json` (métadonnées d'exécution)
- **Nouvelle réconciliation** : flux historique (upload → config/matching → résultats)
- **Historique** : recherche / filtres sur les exécutions passées
- **Administration** (ADMIN) : inchangé

## Historique
Écrit à chaque fin de traitement (`completed` / `failed`) via `ui/history_store.py`.
Ne contient **pas** de transactions ni de montants métier — uniquement paramètres d'exécution.

## Design system
Classes CSS préfixées `rt-*` injectées par `load_v3_css()` (cartes KPI, stepper, badges).

## Non-régression métier
Les appels `get_processor(...).process()` et les modules partenaires restent identiques.
