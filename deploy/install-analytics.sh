#!/usr/bin/env bash
# Run as root on the landing server from /opt/wltraders-landing.
set -euo pipefail

install -Dm644 deploy/wltraders-analytics.service /etc/systemd/system/wltraders-analytics.service
systemctl daemon-reload
systemctl enable --now wltraders-analytics.service
systemctl restart wltraders-analytics.service
curl --fail --silent http://127.0.0.1:8090/health >/dev/null
python3 deploy/configure-nginx.py

echo 'Service and nginx analytics proxy are running.'
echo 'Report over SSH: python3 /opt/wltraders-landing/analytics_report.py'
