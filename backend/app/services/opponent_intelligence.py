from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

from app.schemas.opponent_intelligence import (
    BlackRepertoire,
    OpeningRepertoire,
    OpponentIntelligenceReport,
    OpponentOpeningMetric,
    OpponentSummary,
    PreparationRecommendation,
    RiskArea,
    WhiteRepertoire,
)
from app.services.chess_dna import (
    infer_analyzed_player,
    player_appears_in_games,
    player_color_for_game,
    result_for_color,
)


REPORT_TARGET_SAMPLE = 50
OPENING_TARGET_SAMPLE = 8
COLOR_TARGET_SAMPLE = 20
ENDGAME_TARGET_SAMPLE = 15
PATTERN_TARGET_SAMPLE = 20


def infer_opponent_name(games: Iterable[Any], requested_opponent_name: str | None = None) -> str:
    return infer_analyzed_player(games, requested_opponent_name)


def opponent_appears_in_games(games: Iterable[Any], opponent_name: str) -> bool:
    return player_appears_in_games(games, opponent_name)


def opponent_color_for_game(game: Any, opponent_name: str) -> str | None:
    return player_color_for_game(game, opponent_name)


def opponent_result_for_color(result: str | None, color: str | None) -> str | None:
    return result_for_color(result, color)


def generate_opponent_intelligence_report(games: list[Any], opponent_name: str) -> dict[str, Any]:
    analyzed_games = [game for game in games if _value(game, "analyzed_player_color") in {"white", "black"}]
    overall = _score_breakdown(analyzed_games)
    overall_score_rate = overall["score_rate_pct"]
    summary = _summary(analyzed_games, opponent_name, overall_score_rate)
    white_openings = _white_openings(analyzed_games, overall_score_rate)
    responses_e4 = _black_responses(analyzed_games, "e4", overall_score_rate)
    responses_d4 = _black_responses(analyzed_games, "d4", overall_score_rate)
    all_opening_metrics = [*white_openings, *responses_e4, *responses_d4]
    best_openings = sorted(
        all_opening_metrics,
        key=lambda metric: metric.rank_score,
        reverse=True,
    )[:5]
    worst_openings = sorted(
        all_opening_metrics,
        key=lambda metric: _weakness_rank_score(metric),
        reverse=True,
    )[:5]
    risk_areas = _risk_areas(
        games=analyzed_games,
        overall_score_rate=overall_score_rate,
        worst_openings=worst_openings,
    )
    recommendations = _recommendations(
        best_openings=best_openings,
        worst_openings=worst_openings,
        risk_areas=risk_areas,
    )

    report = OpponentIntelligenceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        opponent_name=opponent_name,
        summary=summary,
        opening_repertoire=OpeningRepertoire(
            as_white=WhiteRepertoire(most_played_openings=white_openings[:8]),
            as_black=BlackRepertoire(
                responses_against_e4=responses_e4[:8],
                responses_against_d4=responses_d4[:8],
            ),
        ),
        best_performing_openings=best_openings,
        worst_performing_openings=worst_openings,
        risk_areas=risk_areas,
        preparation_recommendations=recommendations,
    )

    return report.model_dump(mode="json")


def _summary(games: list[Any], opponent_name: str, overall_score_rate: float) -> OpponentSummary:
    white_games = [game for game in games if _value(game, "analyzed_player_color") == "white"]
    black_games = [game for game in games if _value(game, "analyzed_player_color") == "black"]
    ratings = [_opponent_rating(game) for game in games]
    ratings = [rating for rating in ratings if rating is not None]

    if len(white_games) > len(black_games) * 1.15:
        preferred_color = "white"
    elif len(black_games) > len(white_games) * 1.15:
        preferred_color = "black"
    elif games:
        preferred_color = "balanced"
    else:
        preferred_color = "unknown"

    rating_min = min(ratings) if ratings else None
    rating_max = max(ratings) if ratings else None

    return OpponentSummary(
        opponent_name=opponent_name,
        total_games=len(games),
        analyzed_games=len(games),
        rating_min=rating_min,
        rating_max=rating_max,
        rating_range=f"{rating_min}-{rating_max}" if rating_min is not None and rating_max is not None else None,
        preferred_color=preferred_color,
        white_games=len(white_games),
        black_games=len(black_games),
        overall_score_rate_pct=overall_score_rate,
        confidence_pct=_confidence_pct(len(games), REPORT_TARGET_SAMPLE),
    )


