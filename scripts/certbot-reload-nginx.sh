#!/bin/bash
# Certbot deploy hook: reload nginx container after cert renewal.
# Install on the host at: /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
# (symlink or copy this file there)

docker exec hms-nginx-prod nginx -s reload
