import shutil
import tempfile
import unittest
from pathlib import Path

from ontology import db, server


class OntologyTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.original_db_data_dir = db.DATA_DIR
        self.original_db_path = db.DB_PATH
        self.original_server_data_dir = server.DATA_DIR
        self.original_server_db_path = server.DB_PATH

        db.DATA_DIR = self.tempdir
        db.DB_PATH = str(Path(self.tempdir) / "ontology.db")
        server.DATA_DIR = self.tempdir
        server.DB_PATH = db.DB_PATH
        db.create_db()

    def tearDown(self):
        db.DATA_DIR = self.original_db_data_dir
        db.DB_PATH = self.original_db_path
        server.DATA_DIR = self.original_server_data_dir
        server.DB_PATH = self.original_server_db_path
        shutil.rmtree(self.tempdir)

    def test_submission_only_creates_league_membership_until_placement(self):
        policy_id = server.mutate(
            "INSERT INTO policies (player_id, name) VALUES (?, ?)",
            (1, "PlacementTest"),
        )

        handler = server.Handler.__new__(server.Handler)
        submission = handler.handle_mutation(
            "/api/players/1/submit",
            {"policy_id": policy_id, "league_id": 1},
        )

        memberships = server.query(
            """
            SELECT dp.*
            FROM division_policies dp
            JOIN divisions d ON d.id = dp.division_id
            WHERE dp.policy_id=? AND d.league_id=?
            """,
            (policy_id, 1),
        )
        self.assertEqual(memberships, [])

        handler.handle_mutation(
            f"/api/submissions/{submission['id']}/place",
            {"division_id": 2},
        )

        memberships = server.query(
            """
            SELECT dp.*
            FROM division_policies dp
            WHERE dp.policy_id=?
            ORDER BY dp.division_id
            """,
            (policy_id,),
        )
        self.assertEqual(len(memberships), 1)
        self.assertEqual(memberships[0]["division_id"], 2)
        self.assertEqual(memberships[0]["is_champion"], 0)

        submissions = server.query(
            "SELECT status FROM submissions WHERE id=?",
            (submission["id"],),
        )
        self.assertEqual(submissions[0]["status"], "placed")

    def test_player_rankings_are_derived_from_policy_rankings(self):
        handler = server.Handler.__new__(server.Handler)
        player_rankings = handler.handle_api("/api/rank_players")

        self.assertTrue(
            any(
                row["league_id"] == 1
                and row["division_id"] == 1
                and row["timestamp"] == "2026-04-01 12:00:00"
                and row["player_id"] == 1
                and row["rank"] == 1
                for row in player_rankings
            )
        )
        self.assertTrue(
            any(
                row["league_id"] == 1
                and row["division_id"] == 2
                and row["timestamp"] == "2026-04-01 12:00:00"
                and row["player_id"] == 1
                and row["rank"] == 4
                for row in player_rankings
            )
        )
        self.assertFalse(any(row["player_id"] == 2 for row in player_rankings))

    def test_user_rankings_are_derived_from_policy_rankings(self):
        handler = server.Handler.__new__(server.Handler)
        user_rankings = handler.handle_api("/api/rank_users")

        self.assertTrue(
            any(
                row["league_id"] == 1
                and row["division_id"] == 1
                and row["timestamp"] == "2026-04-01 12:00:00"
                and row["user_id"] == 1
                and row["rank"] == 1
                for row in user_rankings
            )
        )
        self.assertTrue(
            any(
                row["league_id"] == 1
                and row["division_id"] == 2
                and row["timestamp"] == "2026-04-01 12:00:00"
                and row["user_id"] == 1
                and row["rank"] == 4
                for row in user_rankings
            )
        )
        self.assertTrue(
            any(
                row["league_id"] == 1
                and row["division_id"] == 1
                and row["timestamp"] == "2026-04-01 12:00:00"
                and row["user_id"] == 2
                and row["rank"] == 2
                for row in user_rankings
            )
        )


if __name__ == "__main__":
    unittest.main()