def _white_openings(games: list[Any], overall_score_rate: float) -> list[OpponentOpeningMetric]:
    white_games = [game for game in games if _value(game, "analyzed_player_color") == "white"]
    grouped: dict[tuple[str | None, str], list[Any]] = defaultdict(list)

    for game in white_games:
        opening = _value(game, "opening") or "Unknown opening"
        eco = _value(game, "eco")
        grouped[(eco, opening)].append(game)

    metrics: list[OpponentOpeningMetric] = []
    for (eco, opening), opening_games in grouped.items():
        label = f"{eco} {opening}" if eco else opening
        metrics.append(
            _opening_metric(
                label=label,
                color="white",
                opening=opening,
                eco=eco,
                first_white_move=_common_value(opening_games, "first_white_move"),
                black_response=None,
                games=opening_games,
                denominator=len(white_games),
                overall_score_rate=overall_score_rate,
            )
        )

    return sorted(metrics, key=lambda metric: (metric.games_played, metric.frequency_pct), reverse=True)


def _black_responses(games: list[Any], first_move: str, overall_score_rate: float) -> list[OpponentOpeningMetric]:
    black_games = [
        game
        for game in games
        if _value(game, "analyzed_player_color") == "black" and _normalized_move(_value(game, "first_white_move")) == first_move
    ]
    grouped: dict[tuple[str | None, str, str | None], list[Any]] = defaultdict(list)

    for game in black_games:
        opening = _value(game, "opening") or "Unknown opening"
        eco = _value(game, "eco")
        response = _value(game, "black_response")
        grouped[(eco, opening, response)].append(game)

    metrics: list[OpponentOpeningMetric] = []
    for (eco, opening, response), response_games in grouped.items():
        response_label = response or "Unknown response"
        label = f"vs {first_move}: {response_label}"
        if eco and opening:
            label = f"{label} ({eco} {opening})"

        metrics.append(
            _opening_metric(
                label=label,
                color="black",
                opening=opening,
                eco=eco,
                first_white_move=first_move,
                black_response=response,
                games=response_games,
                denominator=len(black_games),
                overall_score_rate=overall_score_rate,
            )
        )

    return sorted(metrics, key=lambda metric: (metric.games_played, metric.frequency_pct), reverse=True)


def _opening_metric(
    label: str,
    color: str,
    opening: str,
    eco: str | None,
    first_white_move: str | None,
    black_response: str | None,
    games: list[Any],
    denominator: int,
    overall_score_rate: float,
) -> OpponentOpeningMetric:
    score = _score_breakdown(games)
    confidence = _confidence_pct(score["known_results"], OPENING_TARGET_SAMPLE)
    confidence_fraction = confidence / 100
    sample_weight = _sample_weight(score["known_results"], OPENING_TARGET_SAMPLE)
    rank_score = round(score["score_rate_pct"] * sample_weight * confidence_fraction, 2)

    return OpponentOpeningMetric(
        label=label,
        color=color,
        opening=opening,
        eco=eco,
        first_white_move=first_white_move,
        black_response=black_response,
        games_played=len(games),
        frequency_pct=_percentage(len(games), denominator),
        wins=score["wins"],
        draws=score["draws"],
        losses=score["losses"],
        score_rate_pct=score["score_rate_pct"],
        score_delta_pct=round(score["score_rate_pct"] - overall_score_rate, 1),
        confidence_pct=confidence,
        rank_score=rank_score,
    )


