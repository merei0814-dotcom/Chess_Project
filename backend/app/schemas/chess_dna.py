from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    games_played: int
    known_results: int
    wins: int
    draws: int
    losses: int
    score_rate_pct: float


class ReportSummary(BaseModel):
    total_games: int
    analyzed_games: int
    overall_score_rate_pct: float
    average_game_length: float
    average_loss_length: float
    endgame_frequency_pct: float
    confidence_pct: int


class StyleProfile(BaseModel):
    label: Literal["Tactical", "Positional", "Balanced"]
    player_move_count: int
    player_capture_count: int
    player_check_count: int
    capture_rate_per_move: float
    check_rate_per_move: float
    forcing_move_rate: float
    confidence_pct: int
    sample_size: int
    evidence: list[str]


class PerformanceMetric(BaseModel):
    label: str
    games_played: int
    wins: int
    draws: int
    losses: int
    score_rate_pct: float
    overall_score_rate_pct: float
    score_delta_pct: float
    confidence_pct: int
    severity: float


class OpeningMetric(PerformanceMetric):
    opening: str
    eco: str | None = None


class ColorMetric(PerformanceMetric):
    color: Literal["white", "black"]


class PhaseMetric(PerformanceMetric):
    phase: Literal["opening", "middlegame", "endgame"]
    heuristic: str


class Insight(BaseModel):
    id: str
    title: str
    description: str
    category: str
    evidence: list[str]
    sample_size: int
    confidence_pct: int
    severity: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class MistakePattern(BaseModel):
    id: str
    title: str
    description: str
    evidence: list[str]
    sample_size: int
    confidence_pct: int
    severity: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class ImprovementPriority(BaseModel):
    id: str
    title: str
    reason: str
    recommended_action: str
    related_weakness_ids: list[str]
    sample_size: int
    confidence_pct: int
    severity: float


class OpeningSection(BaseModel):
    all_openings: list[OpeningMetric]
    best_openings: list[OpeningMetric]
    worst_openings: list[OpeningMetric]


class ColorSection(BaseModel):
    white: ColorMetric
    black: ColorMetric
    best_color: ColorMetric | None
    worst_color: ColorMetric | None


class PhaseSection(BaseModel):
    opening: PhaseMetric
    middlegame: PhaseMetric
    endgame: PhaseMetric


class ChessDNAReportV2(BaseModel):
    version: Literal["chess_dna_v2"] = "chess_dna_v2"
    generated_at: str
    analyzed_player: str
    summary: ReportSummary
    style: StyleProfile
    openings: OpeningSection
    colors: ColorSection
    phases: PhaseSection
    strengths: list[Insight]
    weaknesses: list[Insight]
    most_common_mistakes: list[MistakePattern]
    improvement_priorities: list[ImprovementPriority]

