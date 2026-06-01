# Backend

FastAPI backend for the smallest CHESS AI COACH validation slice:

`PGN upload -> stored games -> Chess DNA report`

## Run Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default the app uses local SQLite at `backend/chess_ai_coach.db`.

For PostgreSQL, set:

```bash
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/chess_ai_coach
```

## API

Health:

```bash
GET /health
```

Upload PGN and generate Chess DNA:

```bash
POST /api/imports/pgn
Content-Type: multipart/form-data

file: games.pgn
player_name: optional
```

Fetch report:

```bash
GET /api/reports/{import_id}
```

The active report format is `chess_dna_v2`. It is machine-readable and includes confidence-scored openings, colors, phases, strengths, weaknesses, mistake patterns, and improvement priorities.

Upload opponent PGN and generate Opponent Intelligence:

```bash
POST /api/opponents/pgn
Content-Type: multipart/form-data

file: opponent_games.pgn
opponent_name: optional
```

Fetch opponent report:

```bash
GET /api/opponents/reports/{import_id}
```

The opponent report is generated entirely from structured PGN evidence. It does not use LLMs.
