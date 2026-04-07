#!/usr/bin/env python3
"""CLI entry point for the ontology service."""

import sys
import os
import signal

PID_FILE = os.path.join(os.path.expanduser("~"), ".softmax-universe", "ontology.pid")


def main():
    if len(sys.argv) < 2:
        print("Usage: ontology <command>")
        print("Commands:")
        print("  start    Start the web server (background)")
        print("  stop     Stop the web server")
        print("  restart  Restart the web server")
        print("  reset    Reset the database with seed data")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "restart":
        stop()
        start()
    elif cmd == "reset":
        reset()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


def _read_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None


def _is_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start():
    from ontology.db import DB_PATH, DATA_DIR, create_db

    pid = _read_pid()
    if pid and _is_running(pid):
        print(f"Already running (pid {pid})")
        return

    if not os.path.exists(DB_PATH):
        print("No database found, creating with seed data...")
        create_db()

    child = os.fork()
    if child > 0:
        # Parent — write pid and exit
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write(str(child))
        port = int(os.environ.get("ONTOLOGY_PORT", 8777))
        print(f"Ontology server started (pid {child}) at http://localhost:{port}")
        return

    # Child — detach and run server
    os.setsid()
    from http.server import HTTPServer
    from ontology.server import Handler

    port = int(os.environ.get("ONTOLOGY_PORT", 8777))
    server = HTTPServer(("", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    os._exit(0)


def stop():
    pid = _read_pid()
    if not pid or not _is_running(pid):
        print("Not running.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return
    os.kill(pid, signal.SIGTERM)
    print(f"Stopped (pid {pid})")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def reset():
    from ontology.db import create_db

    create_db()
    print("Database reset with seed data.")


if __name__ == "__main__":
    main()
