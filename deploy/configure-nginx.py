#!/usr/bin/env python3
"""Replace the static WLTraders nginx location with the analytics proxy.
Run as root on the server after git pull.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

SITE = Path("/etc/nginx/sites-available/wltraders-landing")
SNIPPET = Path(__file__).with_name("wltraders-analytics-nginx.conf")
STATIC_LOCATION = """    location / {
        try_files $uri $uri/ =404;
    }"""


def main() -> None:
    if not SITE.exists():
        raise SystemExit(f"nginx site not found: {SITE}")
    if not SNIPPET.exists():
        raise SystemExit(f"nginx snippet not found: {SNIPPET}")

    original = SITE.read_text(encoding="utf-8")
    proxy_config = textwrap.indent(SNIPPET.read_text(encoding="utf-8").strip(), "    ")
    if STATIC_LOCATION in original:
        updated = original.replace(STATIC_LOCATION, proxy_config, 1)
    elif "proxy_pass http://127.0.0.1:8090;" in original:
        print("nginx analytics proxy is already configured")
        return
    else:
        raise SystemExit("expected static location block was not found; no changes made")

    backup = SITE.with_suffix(SITE.suffix + ".pre-analytics")
    shutil.copy2(SITE, backup)
    SITE.write_text(updated, encoding="utf-8")
    check = subprocess.run(["nginx", "-t"], text=True, capture_output=True)
    if check.returncode:
        shutil.copy2(backup, SITE)
        sys.stderr.write(check.stderr)
        raise SystemExit("nginx configuration failed; the previous configuration was restored")
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
    print(f"nginx configured; backup: {backup}")


if __name__ == "__main__":
    main()
