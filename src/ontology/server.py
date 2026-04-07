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
        if path == "/api/users":
            return query("SELECT * FROM users")
        if path == "/api/players":
            return query("""
                SELECT p.*, u.name as user_name
                FROM players p JOIN users u ON p.user_id = u.id
            """)
        if path == "/api/policies":
            return query("""
                SELECT pol.*, p.name as player_name, u.name as user_name
                FROM policies pol
                JOIN players p ON pol.player_id = p.id
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
                LEFT JOIN mods m ON l.mod_id = m.id
            """)
        if path == "/api/divisions":
            return query("""
                SELECT d.*, l.name as league_name, g.name as game_name
                FROM divisions d
                JOIN leagues l ON d.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/pools":
            return query("""
                SELECT p.*, d.name as division_name, d.league_id, l.name as league_name, g.name as game_name
                FROM pools p
                JOIN divisions d ON p.division_id = d.id
                JOIN leagues l ON d.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/submissions":
            return query("""
                SELECT s.*, pol.name as policy_name, l.name as league_name,
                       g.name as game_name, p.name as player_name, p.id as player_id,
                       pred.name as pred_policy_name
                FROM submissions s
                JOIN policies pol ON s.policy_id = pol.id
                JOIN players p ON pol.player_id = p.id
                JOIN leagues l ON s.league_id = l.id
                JOIN games g ON l.game_id = g.id
                LEFT JOIN policies pred ON s.pred_policy_id = pred.id
                ORDER BY s.timestamp DESC
            """)
        if path == "/api/placements":
            return query("""
                SELECT pl.*, pol.name as policy_name, l.name as league_name,
                       g.name as game_name, p.name as player_name, p.id as player_id,
                       d.name as division_name, d.level as division_level
                FROM placements pl
                JOIN policies pol ON pl.policy_id = pol.id
                JOIN players p ON pol.player_id = p.id
                JOIN leagues l ON pl.league_id = l.id
                JOIN games g ON l.game_id = g.id
                LEFT JOIN divisions d ON pl.division_id = d.id
            """)
        if path == "/api/placement_results":
            return query("""
                SELECT pr.*, p.id as placement_id,
                       d.name as division_name, d.level as division_level,
                       l.name as league_name, pol.name as policy_name,
                       pl.name as player_name, pl.id as player_id
                FROM placement_results pr
                JOIN placements p ON pr.placement_id = p.id
                JOIN divisions d ON pr.division_id = d.id
                JOIN leagues l ON p.league_id = l.id
                JOIN policies pol ON p.policy_id = pol.id
                JOIN players pl ON pol.player_id = pl.id
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
        if path == "/api/experience_requests":
            return query("""
                SELECT er.*, u.name as user_name
                FROM experience_requests er
                JOIN users u ON er.user_id = u.id
                ORDER BY er.created_at DESC
            """)
        if path == "/api/variants":
            return query("SELECT * FROM variants")
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
                SELECT ep.*, pol.name as policy_name, p.name as player_name, p.id as player_id
                FROM episode_policies ep
                JOIN policies pol ON ep.policy_id = pol.id
                JOIN players p ON pol.player_id = p.id
            """)
        if path == "/api/episode_logs":
            return query("""
                SELECT el.*, e.variant_id, e.seed
                FROM episode_logs el
                JOIN episodes e ON el.episode_id = e.id
            """)
        if path == "/api/rounds":
            return query("""
                SELECT r.*, p.name as pool_name, d.name as division_name,
                       l.name as league_name, g.name as game_name
                FROM rounds r
                JOIN pools p ON r.pool_id = p.id
                JOIN divisions d ON p.division_id = d.id
                JOIN leagues l ON d.league_id = l.id
                JOIN games g ON l.game_id = g.id
            """)
        if path == "/api/rank_users":
            return query("""
                SELECT ru.*, u.name as user_name, l.name as league_name,
                       d.name as division_name
                FROM rank_users ru
                JOIN users u ON ru.user_id = u.id
                JOIN leagues l ON ru.league_id = l.id
                LEFT JOIN divisions d ON ru.division_id = d.id
                ORDER BY ru.league_id, ru.timestamp DESC, ru.rank
            """)
        if path == "/api/rank_players":
            return query("""
                SELECT rp.*, p.name as player_name, l.name as league_name,
                       d.name as division_name, u.name as user_name, p.user_id
                FROM rank_players rp
                JOIN players p ON rp.player_id = p.id
                JOIN users u ON p.user_id = u.id
                JOIN leagues l ON rp.league_id = l.id
                LEFT JOIN divisions d ON rp.division_id = d.id
                ORDER BY rp.league_id, rp.timestamp DESC, rp.rank
            """)
        if path == "/api/rank_policies":
            return query("""
                SELECT rp.*, pol.name as policy_name, l.name as league_name,
                       d.name as division_name, p.name as player_name, p.id as player_id
                FROM rank_policies rp
                JOIN policies pol ON rp.policy_id = pol.id
                JOIN players p ON pol.player_id = p.id
                JOIN leagues l ON rp.league_id = l.id
                LEFT JOIN divisions d ON rp.division_id = d.id
                ORDER BY rp.league_id, rp.timestamp DESC, rp.rank
            """)
        if path == "/api/round_episodes":
            return query("""
                SELECT re.*, r.notes as round_notes, r.pool_id,
                       e.variant_id, e.seed
                FROM round_episodes re
                JOIN rounds r ON re.round_id = r.id
                JOIN episodes e ON re.episode_id = e.id
            """)
        if path == "/api/pool_policies":
            return query("""
                SELECT pp.pool_id, pp.policy_id,
                       po.name as pool_name,
                       pol.name as policy_name,
                       pl.name as player_name
                FROM pool_policies pp
                JOIN pools po ON pp.pool_id = po.id
                JOIN policies pol ON pp.policy_id = pol.id
                JOIN players pl ON pol.player_id = pl.id
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

        # POST /api/players/:id/create_policy {name}
        m = re.match(r"/api/players/(\d+)/create_policy", path)
        if m:
            player_id = int(m.group(1))
            pol_id = mutate(
                "INSERT INTO policies (player_id, name) VALUES (?, ?)",
                (player_id, body["name"]),
            )
            return {"id": pol_id}

        # POST /api/players/:id/submit {policy_id, league_id, notes?, pred_policy_id?, preferences?}
        m = re.match(r"/api/players/(\d+)/submit", path)
        if m:
            player_id = int(m.group(1))
            policy_id = body["policy_id"]
            league_id = body["league_id"]
            notes = body.get("notes", "")
            pred_policy_id = body.get("pred_policy_id")
            preferences = json.dumps(body.get("preferences", {}))
            # Create submission record
            sub_id = mutate(
                "INSERT INTO submissions (policy_id, league_id, notes, pred_policy_id, preferences) VALUES (?, ?, ?, ?, ?)",
                (policy_id, league_id, notes, pred_policy_id, preferences),
            )
            # Ensure player_league_membership exists
            existing = query(
                "SELECT * FROM player_league_memberships WHERE player_id=? AND league_id=?",
                (player_id, league_id),
            )
            if not existing:
                mutate(
                    "INSERT INTO player_league_memberships (player_id, league_id) VALUES (?, ?)",
                    (player_id, league_id),
                )
            # Add policy to first pool in first division of this league
            div = query(
                "SELECT id FROM divisions WHERE league_id=? ORDER BY level LIMIT 1",
                (league_id,),
            )
            if div:
                pool = query(
                    "SELECT id FROM pools WHERE division_id=? LIMIT 1",
                    (div[0]["id"],),
                )
                if pool:
                    existing_pp = query(
                        "SELECT * FROM pool_policies WHERE pool_id=? AND policy_id=?",
                        (pool[0]["id"], policy_id),
                    )
                    if not existing_pp:
                        mutate(
                            "INSERT INTO pool_policies (pool_id, policy_id) VALUES (?, ?)",
                            (pool[0]["id"], policy_id),
                        )
            return {"id": sub_id}

        # POST /api/submissions/:id/place {division_id}
        m = re.match(r"/api/submissions/(\d+)/place", path)
        if m:
            sub_id = int(m.group(1))
            division_id = body["division_id"]
            sub = query("SELECT * FROM submissions WHERE id=?", (sub_id,))
            if not sub:
                return {"error": "not found"}
            s = sub[0]
            # Create placement
            pl_id = mutate(
                "INSERT INTO placements (policy_id, league_id, division_id, notes) VALUES (?, ?, ?, ?)",
                (s["policy_id"], s["league_id"], division_id, f"From submission #{sub_id}"),
            )
            # Create placement result
            mutate(
                "INSERT INTO placement_results (placement_id, division_id) VALUES (?, ?)",
                (pl_id, division_id),
            )
            # Update submission status
            mutate("UPDATE submissions SET status='placed' WHERE id=?", (sub_id,))
            return {"placement_id": pl_id}

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
