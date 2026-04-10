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

    def test_submission_only_creates_entry_until_placement(self):
        policy_version_id = server.mutate(
            "INSERT INTO policy_versions (player_id, name) VALUES (?, ?)",
            (1, "PlacementTest"),
        )

        handler = server.Handler.__new__(server.Handler)
        submission = handler.handle_mutation(
            "/api/players/1/submit",
            {"policy_version_id": policy_version_id, "league_id": 1},
        )

        entries = server.query(
            """
            SELECT de.*
            FROM division_entries de
            WHERE de.policy_version_id=? AND de.league_id=?
            """,
            (policy_version_id, 1),
        )
        self.assertEqual(entries, [])

        result = handler.handle_mutation(
            f"/api/submissions/{submission['id']}/place",
            {"division_id": 2},
        )

        entries = server.query(
            """
            SELECT de.*
            FROM division_entries de
            WHERE de.policy_version_id=? AND de.is_active=1
            ORDER BY de.division_id
            """,
            (policy_version_id,),
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["division_id"], 2)
        self.assertEqual(entries[0]["is_champion"], 0)

        submissions = server.query(
            "SELECT status, division_entry_id FROM submissions WHERE id=?",
            (submission["id"],),
        )
        self.assertEqual(submissions[0]["status"], "placed")
        self.assertEqual(submissions[0]["division_entry_id"], result["division_entry_id"])

    def test_player_rankings_are_derived_from_round_results(self):
        handler = server.Handler.__new__(server.Handler)
        player_rankings = handler.handle_api("/api/rank_players")

        self.assertTrue(
            any(
                row["division_id"] == 1
                and row["round_id"] == 1
                and row["player_id"] == 1
                and row["rank"] == 1
                for row in player_rankings
            )
        )
        self.assertTrue(
            any(
                row["division_id"] == 2
                and row["round_id"] == 3
                and row["player_id"] == 1
                and row["rank"] == 3
                for row in player_rankings
            )
        )
        self.assertFalse(any(row["player_id"] == 4 for row in player_rankings))

    def test_user_rankings_are_derived_from_round_results(self):
        handler = server.Handler.__new__(server.Handler)
        user_rankings = handler.handle_api("/api/rank_users")

        self.assertTrue(
            any(
                row["division_id"] == 1
                and row["round_id"] == 1
                and row["user_id"] == 1
                and row["rank"] == 1
                for row in user_rankings
            )
        )
        self.assertTrue(
            any(
                row["division_id"] == 2
                and row["round_id"] == 3
                and row["user_id"] == 1
                and row["rank"] == 3
                for row in user_rankings
            )
        )
        self.assertTrue(
            any(
                row["division_id"] == 1
                and row["round_id"] == 1
                and row["user_id"] == 2
                and row["rank"] == 2
                for row in user_rankings
            )
        )


if __name__ == "__main__":
    unittest.main()
