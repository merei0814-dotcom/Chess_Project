# CHESS AI COACH PRD

## Product Positioning

CHESS AI COACH is an AI chess coach that helps serious players improve and prepare for opponents.

The product promise:

> A grandmaster coach that knows every game I have ever played.

We are not building a chess server, social network, tournament platform, or Chess.com/Lichess clone. The MVP wins by producing insight players cannot easily get elsewhere.

## Target Users

Primary users:

- Chess.com players
- Lichess players
- FIDE and tournament players
- Ambitious improvers rated 800-2500+

Best early adopter:

- A tournament player or serious online player who has a real upcoming opponent and will pay for preparation.

## Core User Problems

Players have many games but little clarity:

- They do not know their repeatable weaknesses.
- They do not know what to study next.
- They prepare openings blindly.
- They cannot quickly understand an opponent's habits.
- Engine analysis is too raw and does not behave like a coach.

## MVP Features

### 1. Chess DNA Analysis

Inputs:

- Chess.com username
- Lichess username
- PGN upload

Outputs:

- Strengths
- Weaknesses
- Training priorities
- Typical mistakes
- Opening performance
- Middlegame performance
- Endgame performance
- Time management tendencies
- Personalized recommendations

Success criteria:

- A user feels the report accurately describes their playing personality.
- The report gives 3-5 concrete next training priorities.
- The user can understand it without engine jargon.

### 2. Opponent Intelligence

Inputs:

- FIDE ID
- Chess.com username
- Lichess username

Outputs:

- Opening repertoire
- Favorite structures
- Weak structures
- Recurring mistakes
- Time pressure mistakes
- Tactical weaknesses
- Strategic weaknesses
- Practical recommendations

Success criteria:

- A player can prepare for an opponent in under 10 minutes.
- The report answers "what should I play and what should I avoid?"

### 3. Tournament Preparation Report

Outputs:

- What to play
- What to avoid
- Positions to seek
- Positions to avoid
- Most likely openings
- Critical weaknesses
- Practical game strategy

Success criteria:

- Feels like a human coach wrote it.
- Can be exported or shared as a premium report.
- Avoids raw centipawn and engine-dump language.

### 4. AI Chess Coach

The coach answers questions using:

- User games
- User weaknesses
- User strengths
- Opponent analysis
- Generated reports

Success criteria:

- The user asks follow-up questions after reading a report.
- The coach references user-specific patterns, not generic chess advice.

## Explicit Non-Goals For MVP

Reject these until after launch traction:

- Multiplayer
- Social network
- Tournaments
- Game server
- Friends system
- Elo system
- Chat rooms
- Streaming
- Native mobile app

Reason: these features create platform complexity without proving the core paid insight loop.

## Monetization Hypothesis

Initial paid offers:

- Free preview: limited Chess DNA summary from a small game sample.
- Paid report: full Chess DNA or opponent report.
- Subscription: continuous game tracking, AI coach memory, monthly reports.
- Tournament pack: multiple opponent prep reports before an event.

Recommended MVP pricing tests:

- $9-$19 one-time opponent report.
- $19-$39/month serious improver subscription.
- $49-$99 tournament preparation pack.

## Key Metrics

Activation:

- User connects account or uploads PGN.
- User receives first useful report.

Retention:

- User returns after new games.
- User asks coach follow-up questions.
- User generates opponent reports before events.

Revenue:

- Free-to-paid conversion.
- Report purchase rate.
- Subscription conversion after first report.

Quality:

- User rates report accuracy.
- User says recommendation was actionable.
- Low hallucination rate in coach answers.

## MVP Risk Register

Biggest risks:

- Reports feel generic.
- Analysis pipeline is too slow.
- Game ingestion from external services is unreliable.
- Engine analysis becomes expensive.
- AI coach invents unsupported claims.

Mitigations:

- Store structured evidence for every insight.
- Show top supporting games or positions.
- Analyze representative samples before full historical depth.
- Cache imported games and derived features.
- Use constrained report schemas before generating prose.

