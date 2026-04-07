#!/usr/bin/env python3
"""Create and seed the game service SQLite database."""

import sqlite3
import os

DATA_DIR = os.path.join(os.path.expanduser("~"), ".softmax-universe")
DB_PATH = os.path.join(DATA_DIR, "ontology.db")


def create_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE commissioners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            strategy TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game_id INTEGER NOT NULL REFERENCES games(id),
            mod_id INTEGER NOT NULL REFERENCES mods(id),
            commissioner_id INTEGER NOT NULL REFERENCES commissioners(id),
            rules TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            level INTEGER NOT NULL DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE mods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game_id INTEGER NOT NULL REFERENCES games(id),
            owner_id INTEGER NOT NULL REFERENCES users(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT DEFAULT '',
            pred_policy_id INTEGER REFERENCES policies(id),
            preferences TEXT DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'placed', 'rejected')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE placements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            division_id INTEGER NOT NULL REFERENCES divisions(id),
            submission_id INTEGER REFERENCES submissions(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE division_policy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            from_division_id INTEGER REFERENCES divisions(id),
            to_division_id INTEGER NOT NULL REFERENCES divisions(id),
            placement_id INTEGER REFERENCES placements(id),
            submission_id INTEGER REFERENCES submissions(id),
            change_type TEXT NOT NULL DEFAULT 'placement' CHECK(change_type IN ('placement', 'move')),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE player_league_memberships (
            player_id INTEGER NOT NULL REFERENCES players(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            is_avatar INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (player_id, league_id)
        );

        CREATE TABLE variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            config TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL REFERENCES players(id),
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','paused','completed','archived')),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE status_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            content TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE experience_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            mettagrid_config TEXT NOT NULL DEFAULT '{}',
            policy_ids TEXT NOT NULL DEFAULT '[]',
            seed INTEGER,
            num_episodes INTEGER NOT NULL DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE mod_variants (
            mod_id INTEGER NOT NULL REFERENCES mods(id),
            variant_id INTEGER NOT NULL REFERENCES variants(id),
            canonical INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (mod_id, variant_id)
        );

        CREATE TABLE episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER NOT NULL REFERENCES variants(id),
            seed INTEGER NOT NULL,
            score TEXT DEFAULT '{}',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE episode_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            episode_id INTEGER NOT NULL REFERENCES episodes(id),
            agent_id INTEGER NOT NULL DEFAULT 0,
            score REAL DEFAULT 0,
            logs TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE episode_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id INTEGER NOT NULL REFERENCES episodes(id),
            log_uri TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division_id INTEGER NOT NULL REFERENCES divisions(id),
            notes TEXT DEFAULT '',
            results TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE rank_policies (
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            rank INTEGER NOT NULL,
            division_id INTEGER REFERENCES divisions(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (league_id, policy_id, timestamp)
        );

        CREATE TABLE round_episodes (
            round_id INTEGER NOT NULL REFERENCES rounds(id),
            episode_id INTEGER NOT NULL REFERENCES episodes(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (round_id, episode_id)
        );

        CREATE TABLE division_policies (
            division_id INTEGER NOT NULL REFERENCES divisions(id),
            policy_id INTEGER NOT NULL REFERENCES policies(id),
            is_champion INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (division_id, policy_id)
        );
    """)

    # -- Seed data --

    users = [
        ("David Bloomin", "david@example.com"),
        ("Emmett Shear", "emmett@example.com"),
        ("Richard Higgins", "richard@example.com"),
    ]
    c.executemany("INSERT INTO users (name, email) VALUES (?, ?)", users)

    players = [
        (1, "daveey"),
        (1, "daveey_alt"),
        (2, "emmett_main"),
        (2, "emmett_v2"),
        (3, "relh"),
        (3, "relh_smurf"),
    ]
    c.executemany("INSERT INTO players (user_id, name) VALUES (?, ?)", players)

    policies = [
        (1, "AlphaStrike", "Aggressive opener with early rush", "Needs tuning vs turtle strats"),
        (1, "DefendBot", "Defensive wall strategy", ""),
        (2, "RushDown", "All-in rush before 2min mark", "Weak on large maps"),
        (3, "TurtleShell", "Slow economy build into late game", ""),
        (3, "Blitz-v3", "Fast expand with harassment", "v3 fixes pathing bugs"),
        (4, "SwarmAI", "Mass cheap units, overwhelm", "Best on open maps"),
        (4, "HiveMind", "Coordinated multi-front attacks", ""),
        (5, "SniperBot", "Long-range precision strikes", "Counters SwarmAI well"),
        (5, "TankBot", "Heavy armor push", ""),
        (6, "ScoutRush", "Early scouting into adaptive play", "Still experimental"),
        (6, "FlankerPro", "Flanking maneuvers and ambushes", ""),
    ]
    c.executemany("INSERT INTO policies (player_id, name, description, notes) VALUES (?, ?, ?, ?)", policies)

    games = [
        ("Cogs vs Clips", "Tower defense with AI-controlled guardians", 1),
        ("Over Cooked", "Team-based cooperative cooking chaos", 2),
        ("BomberCog", "Grid-based bomb placement and strategy", 3),
    ]
    c.executemany("INSERT INTO games (name, description, owner_id) VALUES (?, ?, ?)", games)

    mods = [
        ("Base", 1, 1),
        ("Clones", 1, 1),
        ("Four-Score", 1, 2),
        ("Latte", 1, 3),
        ("OverCogged", 1, 2),
        ("Classic", 2, 2),
        ("Turbo", 2, 2),
        ("Standard", 3, 3),
    ]
    c.executemany("INSERT INTO mods (name, game_id, owner_id) VALUES (?, ?, ?)", mods)

    commissioners = [
        ("Commie 1", "Round-robin with ELO-based seeding. Promote top 2, relegate bottom 2 each season."),
        ("Commie 2", "Swiss-system tournament, best-of-5 matches. Tiebreaks by head-to-head record."),
        ("Commie 3", "Open ladder with decay. Inactive policies drop rank after 7 days."),
    ]
    c.executemany(
        "INSERT INTO commissioners (name, strategy) VALUES (?, ?)",
        commissioners,
    )

    leagues = [
        ("Base", 1, 1, 1, "Standard rules"),
        ("Clones", 1, 2, 1, "Clone variant with duplicated units"),
        ("Four-Score", 1, 3, 1, "4-player free-for-all, first to 4 wins"),
        ("Pro League", 2, 6, 2, "Tournament format, best of 5"),
        ("Casual", 2, 7, 3, "No stakes, practice matches"),
        ("Championship", 3, 8, 3, "Invite only, top 16 policies"),
    ]
    c.executemany(
        "INSERT INTO leagues (name, game_id, mod_id, commissioner_id, rules) VALUES (?, ?, ?, ?, ?)",
        leagues,
    )

    divisions = [
        ("Carbon", 1, 1),       # Base league
        ("Oxygen", 1, 2),
        ("Silicon", 2, 1),      # Clones league
        ("Carbon", 3, 1),       # Four-Score league
        ("Germanium", 3, 2),
        ("Carbon", 4, 1),       # Pro League
        ("Oxygen", 4, 2),
        ("Silicon", 5, 1),      # Casual
        ("Carbon", 6, 1),       # Championship
    ]
    c.executemany(
        "INSERT INTO divisions (name, league_id, level) VALUES (?, ?, ?)",
        divisions,
    )

    submissions = [
        (1, 1, "2026-04-01 10:00:00", "Initial submission", None, '{"map_size": "large"}', "placed"),
        (2, 1, "2026-04-01 11:00:00", "Defensive variant", 1, '{}', "placed"),
        (3, 1, "2026-04-02 09:00:00", "", None, '{"timeout": 30}', "placed"),
        (5, 2, "2026-04-02 14:00:00", "Testing blitz on clones", None, '{}', "placed"),
        (6, 3, "2026-04-03 08:00:00", "Swarm v2 for four-score", None, '{"team_size": 4}', "placed"),
        (8, 1, "2026-04-03 12:00:00", "Sniper counter-meta", 1, '{}', "placed"),
        (9, 4, "2026-04-04 10:00:00", "", None, '{}', "placed"),
        (1, 2, "2026-04-05 09:00:00", "Updated alpha for clones", None, '{"clone_count": 3}', "pending"),
        (10, 6, "2026-04-05 15:00:00", "Championship entry", None, '{}', "placed"),
    ]
    c.executemany(
        "INSERT INTO submissions (policy_id, league_id, timestamp, notes, pred_policy_id, preferences, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        submissions,
    )

    placements = [
        (1, 1, 1, 1, "Placed into Carbon"),
        (2, 1, 2, 2, "Placed into Oxygen"),
        (3, 1, 1, 3, ""),
        (5, 2, 3, 4, "Placed into Silicon"),
        (6, 3, 4, 5, ""),
        (8, 1, 1, 6, "Sniper placed Carbon"),
        (9, 4, 6, 7, "Pro league entry"),
        (10, 6, 9, 9, "Championship Carbon"),
        (4, 1, 1, None, "Preseason commissioner invite"),
    ]
    c.executemany(
        "INSERT INTO placements (policy_id, league_id, division_id, submission_id, notes) VALUES (?, ?, ?, ?, ?)",
        placements,
    )

    division_policy_history = [
        (1, 1, None, 1, 1, 1, "placement", "Accepted from submission #1"),
        (2, 1, None, 2, 2, 2, "placement", "Accepted from submission #2"),
        (3, 1, None, 1, 3, 3, "placement", "Accepted from submission #3"),
        (5, 2, None, 3, 4, 4, "placement", "Accepted from submission #4"),
        (6, 3, None, 4, 5, 5, "placement", "Accepted from submission #5"),
        (8, 1, None, 1, 6, 6, "placement", "Accepted from submission #6"),
        (9, 4, None, 6, 7, 7, "placement", "Initial Pro League placement"),
        (9, 4, 6, 7, None, None, "move", "Promoted from Carbon to Oxygen"),
        (10, 6, None, 9, 8, 9, "placement", "Accepted from submission #9"),
        (4, 1, None, 1, 9, None, "placement", "Commissioner invite without submission"),
    ]
    c.executemany(
        """
        INSERT INTO division_policy_history (
            policy_id, league_id, from_division_id, to_division_id, placement_id, submission_id, change_type, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        division_policy_history,
    )

    player_league_memberships = [
        (1, 1, 1), (1, 2, 0),  # daveey in Base (avatar), Clones
        (2, 1, 0),               # daveey_alt in Base
        (3, 1, 0), (3, 3, 1),  # emmett_main in Base, Four-Score (avatar)
        (4, 4, 0),               # emmett_v2 in Pro League
        (5, 1, 0), (5, 6, 1),  # relh in Base, Championship (avatar)
        (6, 5, 0),               # relh_smurf in Casual
    ]
    c.executemany(
        "INSERT INTO player_league_memberships (player_id, league_id, is_avatar) VALUES (?, ?, ?)",
        player_league_memberships,
    )

    variants = [
        ("Standard 1v1", '{"map": "arena", "players": 2, "turns": 100}'),
        ("2v2 Teams", '{"map": "battlefield", "players": 4, "turns": 200}'),
        ("FFA Chaos", '{"map": "colosseum", "players": 6, "turns": 150}'),
    ]
    c.executemany("INSERT INTO variants (name, config) VALUES (?, ?)", variants)

    projects = [
        (1, "Rush Meta Research", "active"),
        (1, "Defense Optimization", "paused"),
        (3, "Swarm Tactics v2", "active"),
        (5, "Sniper Counter-Play", "completed"),
        (6, "Tournament Prep", "active"),
    ]
    c.executemany(
        "INSERT INTO projects (player_id, name, status) VALUES (?, ?, ?)",
        projects,
    )

    status_updates = [
        (1, "Started analyzing rush timings across maps"),
        (1, "Found optimal rush window is 45-60s on small maps"),
        (2, "Pausing defense work to focus on rush meta"),
        (3, "SwarmAI v2 prototype showing 15% improvement"),
        (3, "Testing multi-front coordination"),
        (4, "SniperBot now counters all rush variants"),
        (5, "Registered for Championship league"),
        (5, "Running practice matches against top 5 policies"),
    ]
    c.executemany(
        "INSERT INTO status_updates (project_id, content) VALUES (?, ?)",
        status_updates,
    )

    experience_requests = [
        (1, '{"map": "arena", "players": 2}', '[1, 2]', 42, 10),
        (2, '{"map": "battlefield", "fog": true}', '[6, 7]', None, 5),
        (1, '{"map": "arena", "players": 4}', '[1, 2, 4, 8]', 99, 20),
        (3, '{"map": "colosseum"}', '[8, 9]', None, 3),
    ]
    c.executemany(
        "INSERT INTO experience_requests (user_id, mettagrid_config, policy_ids, seed, num_episodes) VALUES (?, ?, ?, ?, ?)",
        experience_requests,
    )

    mod_variants = [
        (1, 1, 1),  # Base mod → Standard 1v1 (canonical)
        (1, 2, 0),  # Base mod → 2v2 Teams
        (2, 1, 1),  # Clones mod → Standard 1v1 (canonical)
        (3, 3, 1),  # Four-Score mod → FFA Chaos (canonical)
        (4, 1, 1),  # Latte mod → Standard 1v1 (canonical)
        (5, 2, 1),  # OverCogged mod → 2v2 Teams (canonical)
    ]
    c.executemany(
        "INSERT INTO mod_variants (mod_id, variant_id, canonical) VALUES (?, ?, ?)",
        mod_variants,
    )

    episodes = [
        (1, 42, '{"winner": "AlphaStrike", "turns": 24}'),
        (1, 99, '{"winner": "AlphaStrike", "turns": 31}'),
        (2, 7, '{"winner": "Blitz-v3", "turns": 18}'),
        (1, 123, '{"winner": "AlphaStrike", "turns": 27}'),
        (3, 55, '{"winner": "TankBot", "turns": 40}'),
        (2, 88, '{"winner": "Blitz-v3", "turns": 22}'),
    ]
    c.executemany("INSERT INTO episodes (variant_id, seed, score) VALUES (?, ?, ?)", episodes)

    episode_policies = [
        (1, 1, 0, 3.5, "Turn 12: captured flag"),
        (2, 1, 1, 1.2, ""),
        (1, 2, 0, 4.0, "Dominated early game"),
        (3, 2, 1, 2.1, ""),
        (5, 3, 0, 5.0, "Perfect score"),
        (6, 3, 1, 3.3, "Close match"),
        (8, 4, 0, 2.8, ""),
        (1, 4, 1, 3.1, ""),
        (9, 5, 0, 4.5, "Strong finish"),
        (10, 5, 1, 1.0, "Eliminated round 2"),
        (5, 6, 0, 3.9, ""),
        (7, 6, 1, 2.5, "HiveMind timeout on turn 8"),
    ]
    c.executemany(
        "INSERT INTO episode_policies (policy_id, episode_id, agent_id, score, logs) VALUES (?, ?, ?, ?, ?)",
        episode_policies,
    )

    episode_logs = [
        (1, "s3://games/episodes/1/replay.log"),
        (1, "s3://games/episodes/1/metrics.json"),
        (2, "s3://games/episodes/2/replay.log"),
        (3, "s3://games/episodes/3/replay.log"),
        (4, "s3://games/episodes/4/replay.log"),
        (5, "s3://games/episodes/5/replay.log"),
        (6, "s3://games/episodes/6/replay.log"),
    ]
    c.executemany(
        "INSERT INTO episode_logs (episode_id, log_uri) VALUES (?, ?)",
        episode_logs,
    )

    rounds = [
        (1, "Round 1", '{"AlphaStrike": 3, "TurtleShell": 1, "SniperBot": 2}'),
        (1, "Round 2", '{"AlphaStrike": 2, "TurtleShell": 2, "SniperBot": 2}'),
        (2, "Round 1", '{"DefendBot": 1, "Blitz-v3": 3, "TankBot": 2}'),
        (3, "Round 1", '{"AlphaStrike": 4, "SwarmAI": 0, "ScoutRush": 2}'),
        (4, "Qualifier", '{"DefendBot": 2, "Blitz-v3": 1, "TankBot": 3}'),
        (6, "Semifinal", '{"AlphaStrike": 5, "SwarmAI": 3, "SniperBot": 4, "FlankerPro": 2}'),
        (9, "Final", '{"AlphaStrike": 6, "SniperBot": 5, "TankBot": 3, "FlankerPro": 4}'),
    ]
    c.executemany(
        "INSERT INTO rounds (division_id, notes, results) VALUES (?, ?, ?)",
        rounds,
    )

    rank_policies = [
        (1, 1, "2026-04-01 12:00:00", 1, 1),
        (1, 2, "2026-04-01 12:00:00", 4, 2),
        (1, 4, "2026-04-01 12:00:00", 2, 1),
        (1, 8, "2026-04-01 12:00:00", 3, 1),
        (2, 5, "2026-04-02 12:00:00", 1, 3),
        (2, 6, "2026-04-02 12:00:00", 2, 3),
        (1, 1, "2026-04-03 12:00:00", 2, 1),
        (1, 4, "2026-04-03 12:00:00", 1, 1),
    ]
    c.executemany(
        "INSERT INTO rank_policies (league_id, policy_id, timestamp, rank, division_id) VALUES (?, ?, ?, ?, ?)",
        rank_policies,
    )

    round_episodes = [
        (1, 1), (1, 2),
        (2, 3),
        (3, 4),
        (5, 5),
        (6, 6),
        (7, 1), (7, 4),
    ]
    c.executemany(
        "INSERT INTO round_episodes (round_id, episode_id) VALUES (?, ?)",
        round_episodes,
    )

    division_policies = [
        (1, 1, 1), (1, 4, 0), (1, 8, 0), (1, 3, 0),   # Base Carbon (AlphaStrike champion)
        (2, 2, 0), (2, 5, 1), (2, 9, 0),                 # Base Oxygen (Blitz-v3 champion)
        (3, 3, 0), (3, 5, 0), (3, 7, 0), (3, 11, 1),     # Clones Silicon (FlankerPro champion)
        (4, 2, 0), (4, 5, 0), (4, 6, 1),                 # Four-Score Carbon (SwarmAI champion)
        (5, 9, 0),                                         # Four-Score Germanium
        (6, 1, 1), (6, 6, 0), (6, 8, 0), (6, 11, 0),   # Pro League Carbon (AlphaStrike champion)
        (7, 4, 0), (7, 7, 0), (7, 9, 0), (7, 10, 1),     # Pro League Oxygen (ScoutRush champion)
        (8, 10, 0),                                        # Casual Silicon
        (9, 1, 0), (9, 8, 1), (9, 9, 0), (9, 10, 0), (9, 11, 0),   # Championship Carbon (SniperBot champion)
    ]
    c.executemany("INSERT INTO division_policies (division_id, policy_id, is_champion) VALUES (?, ?, ?)", division_policies)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_db()
