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

        CREATE TABLE policy_versions (
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

        CREATE TABLE mods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game_id INTEGER NOT NULL REFERENCES games(id),
            owner_id INTEGER NOT NULL REFERENCES users(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game_id INTEGER NOT NULL REFERENCES games(id),
            config TEXT DEFAULT '',
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

        CREATE TABLE leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            game_id INTEGER NOT NULL REFERENCES games(id),
            mod_id INTEGER NOT NULL REFERENCES mods(id),
            commissioner_key TEXT NOT NULL,
            commissioner_config TEXT DEFAULT '{}',
            rules TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            level INTEGER NOT NULL DEFAULT 1,
            leaderboard_config TEXT DEFAULT '{}',
            round_schedule TEXT DEFAULT '{}',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            notes TEXT DEFAULT '',
            preferences TEXT DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'placed', 'rejected')),
            division_entry_id INTEGER REFERENCES division_entries(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE division_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            division_id INTEGER NOT NULL REFERENCES divisions(id),
            player_id INTEGER REFERENCES players(id),
            is_active INTEGER NOT NULL DEFAULT 1,
            is_champion INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE division_entry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            player_id INTEGER REFERENCES players(id),
            from_division_id INTEGER REFERENCES divisions(id),
            to_division_id INTEGER NOT NULL REFERENCES divisions(id),
            division_entry_id INTEGER REFERENCES division_entries(id),
            event_type TEXT NOT NULL DEFAULT 'place' CHECK(event_type IN ('place', 'move', 'remove', 'promote', 'demote')),
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
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
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
            round_display TEXT DEFAULT '{}',
            notes TEXT DEFAULT '',
            results TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE round_episodes (
            round_id INTEGER NOT NULL REFERENCES rounds(id),
            episode_id INTEGER NOT NULL REFERENCES episodes(id),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (round_id, episode_id)
        );

        CREATE TABLE round_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id INTEGER NOT NULL REFERENCES rounds(id),
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            player_id INTEGER REFERENCES players(id),
            rank INTEGER NOT NULL,
            score REAL DEFAULT 0,
            result_metadata TEXT DEFAULT '{}',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id INTEGER NOT NULL REFERENCES rounds(id),
            pool_index INTEGER NOT NULL DEFAULT 0,
            label TEXT NOT NULL,
            pool_type TEXT NOT NULL,
            variant_id INTEGER REFERENCES variants(id),
            config TEXT DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed')),
            error TEXT,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE pool_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER NOT NULL REFERENCES pools(id),
            division_entry_id INTEGER REFERENCES division_entries(id),
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            player_id INTEGER REFERENCES players(id),
            seed_order INTEGER NOT NULL DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE episode_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER REFERENCES pools(id),
            variant_id INTEGER NOT NULL REFERENCES variants(id),
            requester_user_id INTEGER NOT NULL REFERENCES users(id),
            player_id INTEGER REFERENCES players(id),
            job_index INTEGER,
            assignments TEXT DEFAULT '[]',
            seed INTEGER,
            max_steps INTEGER,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'submitted', 'running', 'completed', 'failed', 'cancelled')),
            job_spec TEXT DEFAULT '{}',
            synthetic_result TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE episode_request_policies (
            episode_request_id INTEGER NOT NULL REFERENCES episode_requests(id),
            position INTEGER NOT NULL,
            policy_version_id INTEGER NOT NULL REFERENCES policy_versions(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (episode_request_id, position)
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

    policy_versions = [
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
    c.executemany("INSERT INTO policy_versions (player_id, name, description, notes) VALUES (?, ?, ?, ?)", policy_versions)

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

    leagues = [
        ("Base", 1, 1, "round_robin_elo", '{"promote": 2, "relegate": 2}', "Standard rules"),
        ("Clones", 1, 2, "round_robin_elo", '{"promote": 2, "relegate": 2}', "Clone variant with duplicated units"),
        ("Four-Score", 1, 3, "round_robin_elo", '{"promote": 2, "relegate": 2}', "4-player free-for-all, first to 4 wins"),
        ("Pro League", 2, 6, "swiss_bo5", '{"tiebreak": "head_to_head"}', "Tournament format, best of 5"),
        ("Casual", 2, 7, "open_ladder", '{"decay_days": 7}', "No stakes, practice matches"),
        ("Championship", 3, 8, "open_ladder", '{"decay_days": 7}', "Invite only, top 16 policies"),
    ]
    c.executemany(
        "INSERT INTO leagues (name, game_id, mod_id, commissioner_key, commissioner_config, rules) VALUES (?, ?, ?, ?, ?, ?)",
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

    # division_entries merges old placements + division_policies
    # (policy_version_id, league_id, division_id, player_id, is_active, is_champion)
    division_entries = [
        (1, 1, 1, 1, 1, 1),    # AlphaStrike in Base Carbon (champion)
        (2, 1, 2, 1, 1, 0),    # DefendBot in Base Oxygen
        (3, 1, 1, 2, 1, 0),    # RushDown in Base Carbon
        (5, 2, 3, 3, 1, 0),    # Blitz-v3 in Clones Silicon
        (6, 3, 4, 4, 1, 1),    # SwarmAI in Four-Score Carbon (champion)
        (8, 1, 1, 5, 1, 0),    # SniperBot in Base Carbon
        (9, 4, 6, 5, 1, 0),    # TankBot in Pro League Carbon
        (10, 6, 9, 6, 1, 0),   # ScoutRush in Championship Carbon
        (4, 1, 1, 2, 1, 0),    # TurtleShell in Base Carbon (commissioner invite)
    ]
    c.executemany(
        "INSERT INTO division_entries (policy_version_id, league_id, division_id, player_id, is_active, is_champion) VALUES (?, ?, ?, ?, ?, ?)",
        division_entries,
    )

    # submissions now point to division_entries via division_entry_id
    submissions = [
        (1, 1, "2026-04-01 10:00:00", "Initial submission", '{"map_size": "large"}', "placed", 1),
        (2, 1, "2026-04-01 11:00:00", "Defensive variant", '{}', "placed", 2),
        (3, 1, "2026-04-02 09:00:00", "", '{"timeout": 30}', "placed", 3),
        (5, 2, "2026-04-02 14:00:00", "Testing blitz on clones", '{}', "placed", 4),
        (6, 3, "2026-04-03 08:00:00", "Swarm v2 for four-score", '{"team_size": 4}', "placed", 5),
        (8, 1, "2026-04-03 12:00:00", "Sniper counter-meta", '{}', "placed", 6),
        (9, 4, "2026-04-04 10:00:00", "", '{}', "placed", 7),
        (1, 2, "2026-04-05 09:00:00", "Updated alpha for clones", '{"clone_count": 3}', "pending", None),
        (10, 6, "2026-04-05 15:00:00", "Championship entry", '{}', "placed", 8),
    ]
    c.executemany(
        "INSERT INTO submissions (policy_version_id, league_id, timestamp, notes, preferences, status, division_entry_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        submissions,
    )

    division_entry_events = [
        (1, 1, 1, None, 1, 1, "place", "Accepted from submission #1"),
        (2, 1, 1, None, 2, 2, "place", "Accepted from submission #2"),
        (3, 1, 2, None, 1, 3, "place", "Accepted from submission #3"),
        (5, 2, 3, None, 3, 4, "place", "Accepted from submission #4"),
        (6, 3, 4, None, 4, 5, "place", "Accepted from submission #5"),
        (8, 1, 5, None, 1, 6, "place", "Accepted from submission #6"),
        (9, 4, 5, None, 6, 7, "place", "Initial Pro League placement"),
        (9, 4, 5, 6, 7, 7, "move", "Promoted from Carbon to Oxygen"),
        (10, 6, 6, None, 9, 8, "place", "Accepted from submission #9"),
        (4, 1, 2, None, 1, 9, "place", "Commissioner invite without submission"),
    ]
    c.executemany(
        """
        INSERT INTO division_entry_events (
            policy_version_id, league_id, player_id, from_division_id, to_division_id, division_entry_id, event_type, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        division_entry_events,
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
        ("Standard 1v1", 1, '{"map": "arena", "players": 2, "turns": 100}'),
        ("2v2 Teams", 1, '{"map": "battlefield", "players": 4, "turns": 200}'),
        ("FFA Chaos", 1, '{"map": "colosseum", "players": 6, "turns": 150}'),
    ]
    c.executemany("INSERT INTO variants (name, game_id, config) VALUES (?, ?, ?)", variants)

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
        "INSERT INTO episode_policies (policy_version_id, episode_id, agent_id, score, logs) VALUES (?, ?, ?, ?, ?)",
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

    # round_results replaces rank_policies
    # (round_id, policy_version_id, player_id, rank, score)
    round_results = [
        (1, 1, 1, 1, 3.0),   # Round 1: AlphaStrike 1st
        (1, 4, 2, 2, 1.0),   # Round 1: TurtleShell 2nd
        (1, 8, 5, 3, 2.0),   # Round 1: SniperBot 3rd
        (2, 1, 1, 2, 2.0),   # Round 2: AlphaStrike 2nd
        (2, 4, 2, 1, 2.0),   # Round 2: TurtleShell 1st
        (2, 8, 5, 3, 2.0),   # Round 2: SniperBot 3rd
        (3, 2, 1, 3, 1.0),   # Oxygen Round 1: DefendBot 3rd
        (3, 5, 3, 1, 3.0),   # Oxygen Round 1: Blitz-v3 1st
        (3, 9, 5, 2, 2.0),   # Oxygen Round 1: TankBot 2nd
    ]
    c.executemany(
        "INSERT INTO round_results (round_id, policy_version_id, player_id, rank, score) VALUES (?, ?, ?, ?, ?)",
        round_results,
    )

    # Pools for round 1 (simple arena)
    pools = [
        (1, 0, "Arena", "arena", 1, '{}', "completed"),
        (2, 0, "Arena", "arena", 1, '{}', "completed"),
    ]
    c.executemany(
        "INSERT INTO pools (round_id, pool_index, label, pool_type, variant_id, config, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        pools,
    )

    pool_entries = [
        (1, 1, 1, 1, 0),   # Pool 1: AlphaStrike
        (1, 9, 4, 2, 1),   # Pool 1: TurtleShell
        (1, 6, 8, 5, 2),   # Pool 1: SniperBot
        (2, 1, 1, 1, 0),   # Pool 2: AlphaStrike
        (2, 9, 4, 2, 1),   # Pool 2: TurtleShell
        (2, 6, 8, 5, 2),   # Pool 2: SniperBot
    ]
    c.executemany(
        "INSERT INTO pool_entries (pool_id, division_entry_id, policy_version_id, player_id, seed_order) VALUES (?, ?, ?, ?, ?)",
        pool_entries,
    )

    # Episode requests (replacing experience_requests)
    episode_requests = [
        (None, 1, 1, None, None, '[0, 1]', 42, None, "completed"),
        (None, 2, 2, None, None, '[0, 1]', None, None, "completed"),
        (None, 1, 1, None, None, '[0, 1, 2, 3]', 99, None, "completed"),
        (None, 3, 3, None, None, '[0, 1]', None, None, "completed"),
    ]
    c.executemany(
        "INSERT INTO episode_requests (pool_id, variant_id, requester_user_id, player_id, job_index, assignments, seed, max_steps, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        episode_requests,
    )

    episode_request_policies = [
        (1, 0, 1),  # Request 1: AlphaStrike at position 0
        (1, 1, 2),  # Request 1: DefendBot at position 1
        (2, 0, 6),  # Request 2: SwarmAI at position 0
        (2, 1, 7),  # Request 2: HiveMind at position 1
        (3, 0, 1),  # Request 3: AlphaStrike
        (3, 1, 2),  # Request 3: DefendBot
        (3, 2, 4),  # Request 3: TurtleShell
        (3, 3, 8),  # Request 3: SniperBot
        (4, 0, 8),  # Request 4: SniperBot
        (4, 1, 9),  # Request 4: TankBot
    ]
    c.executemany(
        "INSERT INTO episode_request_policies (episode_request_id, position, policy_version_id) VALUES (?, ?, ?)",
        episode_request_policies,
    )

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_db()