def _risk_areas(
    games: list[Any],
    overall_score_rate: float,
    worst_openings: list[OpponentOpeningMetric],
) -> list[RiskArea]:
    risks: list[RiskArea] = []
    white_games = [game for game in games if _value(game, "analyzed_player_color") == "white"]
    black_games = [game for game in games if _value(game, "analyzed_player_color") == "black"]
    endgame_games = [game for game in games if _value(game, "reached_endgame", False)]
    losses = [game for game in games if _value(game, "analyzed_player_result") == "loss"]
    loss_rate = _percentage(len(losses), len(games))
    average_loss_length = _average(_value(game, "fullmove_count", 0) for game in losses)

    for opening in worst_openings[:3]:
        if opening.games_played >= 3 and opening.score_rate_pct <= 40:
            risks.append(
                RiskArea(
                    id=f"weak_opening_{_slug(opening.label)}",
                    category="weak_opening",
                    title=f"Weak results in {opening.label}",
                    description="This opening or response scores poorly for the opponent.",
                    evidence=[
                        f"{opening.games_played} games.",
                        f"{opening.score_rate_pct}% score rate.",
                        f"{opening.frequency_pct}% frequency in its repertoire bucket.",
                    ],
                    sample_size=opening.games_played,
                    confidence_pct=opening.confidence_pct,
                    severity=_weakness_rank_score(opening),
                    metrics=opening.model_dump(mode="json"),
                )
            )

    risks.extend(
        _color_risk(
            color="white",
            games=white_games,
            overall_score_rate=overall_score_rate,
        )
    )
    risks.extend(
        _color_risk(
            color="black",
            games=black_games,
            overall_score_rate=overall_score_rate,
        )
    )

    endgame_score = _score_breakdown(endgame_games)
    if endgame_score["known_results"] >= 3 and (
        endgame_score["score_rate_pct"] < 45 or endgame_score["score_rate_pct"] <= overall_score_rate - 8
    ):
        confidence = _confidence_pct(endgame_score["known_results"], ENDGAME_TARGET_SAMPLE)
        severity = _severity(overall_score_rate - endgame_score["score_rate_pct"], endgame_score["known_results"], ENDGAME_TARGET_SAMPLE)
        risks.append(
            RiskArea(
                id="poor_endgame_results",
                category="phase",
                title="Poor endgame results",
                description="The opponent underperforms in games that reach the endgame threshold.",
                evidence=[
                    f"{len(endgame_games)} endgame-threshold games.",
                    f"{endgame_score['score_rate_pct']}% score rate vs {overall_score_rate}% overall.",
                ],
                sample_size=len(endgame_games),
                confidence_pct=confidence,
                severity=severity,
                metrics=endgame_score,
            )
        )

    if len(losses) >= 3 and loss_rate >= 35 and average_loss_length < 25:
        confidence = _confidence_pct(len(losses), PATTERN_TARGET_SAMPLE)
        severity = round(((loss_rate - 35) + (25 - average_loss_length)) * (confidence / 100), 2)
        risks.append(
            RiskArea(
                id="short_loss_pattern",
                category="loss_pattern",
                title="Short-loss pattern",
                description="A meaningful share of the opponent's losses end before move 25.",
                evidence=[
                    f"{len(losses)} losses.",
                    f"{loss_rate}% loss rate.",
                    f"Average loss length is {round(average_loss_length, 1)} moves.",
                ],
                sample_size=len(losses),
                confidence_pct=confidence,
                severity=max(severity, 1.0),
                metrics={
                    "loss_rate_pct": loss_rate,
                    "average_loss_length": round(average_loss_length, 1),
                },
            )
        )

    return sorted(risks, key=lambda risk: risk.severity, reverse=True)[:7]


