#!/bin/bash
# Redeploy web/ + exports/ to the always-on freedaiy (thebeast-1) box, publicly
# served at https://freedaiy.tail25e0dd.ts.net:8443/ via Tailscale Funnel.
#
# Run this any time web/ or exports/ change. The remote static file server
# (systemd --user unit `museum-of-sam.service`, Caddy file-server on
# 127.0.0.1:4300) picks up new files immediately — no restart needed unless
# you change the service definition itself. Tailscale serve/funnel config on
# port 8443 is untouched by this script.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "--- syncing web/ ---"
rsync -az --progress -e ssh web/ steve@freedaiy:~/museum-of-sam-deploy/

echo "--- syncing exports/ into deploy/exports ---"
rsync -az --progress -e ssh exports/ steve@freedaiy:~/museum-of-sam-deploy/exports/

echo "--- fixing ../exports/ -> ./exports/ in the deployed index.html (deploy root has exports/ nested inside it, not a sibling) ---"
ssh steve@freedaiy 'sed -i "s#\.\./exports/#./exports/#g" ~/museum-of-sam-deploy/index.html'

echo "--- verifying ---"
ssh steve@freedaiy '
curl -s -o /dev/null -w "root -> %{http_code}\n" http://127.0.0.1:4300/
curl -s -o /dev/null -w "manifest -> %{http_code}\n" http://127.0.0.1:4300/artwork/chaz-manifest.json
'
echo "Done. Live at https://freedaiy.tail25e0dd.ts.net:8443/"
