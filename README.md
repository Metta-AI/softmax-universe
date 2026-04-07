# softmax-universe

Game service ontology and admin dashboard for managing users, players, policies, games, leagues, and tournaments.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Start the web server (creates DB on first run)
ontology start

# Reset the database with seed data
ontology reset
```

The dashboard will be available at http://localhost:8777.

Set `ONTOLOGY_PORT` to change the port.

## Data Model

- **Users** own **Players**, who create **Policies** (bots)
- **Games** have **Mods** and **Variants**
- **Leagues** contain **Divisions** and **Pools**
- **Submissions** flow through placement into divisions
- **Episodes** and **Rounds** track match results
- **Rankings** track user/player/policy standings per league
