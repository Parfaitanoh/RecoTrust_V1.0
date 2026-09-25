# RecoTrust — Scaling multi-instances

## Objectif
Servir plusieurs utilisateurs et plusieurs réconciliations en parallèle en lançant
**plusieurs processus Streamlit** derrière nginx, sans réécrire le moteur métier.

## Architecture recommandée (même serveur)

```
Utilisateurs
    │ HTTPS
    ▼
  nginx (TLS, client_max_body_size 4096m)
    │ ip_hash / sticky
    ├────────────┬────────────┐
    ▼            ▼            ▼
 :8501        :8502        :8503
 Streamlit    Streamlit    Streamlit
    │            │            │
    └────────────┴────────────┘
                 │
     RECOTRUST_DATA_DIR partagé
     /var/lib/recotrust/data
       ├── authorized_users.json
       ├── sessions/
       └── reco_history.json
```

## Règles obligatoires

1. **Sticky session** (affinité)
   - Streamlit utilise WebSocket + état mémoire process.
   - Sans affinité, l’utilisateur peut perdre sa session entre deux requêtes.
   - nginx : `ip_hash` (voir `nginx.multi.example.conf`).

2. **Répertoire data partagé**
   ```bash
   export RECOTRUST_DATA_DIR=/var/lib/recotrust/data
   ```
   Contient :
   - `authorized_users.json` (comptes)
   - `sessions/` (sid F5)
   - `reco_history.json` (dashboard / historique)

3. **Même code / même venv**
   - Une seule arborescence `/opt/recotrust`
   - Plusieurs unités `recotrust@8501` … `recotrust@8503`

4. **Mémoire**
   - Chaque instance a son propre budget RAM (ex. `MemoryMax=4G`).
   - Gros fichiers (2–3 Go) : dimensionner `instances × charge` en conséquence.
   - Exemple 3 instances sur hôte 32 Go : OK pour usage mixte ; limiter les reco multi-Go simultanées.

## Installation rapide (3 instances)

```bash
sudo mkdir -p /var/lib/recotrust/data/sessions /var/log/recotrust
sudo chown -R recotrust:recotrust /var/lib/recotrust /var/log/recotrust

sudo cp deploy/recotrust@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now recotrust@8501
sudo systemctl enable --now recotrust@8502
sudo systemctl enable --now recotrust@8503

# nginx
sudo cp deploy/nginx.multi.example.conf /etc/nginx/sites-available/recotrust
# adapter certificats + server_name
sudo nginx -t && sudo systemctl reload nginx
```

Vérification :
```bash
systemctl status recotrust@8501 recotrust@8502 recotrust@8503
ss -lntp | grep 850
```

## Scaling sur plusieurs serveurs (horizontal)

| Besoin | Solution |
|--------|----------|
| Sessions sid + users + history | Stockage **partagé** (NFS, EFS, disque partagé) pour `RECOTRUST_DATA_DIR` |
| Affinité | LB cookie sticky ou ip_hash vers le même nœud |
| Fichiers uploadés en mémoire process | Restent locaux au process — sticky obligatoire pendant le traitement |
| Haute dispo | 2+ nœuds + shared data ; pas de sticky cross-node sans session store centralisé |

> Streamlit n’est pas un cluster applicatif natif. Le modèle sûr est :
> **sticky + data partagée + N processus**.

## Ce qui se scale bien

- Nombre d’utilisateurs connectés (navigation, dashboard)
- Réconciliations **en parallèle** (chaque instance traite les siennes)
- Isolation USER / ADMIN sur l’historique (fichier partagé)

## Ce qui ne se scale pas « gratuitement »

- Une seule reco très lourde (liée au CPU/RAM d’**une** instance)
- Partage du cache `@st.cache_data` entre processus (chaque instance a son cache)
- Absence de sticky (cassures WebSocket / F5)

## Dimensionnement indicatif

| Profil | Instances | RAM hôte | Notes |
|--------|-----------|----------|-------|
| Équipe 3–5 users, fichiers moyens | 2 | 16 Go | Confortable |
| 5–10 users, pics 2 Go | 3 | 32 Go | Sticky + monitoring RAM |
| Très gros volumes simultanés | 3–4 | 64 Go | Ou files d’attente (évolution future) |

## Monitoring

- RAM / CPU par process `streamlit`
- `journalctl -u recotrust@8501 -f`
- Taille `reco_history.json` et `sessions/`
- Codes 502/504 nginx (timeouts ou instance saturée)

## Rollback

```bash
sudo systemctl disable --now recotrust@8502 recotrust@8503
# revenir à une seule instance + nginx.example.conf (single upstream)
```
