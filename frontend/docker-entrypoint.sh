#!/bin/sh
set -e

# API_BASE_URL est fourni par le Deployment Kubernetes.
# On le matérialise en JavaScript à chaque démarrage du conteneur.
# L'image reste ainsi indépendante de l'adresse de l'API.

: "${API_BASE_URL:?La variable d'environnement API_BASE_URL est requise}"

cat > /usr/share/nginx/html/config.js <<EOF2
window.API_BASE_URL = "${API_BASE_URL}";
EOF2

exec nginx -g "daemon off;"
