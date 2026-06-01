from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OpponentSummary(BaseModel):
    opponent_name: str
    total_games: int
    analyzed_games: int
    rating_min: int | None
    rating_max: int | None
    rating_range: str | None
    preferred_color: Literal["white", "black", "balanced", "unknown"]
    white_games: int
    black_games: int
    overall_score_rate_pct: float
    confidence_pct: int


class OpponentOpeningMetric(BaseModel):
    label: str
    color: Literal["white", "black"]
    opening: str
    eco: str | None = None
    first_white_move: str | None = None
    black_response: str | None = None
    games_played: int
    frequency_pct: float
    wins: int
    draws: int
    losses: int
    score_rate_pct: float
    score_delta_pct: float
    confidence_pct: int
    rank_score: float


class WhiteRepertoire(BaseModel):
    most_played_openings: list[OpponentOpeningMetric]


class BlackRepertoire(BaseModel):
    responses_against_e4: list[OpponentOpeningMetric]
    responses_against_d4: list[OpponentOpeningMetric]


class OpeningRepertoire(BaseModel):
    as_white: WhiteRepertoire
    as_black: BlackRepertoire


class RiskArea(BaseModel):
    id: str
    category: str
    title: str
    description: str
    evidence: list[str]
    sample_size: int
    confidence_pct: int
    severity: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class PreparationRecommendation(BaseModel):
    id: str
    action: str
    rationale: str
    evidence: list[str]
    source_rule: str
    sample_size: int
    confidence_pct: int
    severity: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class OpponentIntelligenceReport(BaseModel):
    version: Literal["opponent_intelligence_v1"] = "opponent_intelligence_v1"
    generated_at: str
    opponent_name: str
    summary: OpponentSummary
    opening_repertoire: OpeningRepertoire
    best_performing_openings: list[OpponentOpeningMetric]
    worst_performing_openings: list[OpponentOpeningMetric]
    risk_areas: list[RiskArea]
    preparation_recommendations: list[PreparationRecommendation]

