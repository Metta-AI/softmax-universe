#!/usr/bin/env python3
"""Serve the game service UI with a simple API backed by SQLite."""

import json
import os
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

DATA_DIR = os.path.join(os.path.expanduser("~"), ".softmax-universe")
DB_PATH = os.path.join(DATA_DIR, "ontology.db")
UI_PATH = os.path.join(os.path.dirname(__file__), "ui.html")

RANK_PLAYERS_SQL = """
    WITH best_player_ranks AS (
        SELECT r.division_id, rr.round_id, pv.player_id, MIN(rr.rank) AS rank
        FROM round_results rr
        JOIN rounds r ON rr.round_id = r.id
        JOIN policy_versions pv ON rr.policy_version_id = pv.id
        GROUP BY r.division_id, rr.round_id, pv.player_id
    )
    SELECT bpr.*, p.name as player_name, u.name as user_name, p.user_id,
           d.name as division_name, d.league_id, l.name as league_name
    FROM best_player_ranks bpr
    JOIN players p ON bpr.player_id = p.id
    JOIN users u ON p.user_id = u.id
    JOIN divisions d ON bpr.division_id = d.id
    JOIN leagues l ON d.league_id = l.id
    ORDER BY d.league_id, bpr.round_id DESC, bpr.rank, bpr.player_id
"""

