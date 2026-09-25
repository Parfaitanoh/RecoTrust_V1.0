#!/usr/bin/env bash
# PayMeTrust Reconciliation — lancement accessible sur le réseau local
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8501}"

# --- Détection IP locale (IPv4 privée) ---
detect_ip() {
  local ip=""
  if command -v ip >/dev/null 2>&1; then
    ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
  fi
  if [ -z "$ip" ] && command -v hostname >/dev/null 2>&1; then
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  fi
  if [ -z "$ip" ]; then
    ip=$(ifconfig 2>/dev/null | awk '/inet / && $2 !~ /^127\./ {print $2; exit}' | sed 's/addr://')
  fi
  echo "${ip:-INTROUVABLE}"
}

LOCAL_IP=$(detect_ip)
URL="http://${LOCAL_IP}:${PORT}"

echo ""
echo "============================================"
echo "  PayMeTrust Reconciliation — Mode réseau"
echo "============================================"
echo ""
echo "  Votre adresse IP locale : ${LOCAL_IP}"
echo ""
echo "  --------------------------------------------"
echo "   Lien à partager aux collègues :"
echo ""
echo "      ${URL}"
echo ""
echo "  --------------------------------------------"
echo ""
echo "  Conditions :"
echo "   - Ce terminal reste ouvert (app en cours)"
echo "   - Collègues sur le MÊME réseau Wi‑Fi / Ethernet"
echo "   - Pare-feu : autoriser le port ${PORT} si besoin"
echo ""
echo "  Connexion app : email @paymetrust.net"
echo ""
echo "  Démarrage de Streamlit..."
echo "  (Ctrl+C pour arrêter)"
echo ""

# macOS : tentative d'ouverture du pare-feu (souvent sans effet sans droits admin)
if [[ "$(uname)" == "Darwin" ]]; then
  :
fi

exec streamlit run main.py --server.address 0.0.0.0 --server.port "${PORT}"
