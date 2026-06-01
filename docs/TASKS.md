# CHESS AI COACH TASKS

## Immediate Foundation

- [ ] Create `frontend/` Next.js 15 app with TypeScript.
- [ ] Add Tailwind CSS, shadcn/ui, and Framer Motion.
- [ ] Create `backend/` FastAPI app.
- [ ] Create `database/` migrations folder.
- [ ] Add local development README.
- [ ] Add environment variable templates.

## Product And Design

- [ ] Define dashboard information architecture.
- [ ] Design dark premium shell.
- [ ] Design import flow for username and PGN upload.
- [ ] Design Chess DNA report page.
- [ ] Design opponent report page.
- [ ] Define report confidence and feedback UI.

## Backend

- [x] Add FastAPI health endpoint.
- [ ] Add Clerk token verification.
- [x] Add PostgreSQL connection layer.
- [x] Add migration tooling.
- [x] Create core database schema.
- [ ] Add analysis job table and worker polling.
- [ ] Add structured logging.

## Chess Ingestion

- [x] Implement PGN upload.
- [x] Parse PGN with python-chess.
- [x] Normalize players, colors, results, dates, ratings, time controls.
- [ ] Implement Chess.com game import.
- [ ] Implement Lichess game import.
- [x] Deduplicate games by PGN hash inside an import.

## Analysis

- [x] Extract opening names and ECO codes where available.
- [x] Calculate performance by color.
- [x] Calculate performance by opening.
- [ ] Classify games by phase failure where possible.
- [x] Detect basic tactical vs positional tendencies.
- [ ] Add selective Stockfish evaluation for critical moments.
- [x] Generate structured Chess DNA insights.
- [x] Add Chess DNA v2 target-player-only metrics.
- [x] Add confidence scores to insights.
- [x] Rank strengths and weaknesses by severity.
- [x] Add phase performance heuristics.

## Reports

- [x] Create report schema.
- [x] Generate first Chess DNA report.
- [x] Create machine-readable Chess DNA v2 Pydantic schema.
- [x] Create machine-readable Opponent Intelligence schema.
- [x] Generate structured Opponent Intelligence report.
- [ ] Render report in frontend.
- [ ] Add report feedback.
- [x] Add opponent intelligence report.
- [ ] Add tournament preparation report.

## Opponent Intelligence

- [x] Add opponent PGN upload endpoint.
- [x] Infer opponent from uploaded PGN.
- [x] Store opponent report separately from Chess DNA report.
- [x] Analyze White opening repertoire.
- [x] Analyze Black responses against `1. e4`.
- [x] Analyze Black responses against `1. d4`.
- [x] Rank best and worst openings by sample, score, and confidence.
- [x] Detect weak openings, color gaps, poor endgame results, and short-loss patterns.
- [x] Generate rule-based preparation recommendations.

## AI Coach

- [ ] Create coach retrieval model from reports and findings.
- [ ] Add coach chat API.
- [ ] Add guardrails against unsupported claims.
- [ ] Add coach UI.
- [ ] Add conversation persistence.

## Monetization

- [ ] Define free preview limits.
- [ ] Add usage limits.
- [ ] Add payment provider integration.
- [ ] Add subscription plans.
- [ ] Add one-time report purchase.

## Launch

- [ ] Create landing page focused on tournament prep and improvement.
- [ ] Add analytics.
- [ ] Add error tracking.
- [ ] Recruit first 20 beta users.
- [ ] Collect report accuracy feedback.
- [ ] Convert first paid users.

## Features To Reject Until Later

- [ ] Multiplayer
- [ ] Social feed
- [ ] Friends system
- [ ] Elo system
- [ ] Chat rooms
- [ ] Streaming
- [ ] Native mobile app
- [ ] Tournament hosting