RANK_USERS_SQL = """
    WITH best_user_ranks AS (
        SELECT r.division_id, rr.round_id, p.user_id, MIN(rr.rank) AS rank
        FROM round_results rr
        JOIN rounds r ON rr.round_id = r.id
        JOIN policy_versions pv ON rr.policy_version_id = pv.id
        JOIN players p ON pv.player_id = p.id
        GROUP BY r.division_id, rr.round_id, p.user_id
    )
    SELECT bur.*, u.name as user_name,
           d.name as division_name, d.league_id, l.name as league_name
    FROM best_user_ranks bur
    JOIN users u ON bur.user_id = u.id
    JOIN divisions d ON bur.division_id = d.id
    JOIN leagues l ON d.league_id = l.id
    ORDER BY d.league_id, bur.round_id DESC, bur.rank, bur.user_id
"""


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def mutate(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def read_schema():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    tables = []
    table_names = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    for table_row in table_names:
        table_name = table_row["name"]
        quoted_name = quote_identifier(table_name)
        columns = [dict(row) for row in conn.execute(f"PRAGMA table_info({quoted_name})").fetchall()]
        columns_by_name = {column["name"]: column for column in columns}
        foreign_keys = []
        for fk in conn.execute(f"PRAGMA foreign_key_list({quoted_name})").fetchall():
            foreign_key = dict(fk)
            column = columns_by_name.get(foreign_key["from"], {})
            foreign_key["optional"] = not bool(column.get("notnull") or column.get("pk"))
            foreign_keys.append(foreign_key)
        row_count = conn.execute(f"SELECT COUNT(*) AS count FROM {quoted_name}").fetchone()["count"]
        tables.append({
            "name": table_name,
            "row_count": row_count,
            "columns": columns,
            "foreign_keys": foreign_keys,
        })

    conn.close()
    return {"tables": tables}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path.startswith("/api/"):
            data = self.handle_api(path)
            if data is not None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
                return

        # Serve UI for all non-API routes (SPA fallback)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(UI_PATH, "rb") as f:
            self.wfile.write(f.read())

    def handle_api(self, path):
        if path == "/api/schema":
            return read_schema()
        if path == "/api/users":
            return query("SELECT * FROM users")
        if path == "/api/players":
            return query("""
                SELECT p.*, u.name as user_name
                FROM players p JOIN users u ON p.user_id = u.id
            """)
        if path == "/api/policy_versions":
            return query("""
                SELECT pv.*, p.name as player_name, u.name as user_name
                FROM policy_versions pv
                JOIN players p ON pv.player_id = p.id
                JOIN users u ON p.user_id = u.id
            """)
        if path == "/api/games":
            return query("""
                SELECT g.*, u.name as owner_name
                FROM games g JOIN users u ON g.owner_id = u.id
            """)
        if path == "/api/mods":
            return query("""
                SELECT m.*, g.name as game_name, u.name as owner_name
                FROM mods m
                JOIN games g ON m.game_id = g.id
                JOIN users u ON m.owner_id = u.id
            """)
        if path == "/api/leagues":
            return query("""
                SELECT l.*, g.name as game_name, m.name as mod_name
                FROM leagues l
                JOIN games g ON l.game_id = g.id
                JOIN mods m ON l.mod_id = m.id
            """)
        if path == "/api/divisions":
            return query("""
                SELECT d.*, l.name as league_name, g.name as game_name
                FROM divisions d
                JOIN leagues l ON d.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/submissions":
            return query("""
                SELECT s.*, pv.name as policy_version_name, l.name as league_name,
                       g.name as game_name, p.name as player_name, p.id as player_id
                FROM submissions s
                JOIN policy_versions pv ON s.policy_version_id = pv.id
                JOIN players p ON pv.player_id = p.id
                JOIN leagues l ON s.league_id = l.id
                JOIN games g ON l.game_id = g.id
                ORDER BY s.timestamp DESC
            """)
        if path == "/api/division_entries":
            return query("""
                SELECT de.*, pv.name as policy_version_name, l.name as league_name,
                       g.name as game_name, p.name as player_name,
                       d.name as division_name, d.level as division_level
                FROM division_entries de
                JOIN policy_versions pv ON de.policy_version_id = pv.id
                JOIN players p ON de.player_id = p.id
                JOIN leagues l ON de.league_id = l.id
                JOIN games g ON l.game_id = g.id
                JOIN divisions d ON de.division_id = d.id
                ORDER BY de.created_at DESC, de.id DESC
            """)
        if path == "/api/division_entry_events":
            return query("""
                SELECT dee.*, pv.name as policy_version_name,
                       p.name as player_name,
                       l.name as league_name,
                       from_d.name as from_division_name, from_d.level as from_division_level,
                       to_d.name as to_division_name, to_d.level as to_division_level
                FROM division_entry_events dee
                JOIN policy_versions pv ON dee.policy_version_id = pv.id
                JOIN players p ON pv.player_id = p.id
                JOIN leagues l ON dee.league_id = l.id
                LEFT JOIN divisions from_d ON dee.from_division_id = from_d.id
                JOIN divisions to_d ON dee.to_division_id = to_d.id
                ORDER BY dee.created_at DESC, dee.id DESC
            """)
        if path == "/api/player_league_memberships":
            return query("""
                SELECT plm.*, p.name as player_name, l.name as league_name, g.name as game_name,
                       u.name as user_name, p.user_id
                FROM player_league_memberships plm
                JOIN players p ON plm.player_id = p.id
                JOIN users u ON p.user_id = u.id
                JOIN leagues l ON plm.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/projects":
            return query("""
                SELECT pr.*, p.name as player_name, p.user_id, u.name as user_name
                FROM projects pr
                JOIN players p ON pr.player_id = p.id
                JOIN users u ON p.user_id = u.id
            """)
        if path == "/api/status_updates":
            return query("""
                SELECT su.*, pr.name as project_name, pr.player_id,
                       p.name as player_name
                FROM status_updates su
                JOIN projects pr ON su.project_id = pr.id
                JOIN players p ON pr.player_id = p.id
                ORDER BY su.created_at DESC
            """)
        if path == "/api/variants":
            return query("""
                SELECT v.*, g.name as game_name
                FROM variants v
                JOIN games g ON v.game_id = g.id
            """)
        if path == "/api/mod_variants":
            return query("""
                SELECT mv.*, m.name as mod_name, v.name as variant_name
                FROM mod_variants mv
                JOIN mods m ON mv.mod_id = m.id
                JOIN variants v ON mv.variant_id = v.id
            """)
        if path == "/api/episodes":
            return query("""
                SELECT e.*, v.name as variant_name
                FROM episodes e JOIN variants v ON e.variant_id = v.id
            """)
        if path == "/api/episode_policies":
            return query("""
                SELECT ep.*, pv.name as policy_version_name, p.name as player_name, p.id as player_id
                FROM episode_policies ep
                JOIN policy_versions pv ON ep.policy_version_id = pv.id
                JOIN players p ON pv.player_id = p.id
            """)
        if path == "/api/episode_logs":
            return query("""
                SELECT el.*, e.variant_id, e.seed
                FROM episode_logs el
                JOIN episodes e ON el.episode_id = e.id
            """)
        if path == "/api/rounds":
            return query("""
                SELECT r.*, d.name as division_name,
                       l.name as league_name, g.name as game_name
                FROM rounds r
                JOIN divisions d ON r.division_id = d.id
                JOIN leagues l ON d.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/rank_users":
            return query(RANK_USERS_SQL)
        if path == "/api/rank_players":
            return query(RANK_PLAYERS_SQL)
        if path == "/api/round_results":
            return query("""
                SELECT rr.*, pv.name as policy_version_name,
                       p.name as player_name,
                       r.division_id, d.name as division_name,
                       l.name as league_name
                FROM round_results rr
                JOIN policy_versions pv ON rr.policy_version_id = pv.id
                JOIN players p ON rr.player_id = p.id
                JOIN rounds r ON rr.round_id = r.id
                JOIN divisions d ON r.division_id = d.id
                JOIN leagues l ON d.league_id = l.id
                ORDER BY rr.round_id, rr.rank
            """)
        if path == "/api/round_episodes":
            return query("""
                SELECT re.*, r.notes as round_notes, r.division_id,
                       e.variant_id, e.seed
                FROM round_episodes re
                JOIN rounds r ON re.round_id = r.id
                JOIN episodes e ON re.episode_id = e.id
            """)
        if path == "/api/policy_pools":
            return query("""
                SELECT p.*, r.division_id, r.notes as round_notes,
                       v.name as variant_name
                FROM policy_pools p
                JOIN rounds r ON p.round_id = r.id
                LEFT JOIN variants v ON p.variant_id = v.id
            """)
        if path == "/api/policy_pool_entries":
            return query("""
                SELECT pe.*, pv.name as policy_version_name,
                       pl.name as player_name,
                       p.label as pool_label, p.pool_type
                FROM policy_pool_entries pe
                JOIN policy_versions pv ON pe.policy_version_id = pv.id
                LEFT JOIN players pl ON pe.player_id = pl.id
                JOIN policy_pools p ON pe.policy_pool_id = p.id
            """)
        if path == "/api/episode_requests":
            return query("""
                SELECT er.*, v.name as variant_name, u.name as requester_name
                FROM episode_requests er
                JOIN variants v ON er.variant_id = v.id
                JOIN users u ON er.requester_user_id = u.id
                ORDER BY er.created_at DESC
            """)
        if path == "/api/episode_request_policies":
            return query("""
                SELECT erp.*, pv.name as policy_version_name
                FROM episode_request_policies erp
                JOIN policy_versions pv ON erp.policy_version_id = pv.id
                ORDER BY erp.episode_request_id, erp.position
            """)
        return None

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        result = self.handle_mutation(path, body)
        if result is not None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def handle_mutation(self, path, body):
        # POST /api/users/new {name, email}
        if path == "/api/users/new":
            uid = mutate(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (body["name"], body["email"]),
            )
            return {"id": uid}

        # POST /api/users/:id/create_player {name}
        import re
        m = re.match(r"/api/users/(\d+)/create_player", path)
        if m:
            user_id = int(m.group(1))
            pid = mutate(
                "INSERT INTO players (user_id, name) VALUES (?, ?)",
                (user_id, body["name"]),
            )
            return {"id": pid}

        # POST /api/players/:id/create_policy_version {name}
        m = re.match(r"/api/players/(\d+)/create_policy_version", path)
        if m:
            player_id = int(m.group(1))
            pv_id = mutate(
                "INSERT INTO policy_versions (player_id, name) VALUES (?, ?)",
                (player_id, body["name"]),
            )
            return {"id": pv_id}

        # POST /api/players/:id/submit {policy_version_id, league_id, notes?, preferences?}
        m = re.match(r"/api/players/(\d+)/submit", path)
        if m:
            player_id = int(m.group(1))
            policy_version_id = body["policy_version_id"]
            league_id = body["league_id"]
            notes = body.get("notes", "")
            preferences = json.dumps(body.get("preferences", {}))
            sub_id = mutate(
                "INSERT INTO submissions (policy_version_id, league_id, notes, preferences) VALUES (?, ?, ?, ?)",
                (policy_version_id, league_id, notes, preferences),
            )
            existing = query(
                "SELECT * FROM player_league_memberships WHERE player_id=? AND league_id=?",
                (player_id, league_id),
            )
            if not existing:
                mutate(
                    "INSERT INTO player_league_memberships (player_id, league_id) VALUES (?, ?)",
                    (player_id, league_id),
                )
            return {"id": sub_id}

        # POST /api/submissions/:id/place {division_id}
        m = re.match(r"/api/submissions/(\d+)/place", path)
        if m:
            sub_id = int(m.group(1))
            division_id = body["division_id"]
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            sub = conn.execute("SELECT * FROM submissions WHERE id=?", (sub_id,)).fetchone()
            if not sub:
                conn.close()
                return {"error": "not found"}
            division = conn.execute("SELECT * FROM divisions WHERE id=?", (division_id,)).fetchone()
            if not division:
                conn.close()
                return {"error": "division not found"}
            if division["league_id"] != sub["league_id"]:
                conn.close()
                return {"error": "division must belong to submission league"}

            policy_version_id = sub["policy_version_id"]
            league_id = sub["league_id"]

            # Get player_id from policy_version
            pv = conn.execute("SELECT player_id FROM policy_versions WHERE id=?", (policy_version_id,)).fetchone()
            player_id = pv["player_id"] if pv else None

            # Check for existing active entry in this league
            existing_entry = conn.execute("""
                SELECT de.id, de.division_id
                FROM division_entries de
                WHERE de.policy_version_id = ? AND de.league_id = ? AND de.is_active = 1
                ORDER BY de.id DESC LIMIT 1
            """, (policy_version_id, league_id)).fetchone()

            from_division_id = existing_entry["division_id"] if existing_entry else None

            if existing_entry and existing_entry["division_id"] != division_id:
                # Deactivate old entry
                conn.execute(
                    "UPDATE division_entries SET is_active = 0 WHERE id = ?",
                    (existing_entry["id"],),
                )

            if not existing_entry or existing_entry["division_id"] != division_id:
                # Create new division entry
                cur = conn.execute(
                    "INSERT INTO division_entries (policy_version_id, league_id, division_id, player_id) VALUES (?, ?, ?, ?)",
                    (policy_version_id, league_id, division_id, player_id),
                )
                entry_id = cur.lastrowid
            else:
                entry_id = existing_entry["id"]

            # Record event
            if from_division_id != division_id:
                conn.execute("""
                    INSERT INTO division_entry_events (
                        policy_version_id, league_id, player_id, from_division_id, to_division_id, division_entry_id, event_type, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    policy_version_id,
                    league_id,
                    player_id,
                    from_division_id,
                    division_id,
                    entry_id,
                    "place" if from_division_id is None else "move",
                    f"Recorded from submission #{sub_id}",
                ))

            # Link submission to entry and mark placed
            conn.execute("UPDATE submissions SET status='placed', division_entry_id=? WHERE id=?", (entry_id, sub_id))
            conn.commit()
            conn.close()
            return {"division_entry_id": entry_id}

        # POST /api/submissions/:id/reject {notes?}
        m = re.match(r"/api/submissions/(\d+)/reject", path)
        if m:
            sub_id = int(m.group(1))
            notes = body.get("notes", "")
            mutate(
                "UPDATE submissions SET status='rejected', notes=notes||? WHERE id=?",
                ((" [REJECTED: " + notes + "]") if notes else " [REJECTED]", sub_id),
            )
            return {"ok": True}

        return None

    def log_message(self, format, *args):
        pass  # quiet


if __name__ == "__main__":
    port = 8777
    server = HTTPServer(("", port), Handler)
    print(f"Serving at http://localhost:{port}")
    server.serve_forever()
