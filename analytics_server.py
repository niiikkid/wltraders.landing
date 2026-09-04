#!/usr/bin/env python3
"""WLTraders landing: static site server with private visitor analytics.

Run only behind nginx. nginx must pass the client IP from Cloudflare in
X-Real-IP and this process must remain bound to 127.0.0.1.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import os
import re
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

BOT_PATTERN = re.compile(
    r"bot|crawler|spider|slurp|bingpreview|facebookexternalhit|"
    r"telegrambot|discordbot|whatsapp|vkshare|yandex|google-inspectiontool|"
    r"headless|lighthouse|pagespeed|curl|wget|python-requests|axios",
    re.IGNORECASE,
)

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("ANALYTICS_DB", "/var/lib/wltraders-analytics/visitors.sqlite3"))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def database() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS unique_visitors (
            kind TEXT NOT NULL CHECK(kind IN ('human', 'bot')),
            ip TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            visits INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (kind, ip)
        );
        CREATE TABLE IF NOT EXISTS visit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seen_at TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('human', 'bot')),
            ip TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            user_agent TEXT NOT NULL,
            referer TEXT NOT NULL,
            accept_language TEXT NOT NULL,
            cf_country TEXT NOT NULL,
            cf_city TEXT NOT NULL,
            cf_timezone TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS visit_log_seen_at_idx ON visit_log(seen_at DESC);
        CREATE INDEX IF NOT EXISTS visit_log_kind_seen_at_idx ON visit_log(kind, seen_at DESC);
        """
    )
    return conn


def client_ip(handler: SimpleHTTPRequestHandler) -> str:
    # X-Real-IP is supplied by localhost nginx, not trusted from public traffic.
    candidate = handler.headers.get("X-Real-IP", handler.client_address[0]).strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return handler.client_address[0]


def visitor_kind(user_agent: str) -> str:
    return "bot" if not user_agent or BOT_PATTERN.search(user_agent) else "human"


def record_visit(handler: SimpleHTTPRequestHandler) -> None:
    ip = client_ip(handler)
    user_agent = handler.headers.get("User-Agent", "")[:1000]
    kind = visitor_kind(user_agent)
    now = utc_now()
    details = (
        now, kind, ip, handler.command, handler.path[:2048], user_agent,
        handler.headers.get("Referer", "")[:2048],
        handler.headers.get("Accept-Language", "")[:255],
        handler.headers.get("CF-IPCountry", "")[:16],
        handler.headers.get("CF-IPCity", "")[:255],
        handler.headers.get("CF-Timezone", "")[:255],
    )
    with database() as conn:
        conn.execute(
            """INSERT INTO unique_visitors(kind, ip, first_seen_at, last_seen_at, visits)
               VALUES (?, ?, ?, ?, 1)
               ON CONFLICT(kind, ip) DO UPDATE SET
                   last_seen_at=excluded.last_seen_at, visits=unique_visitors.visits + 1""",
            (kind, ip, now, now),
        )
        conn.execute(
            """INSERT INTO visit_log(
                 seen_at, kind, ip, method, path, user_agent, referer,
                 accept_language, cf_country, cf_city, cf_timezone
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            details,
        )


def summary() -> dict[str, Any]:
    with database() as conn:
        counters = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM unique_visitors GROUP BY kind"
        ).fetchall())
        latest = conn.execute(
            """SELECT seen_at, kind, ip, path, user_agent, referer,
                      accept_language, cf_country, cf_city, cf_timezone
               FROM visit_log ORDER BY id DESC LIMIT 50"""
        ).fetchall()
    fields = ["seen_at", "kind", "ip", "path", "user_agent", "referer",
              "accept_language", "cf_country", "cf_city", "cf_timezone"]
    return {
        "unique_visitors": {"humans": counters.get("human", 0), "bots": counters.get("bot", 0)},
        "latest_visits": [dict(zip(fields, row)) for row in latest],
    }


class LandingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        # nginx owns access logs; analytics data is stored in SQLite.
        return

    def do_GET(self) -> None:
        if self.path == "/analytics-summary":
            if not ipaddress.ip_address(self.client_address[0]).is_loopback:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            payload = json.dumps(summary(), ensure_ascii=False, indent=2).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/health":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        # One page-view per document request. Assets are intentionally excluded.
        if self.path in ("/", "/index.html"):
            record_visit(self)
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LandingHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
