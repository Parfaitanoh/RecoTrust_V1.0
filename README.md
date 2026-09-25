# RecoTrust V5.1 — Application de Réconciliation Revenue Assurance

**PayMeTrust** · Revenue Assurance

---

## Nouveautés V5.1 (production + multi-utilisateurs)

- Configuration **production-ready** (upload 4 Go, headless, pas d'exposition des détails d'erreur)
- Limite d'upload alignée validation / Streamlit
- Dépendances **pinées**
- Scripts et exemples de déploiement (`deploy/`) : systemd, nginx, lancement local sécurisé
- Optimisation mémoire : caches DataFrame limités, purge automatique des uploads obsolètes, libération à la déconnexion
- **Aucune modification des règles métier, processeurs partenaires, calculs ou exports**

### Hérité de V4.0 / V3.0
- Page d'accueil Revenue Assurance
- Authentification e-mail + mot de passe (liste blanche, PBKDF2)
- Rôles USER / ADMIN + écran d'administration
- Validation centralisée, journalisation audit
- Aucun paramètre d'authentification dans l'URL
- Sessions isolées via `st.session_state`

---

## Lancement rapide (développement / LAN)

```bash
cd RECOTrust_V5.1.0
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

Ou scripts réseau existants :

```bash
./lancer_reseau.sh          # Linux / macOS
lancer_reseau.bat           # Windows
```

---

## Lancement production (recommandé)

```bash
# Écoute locale uniquement — placer derrière reverse-proxy HTTPS
./deploy/lancer_production.sh

# Ou avec variables :
export RECOTRUST_DATA_DIR=/var/lib/recotrust/data
export RECOTRUST_LOG_DIR=/var/log/recotrust
export RECOTRUST_HOST=127.0.0.1
export RECOTRUST_PORT=8501
./deploy/lancer_production.sh
```

Exemples fournis :
- `deploy/recotrust.service` — unité systemd
- `deploy/nginx.example.conf` — reverse-proxy HTTPS + limite body 4 Go + timeouts

Voir aussi `.env.example`.

---

## Connexion

1. Page d'accueil → **Connexion**
2. E-mail + mot de passe autorisés

**Mot de passe initial** (première initialisation uniquement) :

```
RecoTrust2026!
```

**À changer immédiatement** via l'écran Administration (rôle ADMIN).

| Email | Rôle |
|-------|------|
| parfait.ngoran@paymetrust.net | ADMIN |
| eliezer.tanoh@paymetrust.net | ADMIN |
| niamkey.nguessan@paymetrust.net | USER |
| pegard.kouadja@paymetrust.net | USER |
| joel.nando@paymetrust.net | USER |
| franck.ouraga@paymetrust.net | USER |

---

## Multi-utilisateurs

- Isolation native par session Streamlit (`st.session_state`)
- Cache fichiers partagé au niveau process (relecture rapide) avec `max_entries` dimensionnés pour limiter la RAM
- Pour plusieurs utilisateurs simultanés sur gros fichiers :
  - Reverse-proxy + éventuellement plusieurs workers + sticky sessions
  - Limites mémoire/CPU (systemd / Docker)
  - Surveiller la RAM du process Streamlit

---

## Architecture (rappel)

```
RECOTrust_V5.1.0/
├── main.py                 # Orchestration UI (pas de calcul métier)
├── auth/                   # Session, users, admin, audit, validators
├── partenaires/            # ★ Cœur métier — ne pas modifier sans justification
├── utils/                  # data_loader, exports, match_config, RA modules
├── styles/                 # Branding
├── data/                   # authorized_users.json (persistant)
├── logs/                   # recotrust_audit.log
├── deploy/                 # Production (systemd, nginx, launcher)
├── .streamlit/config.toml  # Config production
└── requirements.txt        # Versions pinées
```

---

## Support

revenu.assurance@paymetrust.net
