#!/usr/bin/env python3
"""CLI entry point for the ontology service."""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: ontology <command>")
        print("Commands:")
        print("  start    Start the web server")
        print("  reset    Reset the database with seed data")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        start()
    elif cmd == "reset":
        reset()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


def start():
    from ontology.db import DB_PATH, create_db
    from ontology.server import Handler

    if not os.path.exists(DB_PATH):
        print("No database found, creating with seed data...")
        create_db()

    from http.server import HTTPServer

    port = int(os.environ.get("ONTOLOGY_PORT", 8777))
    server = HTTPServer(("", port), Handler)
    print(f"Ontology server running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


def reset():
    from ontology.db import create_db

    create_db()
    print("Database reset with seed data.")


if __name__ == "__main__":
    main()
