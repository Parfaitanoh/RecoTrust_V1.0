# RecoTrust V5.1 — Changelog

**Date** : 2026-09-21  
**Type** : évolution production / multi-utilisateurs (non-régressive)

## Objectif

Préparer l'application pour une mise en production sur instance entreprise avec plusieurs utilisateurs simultanés, **sans modifier les règles métier, les processeurs partenaires, les calculs ni les résultats de réconciliation**.

## Modifications effectuées

### Configuration (`.streamlit/config.toml`)
- `maxUploadSize` / `maxMessageSize` : 10 Go → **4 Go** (stabilité mémoire multi-utilisateurs)
- `headless = true`
- `fileWatcherType = "none"` (stabilité CPU en production)
- `showErrorDetails = false` (ne pas exposer les traces techniques aux utilisateurs)
- Conservation : XSRF activé, CORS désactivé, thème PayMeTrust, fastReruns

### Validation (`auth/validators.py`)
- `MAX_UPLOAD_BYTES` aligné sur 1 Go (cohérent avec config.toml)

### Performance multi-utilisateurs (`utils/data_loader.py`)
- Réduction légère de `max_entries` des caches Streamlit (pression mémoire sous charge concurrente)
- **Aucune modification** de la logique de parsing CSV/Excel, détection séparateur/encodage, ou signatures des fonctions

### Dépendances (`requirements.txt`)
- Versions **pinées** pour reproductibilité en production

### Déploiement (nouveau dossier `deploy/`)
- `lancer_production.sh` — écoute 127.0.0.1, variables `RECOTRUST_*`
- `recotrust.service` — exemple unité systemd avec limites mémoire/CPU
- `nginx.example.conf` — reverse-proxy HTTPS, timeouts, limite body, headers sécurité

### Autres
- `.env.example` — documentation des variables d'environnement déjà supportées
- `main.py` — version affichée V5.1 uniquement (aucune logique métier touchée)
- README mis à jour (section production)


### Gestion mémoire Streamlit (V5.1 — complément)
- Caches DataFrame (`@st.cache_data`) limités à **4 entrées** / TTL 30 min (fichiers multi-Go)
- Caches en-têtes réduits (légers, plus d'entrées conservées)
- `prune_stale_file_bytes()` : ne conserve en session que les 2 fichiers actifs
- `release_heavy_session_artifacts()` : libère Excel / résultats hors navigation
- Appel automatique au **changement de fichiers** et à la **déconnexion**
- `gc.collect()` après purge complète
- **Aucune modification** de la logique de parsing ni des processeurs partenaires


### Persistance session au rafraîchissement (F5)
- **Comportement F5** : rester connecté + revenir à l'écran **chargement PMT / Partenaire**
- Ne pas renvoyer vers la page de connexion si `sid` valide
- Ne pas conserver la vue résultats après F5 (rechargement fichiers requis)

- Jeton opaque serveur `sid` (pas d'e-mail ni mot de passe) dans l'URL
- Sessions stockées sous `data/sessions/` (TTL 12 h glissant)
- Après F5 : restauration auto de la connexion + conservation des résultats
- Les fichiers uploadés Streamlit restent à recharger pour une **nouvelle** reco (limitation plateforme)
- Ne plus effacer `already_processed` / rapport Excel quand les uploaders sont vides après F5

## Zones strictement non modifiées

- Tous les fichiers sous `partenaires/`
- Calculs, matching, KPI, statuts
- `utils/excel_export.py`, `utils/ra_modules.py`, `utils/merchant_conversion.py`, `utils/match_config.py`
- Flux d'authentification et modèle de données utilisateurs
- Format et contenu métier des exports Excel

## Compatibilité

- Rétrocompatible avec les fichiers et workflows existants (tant que la taille des fichiers ≤ 4 Go)
- Si un partenaire produit réellement des fichiers > 4 Go : relever `maxUploadSize` et `MAX_UPLOAD_BYTES` (actuellement 4 Go) de façon coordonnée
