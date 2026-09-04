#!/usr/bin/env bash
# Run as root on the landing server from /var/www/wltraders.landing.
set -euo pipefail

install -Dm644 deploy/wltraders-analytics.service /etc/systemd/system/wltraders-analytics.service
systemctl daemon-reload
systemctl enable --now wltraders-analytics.service
systemctl restart wltraders-analytics.service
curl --fail --silent http://127.0.0.1:8090/health >/dev/null

echo 'Service is running. Add deploy/wltraders-analytics-nginx.conf directives'
echo 'inside the existing wltraders.pro HTTPS server block, then run:'
echo '  nginx -t && systemctl reload nginx'
echo 'Report over SSH: python3 /var/www/wltraders.landing/analytics_report.py'