def _color_risk(color: str, games: list[Any], overall_score_rate: float) -> list[RiskArea]:
    score = _score_breakdown(games)
    if score["known_results"] < 3:
        return []

    if score["score_rate_pct"] >= 45 and score["score_rate_pct"] > overall_score_rate - 8:
        return []

    confidence = _confidence_pct(score["known_results"], COLOR_TARGET_SAMPLE)
    severity = _severity(overall_score_rate - score["score_rate_pct"], score["known_results"], COLOR_TARGET_SAMPLE)

    return [
        RiskArea(
            id=f"poor_{color}_performance",
            category="color",
            title=f"Poor {color.capitalize()} performance",
            description=f"The opponent scores poorly as {color.capitalize()}.",
            evidence=[
                f"{len(games)} games as {color.capitalize()}.",
                f"{score['score_rate_pct']}% score rate vs {overall_score_rate}% overall.",
            ],
            sample_size=len(games),
            confidence_pct=confidence,
            severity=max(severity, 1.0),
            metrics=score,
        )
    ]


def _recommendations(
    best_openings: list[OpponentOpeningMetric],
    worst_openings: list[OpponentOpeningMetric],
    risk_areas: list[RiskArea],
) -> list[PreparationRecommendation]:
    recommendations: list[PreparationRecommendation] = []

    for risk in risk_areas:
        if risk.category == "weak_opening":
            recommendations.append(
                PreparationRecommendation(
                    id=f"prep_target_{_slug(risk.id)}",
                    action=f"Steer toward {risk.metrics.get('label', 'this weak opening')} when practical.",
                    rationale="The opponent's results in this line are materially weak.",
                    evidence=risk.evidence,
                    source_rule="weak_opening_score_rate_lte_40",
                    sample_size=risk.sample_size,
                    confidence_pct=risk.confidence_pct,
                    severity=risk.severity,
                    metrics=risk.metrics,
                )
            )
        elif risk.id == "poor_black_performance":
            recommendations.append(
                PreparationRecommendation(
                    id="prep_test_black_repertoire",
                    action="With White, keep pressure in the opening and make their Black repertoire solve problems early.",
                    rationale="Their Black results are below their overall baseline.",
                    evidence=risk.evidence,
                    source_rule="poor_black_performance",
                    sample_size=risk.sample_size,
                    confidence_pct=risk.confidence_pct,
                    severity=risk.severity,
                    metrics=risk.metrics,
                )
            )
        elif risk.id == "poor_white_performance":
            recommendations.append(
                PreparationRecommendation(
                    id="prep_solid_black_setup",
                    action="With Black, choose a solid setup and make them prove an advantage.",
                    rationale="Their White results are below their overall baseline.",
                    evidence=risk.evidence,
                    source_rule="poor_white_performance",
                    sample_size=risk.sample_size,
                    confidence_pct=risk.confidence_pct,
                    severity=risk.severity,
                    metrics=risk.metrics,
                )
            )
        elif risk.id == "poor_endgame_results":
            recommendations.append(
                PreparationRecommendation(
                    id="prep_simplify_into_endgames",
                    action="Simplify into endgames when the position is equal or slightly favorable.",
                    rationale="Their results drop in games that reach the endgame threshold.",
                    evidence=risk.evidence,
                    source_rule="poor_endgame_results",
                    sample_size=risk.sample_size,
                    confidence_pct=risk.confidence_pct,
                    severity=risk.severity,
                    metrics=risk.metrics,
                )
            )
        elif risk.id == "short_loss_pattern":
            recommendations.append(
                PreparationRecommendation(
                    id="prep_force_early_decisions",
                    action="Create early concrete decisions; avoid drifting into slow equal positions too quickly.",
                    rationale="Their losses often happen before move 25.",
                    evidence=risk.evidence,
                    source_rule="short_loss_pattern",
                    sample_size=risk.sample_size,
                    confidence_pct=risk.confidence_pct,
                    severity=risk.severity,
                    metrics=risk.metrics,
                )
            )

    for opening in best_openings[:2]:
        if opening.games_played >= 3 and opening.score_rate_pct >= 65:
            recommendations.append(
                PreparationRecommendation(
                    id=f"prep_avoid_{_slug(opening.label)}",
                    action=f"Avoid entering {opening.label} without specific preparation.",
                    rationale="This is one of the opponent's best-performing repertoire choices.",
                    evidence=[
                        f"{opening.games_played} games.",
                        f"{opening.score_rate_pct}% score rate.",
                        f"{opening.confidence_pct}% confidence.",
                    ],
                    source_rule="best_opening_score_rate_gte_65",
                    sample_size=opening.games_played,
                    confidence_pct=opening.confidence_pct,
                    severity=opening.rank_score,
                    metrics=opening.model_dump(mode="json"),
                )
            )

    if not recommendations and worst_openings:
        opening = worst_openings[0]
        recommendations.append(
            PreparationRecommendation(
                id="prep_build_targeted_opening_plan",
                action=f"Prepare a targeted line against {opening.label}.",
                rationale="This is the lowest-ranked repertoire area available in the uploaded sample.",
                evidence=[
                    f"{opening.games_played} games.",
                    f"{opening.score_rate_pct}% score rate.",
                ],
                source_rule="fallback_lowest_ranked_opening",
                sample_size=opening.games_played,
                confidence_pct=opening.confidence_pct,
                severity=_weakness_rank_score(opening),
                metrics=opening.model_dump(mode="json"),
            )
        )

    deduped: dict[str, PreparationRecommendation] = {}
    for recommendation in recommendations:
        deduped.setdefault(recommendation.id, recommendation)

    return sorted(deduped.values(), key=lambda recommendation: recommendation.severity, reverse=True)[:6]


