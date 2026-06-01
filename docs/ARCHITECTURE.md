# CHESS AI COACH ARCHITECTURE

## Architecture Principles

- Insight quality beats feature breadth.
- Analysis must be evidence-based and repeatable.
- Slow work runs asynchronously.
- The database stores structured findings before prose is generated.
- Every AI-generated claim should trace back to games, positions, or aggregated metrics.
- MVP infrastructure should be simple enough to ship in 90 days.

## System Overview

Frontend:

- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Clerk for authentication
- Hosted on Vercel

Backend:

- FastAPI
- Python
- python-chess
- Stockfish
- OpenAI and Claude for report generation and coach responses
- Hosted on Railway

Database:

- PostgreSQL
- Source of truth for users, imports, games, positions, features, reports, and jobs

Worker:

- Python worker on Railway
- Pulls pending jobs from PostgreSQL
- Imports games, parses PGN, runs analysis, writes structured results

## Request Flow

1. User signs in with Clerk.
2. Frontend calls FastAPI with Clerk identity token.
3. User creates an import from username or PGN upload.
4. Backend creates an analysis job in PostgreSQL.
5. Worker picks up the job.
6. Worker fetches or parses games.
7. Worker extracts chess features.
8. Optional Stockfish pass evaluates critical positions.
9. Backend stores structured insights.
10. AI report generator turns structured insights into human coaching language.
11. Frontend shows the report and coach follow-up interface.

## Current MVP Vertical Slice

The first implemented slice is intentionally simpler:

1. User uploads a PGN file.
2. FastAPI parses games with python-chess.
3. The backend stores the import and normalized games.
4. The backend generates a deterministic Chess DNA v2 report.
5. The report can be fetched by `import_id`.

This path is synchronous for speed of validation. The schema keeps imports, games, and reports separate so the same flow can move to a background worker when Chess.com/Lichess imports and Stockfish analysis are added.

Not implemented in this slice:

- Authentication
- AI coach chat
- Payments
- Stockfish analysis

## Chess DNA v2 Metrics

Chess DNA v2 avoids mixing opponent behavior into player style metrics. PGN parsing stores move, capture, and check counts separately for White and Black. Report generation selects the counters for the analyzed player's color in each game.

Confidence uses a capped sample-size curve:

`confidence = min(0.95, sqrt(sample_size / target_sample_size))`

Strength and weakness severity uses:

`severity = abs(score_delta) * sample_weight * confidence`

where:

- `score_delta = segment_score_rate - overall_score_rate`
- `sample_weight = min(1.0, sqrt(sample_size / target_sample_size))`

Openings, colors, phases, mistakes, strengths, weaknesses, and priorities are emitted as machine-readable Pydantic models.

## Opponent Intelligence MVP

The opponent pipeline uses the same PGN ingestion foundation:

1. User uploads opponent PGN.
2. FastAPI infers the opponent from the most frequent player name, or uses an optional provided name.
3. Games are stored with the opponent as the analyzed player.
4. The report generator builds a structured preparation report.
5. Recommendations are generated from rules and evidence only.

The PGN parser stores:

- first White move
- Black's first response
- side-specific move counters
- opening and ECO headers when present

Opponent Intelligence outputs:

- opponent summary
- White opening repertoire
- Black responses against `1. e4` and `1. d4`
- best performing openings
- worst performing openings
- risk areas
- preparation recommendations with confidence scores

No LLMs are used for opponent reports in the MVP.

## Core Data Model

Recommended first tables:

- users
- linked_accounts
- game_imports
- games
- game_players
- positions
- analysis_jobs
- player_profiles
- opponent_profiles
- reports
- report_feedback
- coach_messages

Important design choice:

Store raw games separately from derived insights. Derived insights can be recalculated as analysis improves.

## Analysis Pipeline

Stages:

1. Ingestion
2. Normalization
3. Feature extraction
4. Pattern aggregation
5. Engine sampling
6. Insight generation
7. Report generation

Feature examples:

- Opening frequency and score
- Color-specific performance
- Game phase mistake rate
- Time usage by phase when clock data exists
- Tactical motif exposure
- Endgame conversion
- Blunder recovery rate
- Repeated pawn structures
- Opponent repertoire frequency

## AI Design

Do not ask the LLM to "analyze chess games" from raw PGN as the primary method.

Better approach:

1. Python and Stockfish produce structured evidence.
2. The LLM converts evidence into coach-like explanations.
3. The coach chat retrieves relevant findings and supporting games.

Reason:

- Cheaper
- More accurate
- Easier to debug
- Less hallucination risk
- Stronger product trust

## Architecture Alternatives Considered

### Celery + Redis

Pros:

- Mature job processing.
- Good retry and scaling patterns.

Cons:

- Extra infrastructure before product-market signal.
- More deployment surface area.

Decision:

- Defer until job volume requires it.

### Serverless API Only

Pros:

- Simple frontend deployment.

Cons:

- Bad fit for long-running imports, Stockfish, and analysis jobs.

Decision:

- Do not run analysis inside request/response handlers.

### Full Engine Analysis For Every Move

Pros:

- High chess accuracy.

Cons:

- Expensive and slow.
- Overkill for early product validation.

Decision:

- Use selective engine sampling for critical positions first.

### LLM-Only Analysis

Pros:

- Fast to prototype.

Cons:

- Generic output.
- Hallucination risk.
- Weak chess reliability.

Decision:

- Use LLMs for explanation, not as the source of truth.

## Security And Privacy

- Authenticate all user-specific endpoints.
- Do not expose private imports across users.
- Store API secrets only in environment variables.
- Do not store unnecessary external credentials.
- Treat uploaded PGNs as private user data.

## Product Quality Rules

- Reports must avoid engine jargon by default.
- Any strong claim should have supporting evidence.
- Empty or low-data reports should clearly say confidence is limited.
- The UI should feel premium, calm, and professional.
- No wooden boards, cartoon chess pieces, bright chess motifs, or social clutter.
