# Agents Guide

## Project Structure

```
src/ontology/
  cli.py      - CLI entry point (ontology start/reset)
  db.py       - SQLite schema and seed data
  server.py   - HTTP server with REST API and mutation handlers
  ui.html     - Single-file SPA dashboard
```

## Architecture

- **Backend**: Python stdlib only (http.server, sqlite3). No frameworks.
- **Frontend**: Single HTML file with inline CSS/JS. No build step.
- **Database**: SQLite stored at `~/.softmax-universe/ontology.db`.
- **API**: GET endpoints at `/api/<table>`, POST mutations at `/api/<resource>/<action>`.

## Key Patterns

- All tables have `notes` and `created_at` fields.
- The UI is a client-side SPA with hash-free routing (e.g., `/users/1`).
- Server acts as SPA fallback — all non-API routes serve `ui.html`.
- Mutations use `POST` with JSON bodies. `fetchAll()` refreshes all state after each mutation.

## Adding a New Table

1. Add `CREATE TABLE` in `db.py`
2. Add seed data in `db.py`
3. Add GET endpoint in `server.py` `handle_api()`
4. Add to `endpoints` array in `ui.html`
5. Add badge element in sidebar
6. Add list + detail render functions
7. Register in `listViews` and `detailViews`