def _weakness_rank_score(metric: OpponentOpeningMetric) -> float:
    sample_weight = _sample_weight(metric.games_played, OPENING_TARGET_SAMPLE)
    confidence = metric.confidence_pct / 100
    return round((100 - metric.score_rate_pct) * sample_weight * confidence, 2)


def _score_breakdown(games: list[Any]) -> dict[str, Any]:
    wins = sum(1 for game in games if _value(game, "analyzed_player_result") == "win")
    draws = sum(1 for game in games if _value(game, "analyzed_player_result") == "draw")
    losses = sum(1 for game in games if _value(game, "analyzed_player_result") == "loss")
    known_results = wins + draws + losses
    score = wins + 0.5 * draws

    return {
        "games_played": len(games),
        "known_results": known_results,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "score_rate_pct": _percentage(score, known_results),
    }


def _opponent_rating(game: Any) -> int | None:
    color = _value(game, "analyzed_player_color")
    if color == "white":
        return _value(game, "white_elo")
    if color == "black":
        return _value(game, "black_elo")
    return None


def _common_value(games: list[Any], attr: str) -> str | None:
    counts: dict[str, int] = defaultdict(int)
    for game in games:
        value = _value(game, attr)
        if value:
            counts[value] += 1

    if not counts:
        return None

    return max(counts.items(), key=lambda item: item[1])[0]


def _normalized_move(move: str | None) -> str | None:
    if not move:
        return None
    return move.strip().replace("+", "").replace("#", "").casefold()


def _confidence_fraction(sample_size: int, target_sample_size: int) -> float:
    if sample_size <= 0 or target_sample_size <= 0:
        return 0.0
    return min(0.95, math.sqrt(sample_size / target_sample_size))


def _confidence_pct(sample_size: int, target_sample_size: int) -> int:
    return round(_confidence_fraction(sample_size, target_sample_size) * 100)


def _sample_weight(sample_size: int, target_sample_size: int) -> float:
    if sample_size <= 0 or target_sample_size <= 0:
        return 0.0
    return min(1.0, math.sqrt(sample_size / target_sample_size))


def _severity(delta: float, sample_size: int, target_sample_size: int) -> float:
    return round(abs(delta) * _sample_weight(sample_size, target_sample_size) * _confidence_fraction(sample_size, target_sample_size), 2)


def _percentage(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _average(values: Iterable[int | float]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(values_list) / len(values_list)


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in value)
    return "_".join(part for part in slug.split("_") if part)


def _value(obj: Any, attr: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

