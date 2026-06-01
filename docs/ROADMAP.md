# CHESS AI COACH ROADMAP

## 90-Day Objective

Launch a paid MVP that lets chess players generate accurate, beautiful, coach-like reports from their own games and opponent games.

The revenue test is simple:

Can we get serious players to pay for preparation and improvement insight?

## Month 1: Data Foundation And Chess DNA

Goal:

Ship the first useful user report.

Scope:

- Project scaffold: frontend, backend, database, docs.
- Clerk authentication.
- PostgreSQL schema for users, accounts, games, analyses, reports, jobs.
- Chess.com game import.
- Lichess game import.
- PGN upload.
- PGN parsing with python-chess.
- Basic feature extraction.
- Basic Chess DNA report.
- Dark premium dashboard shell.

Quality bar:

- Import at least 100 games for a user.
- Generate a structured analysis from those games.
- Produce human-readable strengths, weaknesses, and priorities.

Do not build:

- Live games.
- Social features.
- Advanced coach chat.
- Full payment stack.

## Month 2: Opponent Intelligence And Reports

Goal:

Make the product valuable for real tournament preparation.

Scope:

- Opponent profile creation.
- Opponent game ingestion from Chess.com/Lichess/PGN.
- Opening repertoire detection.
- Recurring mistake clustering.
- Time-pressure tendency detection when clock data exists.
- Tournament preparation report.
- Beautiful report UI.
- PDF or print-friendly report export.
- Report accuracy feedback.

Quality bar:

- A user can enter an opponent and get a useful prep plan in under 10 minutes.
- The report clearly says what to play, avoid, seek, and avoid.

Do not build:

- Native mobile app.
- Team workspaces.
- Public profile pages.
- Tournament management.

## Month 3: AI Coach And Monetization

Goal:

Turn reports into a paid coaching workflow.

Scope:

- AI coach chat with retrieval from user analysis and reports.
- Guardrails to cite only known user/opponent evidence.
- Subscription and one-time payment options.
- Stripe or equivalent payment integration.
- Usage limits by plan.
- Landing page focused on paid conversion.
- Public launch analytics.

Quality bar:

- Coach answers feel personal and evidence-based.
- Users can pay without manual intervention.
- The funnel from import to paid report is measurable.

Do not build:

- Marketplace.
- Coach directory.
- Community feed.
- Complex CRM.

## Near-Term Build Order

1. Create monorepo structure.
2. Scaffold Next.js frontend.
3. Scaffold FastAPI backend.
4. Define database schema.
5. Implement PGN upload first.
6. Implement Chess.com import.
7. Implement Lichess import.
8. Build analysis job pipeline.
9. Generate first Chess DNA report.
10. Design dashboard and report page.

## CTO Recommendation

Start with PGN upload plus Chess.com import before Lichess.

Why:

- PGN upload lets us test the core analysis loop without external API fragility.
- Chess.com username import is highly recognizable for early users.
- Lichess can follow once the data model is proven.

