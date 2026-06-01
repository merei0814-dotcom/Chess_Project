from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

from app.schemas.chess_dna import (
    ChessDNAReportV2,
    ColorMetric,
    ColorSection,
    ImprovementPriority,
    Insight,
    MistakePattern,
    OpeningMetric,
    OpeningSection,
    PhaseMetric,
    PhaseSection,
    ReportSummary,
    StyleProfile,
)


REPORT_TARGET_SAMPLE = 50
COLOR_TARGET_SAMPLE = 20
OPENING_TARGET_SAMPLE = 12
PHASE_TARGET_SAMPLE = 20
STYLE_TARGET_SAMPLE = 30


def normalize_player_name(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.strip().split()).casefold()


def infer_analyzed_player(games: Iterable[Any], requested_player_name: str | None = None) -> str:
    if requested_player_name and requested_player_name.strip():
        return requested_player_name.strip()

    names: Counter[str] = Counter()
    display_names: dict[str, str] = {}

    for game in games:
        for attr in ("white", "black"):
            name = _value(game, attr)
            normalized = normalize_player_name(name)
            if not normalized:
                continue

            names[normalized] += 1
            display_names.setdefault(normalized, name)

    if not names:
        return "Unknown player"

    return display_names[names.most_common(1)[0][0]]


def player_appears_in_games(games: Iterable[Any], player_name: str) -> bool:
    normalized = normalize_player_name(player_name)
    return any(
        normalize_player_name(_value(game, "white")) == normalized
        or normalize_player_name(_value(game, "black")) == normalized
        for game in games
    )


def player_color_for_game(game: Any, player_name: str) -> str | None:
    normalized = normalize_player_name(player_name)

    if normalize_player_name(_value(game, "white")) == normalized:
        return "white"
    if normalize_player_name(_value(game, "black")) == normalized:
        return "black"

    return None


def result_for_color(result: str | None, color: str | None) -> str | None:
    if color is None or result not in {"1-0", "0-1", "1/2-1/2"}:
        return None

    if result == "1/2-1/2":
        return "draw"
    if result == "1-0":
        return "win" if color == "white" else "loss"
    return "win" if color == "black" else "loss"


def generate_chess_dna_report(games: list[Any], analyzed_player_name: str) -> dict[str, Any]:
    analyzed_games = [game for game in games if _value(game, "analyzed_player_color") in {"white", "black"}]
    overall = _score_breakdown(analyzed_games)
    overall_score_rate = overall["score_rate_pct"]
    endgame_frequency = _endgame_frequency(analyzed_games)

    style = _style_profile(analyzed_games, overall_score_rate, endgame_frequency["percentage"])
    openings = _opening_section(analyzed_games, overall_score_rate)
    colors = _color_section(analyzed_games, overall_score_rate)
    phases = _phase_section(analyzed_games, overall_score_rate)
    mistakes = _mistake_patterns(
        analyzed_games=analyzed_games,
        style=style,
        openings=openings,
        colors=colors,
        phases=phases,
        overall_score_rate=overall_score_rate,
        endgame_frequency_pct=endgame_frequency["percentage"],
    )
    strengths = _ranked_strengths(
        openings=openings,
        colors=colors,
        phases=phases,
        style=style,
        overall_score_rate=overall_score_rate,
    )
    weaknesses = _ranked_weaknesses(openings=openings, colors=colors, phases=phases, mistakes=mistakes)
    priorities = _improvement_priorities(weaknesses, mistakes)

    report = ChessDNAReportV2(
        generated_at=datetime.now(timezone.utc).isoformat(),
        analyzed_player=analyzed_player_name,
        summary=ReportSummary(
            total_games=len(games),
            analyzed_games=len(analyzed_games),
            overall_score_rate_pct=overall_score_rate,
            average_game_length=round(_average(_value(game, "fullmove_count", 0) for game in analyzed_games), 1),
            average_loss_length=round(_average_loss_length(analyzed_games), 1),
            endgame_frequency_pct=endgame_frequency["percentage"],
            confidence_pct=_confidence_pct(overall["known_results"], REPORT_TARGET_SAMPLE),
        ),
        style=style,
        openings=openings,
        colors=colors,
        phases=phases,
        strengths=strengths,
        weaknesses=weaknesses,
        most_common_mistakes=mistakes,
        improvement_priorities=priorities,
    )

    return report.model_dump(mode="json")


def _style_profile(games: list[Any], overall_score_rate: float, endgame_frequency_pct: float) -> StyleProfile:
    player_move_count = sum(_player_move_count(game) for game in games)
    player_capture_count = sum(_player_capture_count(game) for game in games)
    player_check_count = sum(_player_check_count(game) for game in games)
    capture_rate = player_capture_count / player_move_count if player_move_count else 0
    check_rate = player_check_count / player_move_count if player_move_count else 0
    forcing_rate = (player_capture_count + player_check_count) / player_move_count if player_move_count else 0
    average_length = _average(_value(game, "fullmove_count", 0) for game in games)
    confidence = _confidence_pct(len(games), STYLE_TARGET_SAMPLE)
    evidence: list[str] = [
        f"{player_capture_count} captures and {player_check_count} checks across {player_move_count} target-player moves.",
        f"Average game length is {round(average_length, 1)} moves; endgame frequency is {endgame_frequency_pct}%.",
    ]

    if forcing_rate >= 0.32 or capture_rate >= 0.28 or check_rate >= 0.10:
        label = "Tactical"
        evidence.append("Forcing move rate is above the tactical threshold.")
    elif average_length >= 42 and endgame_frequency_pct >= 35 and forcing_rate < 0.28:
        label = "Positional"
        evidence.append("Long games and frequent endgames indicate slower strategic play.")
    else:
        label = "Balanced"
        evidence.append("No tactical or positional threshold dominates this sample.")

    if overall_score_rate < 45 and label == "Tactical":
        evidence.append("The style is tactical, but results are below the baseline target; this may be volatility, not strength.")

    return StyleProfile(
        label=label,
        player_move_count=player_move_count,
        player_capture_count=player_capture_count,
        player_check_count=player_check_count,
        capture_rate_per_move=round(capture_rate, 3),
        check_rate_per_move=round(check_rate, 3),
        forcing_move_rate=round(forcing_rate, 3),
        confidence_pct=confidence,
        sample_size=len(games),
        evidence=evidence,
    )


def _opening_section(games: list[Any], overall_score_rate: float) -> OpeningSection:
    grouped: dict[tuple[str | None, str], list[Any]] = defaultdict(list)

    for game in games:
        opening = _value(game, "opening") or "Unknown opening"
        eco = _value(game, "eco")
        grouped[(eco, opening)].append(game)

    all_openings: list[OpeningMetric] = []
    for (eco, opening), opening_games in grouped.items():
        label = f"{eco} {opening}" if eco else opening
        base = _performance_metric_base(
            label=label,
            games=opening_games,
            overall_score_rate=overall_score_rate,
            target_sample_size=OPENING_TARGET_SAMPLE,
        )
        all_openings.append(OpeningMetric(opening=opening, eco=eco, **base))

    all_openings = sorted(
        all_openings,
        key=lambda metric: (metric.games_played, metric.severity, metric.score_rate_pct),
        reverse=True,
    )
    best_openings = sorted(
        [metric for metric in all_openings if metric.score_delta_pct > 0],
        key=lambda metric: metric.severity,
        reverse=True,
    )[:5]
    worst_openings = sorted(
        [metric for metric in all_openings if metric.score_delta_pct < 0],
        key=lambda metric: metric.severity,
        reverse=True,
    )[:5]

    return OpeningSection(
        all_openings=all_openings,
        best_openings=best_openings,
        worst_openings=worst_openings,
    )


def _color_section(games: list[Any], overall_score_rate: float) -> ColorSection:
    white = ColorMetric(
        color="white",
        **_performance_metric_base(
            label="White",
            games=[game for game in games if _value(game, "analyzed_player_color") == "white"],
            overall_score_rate=overall_score_rate,
            target_sample_size=COLOR_TARGET_SAMPLE,
        ),
    )
    black = ColorMetric(
        color="black",
        **_performance_metric_base(
            label="Black",
            games=[game for game in games if _value(game, "analyzed_player_color") == "black"],
            overall_score_rate=overall_score_rate,
            target_sample_size=COLOR_TARGET_SAMPLE,
        ),
    )
    eligible = [metric for metric in (white, black) if metric.games_played > 0]

    return ColorSection(
        white=white,
        black=black,
        best_color=max(eligible, key=lambda metric: metric.score_delta_pct) if eligible else None,
        worst_color=min(eligible, key=lambda metric: metric.score_delta_pct) if eligible else None,
    )


def _phase_section(games: list[Any], overall_score_rate: float) -> PhaseSection:
    opening_games = [game for game in games if _value(game, "fullmove_count", 0) <= 25]
    middlegame_games = [
        game
        for game in games
        if _value(game, "fullmove_count", 0) > 25 and not _value(game, "reached_endgame", False)
    ]
    endgame_games = [game for game in games if _value(game, "reached_endgame", False)]

    opening = PhaseMetric(
        phase="opening",
        heuristic="Games ending by move 25 are treated as opening or early-tactical outcomes.",
        **_performance_metric_base(
            label="Opening phase",
            games=opening_games,
            overall_score_rate=overall_score_rate,
            target_sample_size=PHASE_TARGET_SAMPLE,
        ),
    )
    middlegame = PhaseMetric(
        phase="middlegame",
        heuristic="Games lasting beyond move 25 without reaching the material endgame threshold are treated as middlegames.",
        **_performance_metric_base(
            label="Middlegame phase",
            games=middlegame_games,
            overall_score_rate=overall_score_rate,
            target_sample_size=PHASE_TARGET_SAMPLE,
        ),
    )
    endgame = PhaseMetric(
        phase="endgame",
        heuristic="A game reaches the endgame when move 30 has passed and 12 or fewer non-king pieces remain.",
        **_performance_metric_base(
            label="Endgame phase",
            games=endgame_games,
            overall_score_rate=overall_score_rate,
            target_sample_size=PHASE_TARGET_SAMPLE,
        ),
    )

    return PhaseSection(opening=opening, middlegame=middlegame, endgame=endgame)


def _ranked_strengths(
    openings: OpeningSection,
    colors: ColorSection,
    phases: PhaseSection,
    style: StyleProfile,
    overall_score_rate: float,
) -> list[Insight]:
    insights: list[Insight] = []

    for metric in _color_metrics(colors):
        if metric.score_delta_pct >= 5 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"strength_color_{metric.color}",
                    title=f"{metric.label} is outperforming your baseline",
                    description=f"You score {metric.score_delta_pct} percentage points above your overall rate as {metric.label}.",
                    category="color",
                    metric=metric,
                )
            )

    for metric in openings.best_openings:
        if metric.score_delta_pct >= 8 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"strength_opening_{_slug(metric.label)}",
                    title=f"{metric.label} is a strong opening",
                    description=f"This opening scores {metric.score_delta_pct} percentage points above your overall performance.",
                    category="opening",
                    metric=metric,
                )
            )

    for metric in _phase_metrics(phases):
        if metric.score_delta_pct >= 8 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"strength_phase_{metric.phase}",
                    title=f"{metric.label} is a relative strength",
                    description=f"This phase scores {metric.score_delta_pct} percentage points above your overall performance.",
                    category="phase",
                    metric=metric,
                )
            )

    if style.label == "Tactical" and overall_score_rate >= 55 and style.confidence_pct >= 50:
        severity = round((style.forcing_move_rate - 0.30) * 100 * (style.confidence_pct / 100), 2)
        insights.append(
            Insight(
                id="strength_style_tactical",
                title="Forcing play is part of your winning profile",
                description="Your target-player-only move data shows frequent captures and checks while your results remain strong.",
                category="style",
                evidence=style.evidence,
                sample_size=style.sample_size,
                confidence_pct=style.confidence_pct,
                severity=max(severity, 1.0),
                metrics={
                    "forcing_move_rate": style.forcing_move_rate,
                    "overall_score_rate_pct": overall_score_rate,
                },
            )
        )

    return sorted(insights, key=lambda insight: insight.severity, reverse=True)[:5]


def _ranked_weaknesses(
    openings: OpeningSection,
    colors: ColorSection,
    phases: PhaseSection,
    mistakes: list[MistakePattern],
) -> list[Insight]:
    insights: list[Insight] = []

    for metric in _color_metrics(colors):
        if metric.score_delta_pct <= -5 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"weakness_color_{metric.color}",
                    title=f"{metric.label} is underperforming",
                    description=f"You score {abs(metric.score_delta_pct)} percentage points below your overall rate as {metric.label}.",
                    category="color",
                    metric=metric,
                )
            )

    for metric in openings.worst_openings:
        if metric.score_delta_pct <= -8 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"weakness_opening_{_slug(metric.label)}",
                    title=f"{metric.label} is costing points",
                    description=f"This opening scores {abs(metric.score_delta_pct)} percentage points below your overall performance.",
                    category="opening",
                    metric=metric,
                )
            )

    for metric in _phase_metrics(phases):
        if metric.score_delta_pct <= -8 and metric.confidence_pct >= 40:
            insights.append(
                _insight_from_metric(
                    insight_id=f"weakness_phase_{metric.phase}",
                    title=f"{metric.label} is a relative weakness",
                    description=f"This phase scores {abs(metric.score_delta_pct)} percentage points below your overall performance.",
                    category="phase",
                    metric=metric,
                )
            )

    for mistake in mistakes:
        insights.append(
            Insight(
                id=f"weakness_{mistake.id}",
                title=mistake.title,
                description=mistake.description,
                category="mistake_pattern",
                evidence=mistake.evidence,
                sample_size=mistake.sample_size,
                confidence_pct=mistake.confidence_pct,
                severity=mistake.severity,
                metrics=mistake.metrics,
            )
        )

    return sorted(insights, key=lambda insight: insight.severity, reverse=True)[:5]


def _mistake_patterns(
    analyzed_games: list[Any],
    style: StyleProfile,
    openings: OpeningSection,
    colors: ColorSection,
    phases: PhaseSection,
    overall_score_rate: float,
    endgame_frequency_pct: float,
) -> list[MistakePattern]:
    mistakes: list[MistakePattern] = []
    total_games = len(analyzed_games)
    losses = [game for game in analyzed_games if _value(game, "analyzed_player_result") == "loss"]
    loss_rate = _percentage(len(losses), total_games)
    average_loss_length = _average_loss_length(analyzed_games)

    if style.forcing_move_rate >= 0.30 and overall_score_rate < 50:
        confidence = style.confidence_pct
        severity = round(((style.forcing_move_rate - 0.30) * 100 + (50 - overall_score_rate)) * (confidence / 100), 2)
        mistakes.append(
            MistakePattern(
                id="high_forcing_low_score",
                title="Forcing play is not converting into results",
                description="You create many captures and checks, but the overall score rate is below 50%.",
                evidence=style.evidence,
                sample_size=style.sample_size,
                confidence_pct=confidence,
                severity=max(severity, 1.0),
                metrics={
                    "forcing_move_rate": style.forcing_move_rate,
                    "overall_score_rate_pct": overall_score_rate,
                },
            )
        )

    if total_games >= 10 and endgame_frequency_pct < 20:
        confidence = _confidence_pct(total_games, STYLE_TARGET_SAMPLE)
        severity = round((20 - endgame_frequency_pct) * (confidence / 100), 2)
        mistakes.append(
            MistakePattern(
                id="low_endgame_exposure",
                title="Few games reach technical endgames",
                description="Your sample rarely reaches the endgame threshold, so conversion and defense skills are not being tested often.",
                evidence=[f"{endgame_frequency_pct}% of games reached the endgame threshold."],
                sample_size=total_games,
                confidence_pct=confidence,
                severity=severity,
                metrics={"endgame_frequency_pct": endgame_frequency_pct},
            )
        )

    if total_games >= 5 and loss_rate >= 40 and average_loss_length < 25:
        confidence = _confidence_pct(len(losses), STYLE_TARGET_SAMPLE)
        severity = round(((loss_rate - 40) + (25 - average_loss_length)) * (confidence / 100), 2)
        mistakes.append(
            MistakePattern(
                id="short_loss_pattern",
                title="Losses are ending too early",
                description="A high share of losses finish before move 25, pointing to opening safety or early tactical awareness.",
                evidence=[
                    f"Loss rate is {loss_rate}%.",
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

    for metric in openings.worst_openings[:1]:
        if metric.score_delta_pct <= -12 and metric.confidence_pct >= 40:
            mistakes.append(
                MistakePattern(
                    id=f"opening_underperformance_{_slug(metric.label)}",
                    title="Recurring opening underperformance",
                    description=f"{metric.label} is materially below your overall scoring rate.",
                    evidence=[
                        f"{metric.games_played} games in this opening.",
                        f"{metric.score_rate_pct}% score rate vs {metric.overall_score_rate_pct}% overall.",
                    ],
                    sample_size=metric.games_played,
                    confidence_pct=metric.confidence_pct,
                    severity=metric.severity,
                    metrics=metric.model_dump(mode="json"),
                )
            )

    worst_color = colors.worst_color
    if worst_color and worst_color.score_delta_pct <= -10 and worst_color.confidence_pct >= 40:
        mistakes.append(
            MistakePattern(
                id=f"color_gap_{worst_color.color}",
                title=f"{worst_color.label} performance gap",
                description=f"Your {worst_color.label} score is significantly below your overall score.",
                evidence=[
                    f"{worst_color.games_played} games as {worst_color.label}.",
                    f"{worst_color.score_rate_pct}% score rate vs {worst_color.overall_score_rate_pct}% overall.",
                ],
                sample_size=worst_color.games_played,
                confidence_pct=worst_color.confidence_pct,
                severity=worst_color.severity,
                metrics=worst_color.model_dump(mode="json"),
            )
        )

    worst_phase = min(_phase_metrics(phases), key=lambda metric: metric.score_delta_pct)
    if worst_phase.score_delta_pct <= -12 and worst_phase.confidence_pct >= 40:
        mistakes.append(
            MistakePattern(
                id=f"phase_gap_{worst_phase.phase}",
                title=f"{worst_phase.label} performance gap",
                description=f"Your {worst_phase.phase} proxy score is materially below your overall score.",
                evidence=[
                    worst_phase.heuristic,
                    f"{worst_phase.score_rate_pct}% score rate vs {worst_phase.overall_score_rate_pct}% overall.",
                ],
                sample_size=worst_phase.games_played,
                confidence_pct=worst_phase.confidence_pct,
                severity=worst_phase.severity,
                metrics=worst_phase.model_dump(mode="json"),
            )
        )

    return sorted(mistakes, key=lambda mistake: mistake.severity, reverse=True)[:5]


def _improvement_priorities(
    weaknesses: list[Insight],
    mistakes: list[MistakePattern],
) -> list[ImprovementPriority]:
    candidates = sorted(weaknesses or mistakes, key=lambda item: item.severity, reverse=True)
    priorities: list[ImprovementPriority] = []
    seen: set[str] = set()

    for item in candidates:
        category = getattr(item, "category", "mistake_pattern")
        priority_id = f"priority_{_slug(item.id)}"
        if priority_id in seen:
            continue

        seen.add(priority_id)
        priorities.append(
            ImprovementPriority(
                id=priority_id,
                title=item.title,
                reason=item.description,
                recommended_action=_recommended_action(category, item.title),
                related_weakness_ids=[item.id],
                sample_size=item.sample_size,
                confidence_pct=item.confidence_pct,
                severity=item.severity,
            )
        )

        if len(priorities) == 3:
            break

    return priorities


def _performance_metric_base(
    label: str,
    games: list[Any],
    overall_score_rate: float,
    target_sample_size: int,
) -> dict[str, Any]:
    score = _score_breakdown(games)
    sample_size = score["known_results"]
    delta = round(score["score_rate_pct"] - overall_score_rate, 1) if sample_size else 0.0

    return {
        "label": label,
        "games_played": len(games),
        "wins": score["wins"],
        "draws": score["draws"],
        "losses": score["losses"],
        "score_rate_pct": score["score_rate_pct"],
        "overall_score_rate_pct": overall_score_rate,
        "score_delta_pct": delta,
        "confidence_pct": _confidence_pct(sample_size, target_sample_size),
        "severity": _severity(delta, sample_size, target_sample_size),
    }


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


def _insight_from_metric(
    insight_id: str,
    title: str,
    description: str,
    category: str,
    metric: OpeningMetric | ColorMetric | PhaseMetric,
) -> Insight:
    return Insight(
        id=insight_id,
        title=title,
        description=description,
        category=category,
        evidence=[
            f"{metric.games_played} games.",
            f"{metric.score_rate_pct}% score rate vs {metric.overall_score_rate_pct}% overall.",
            f"Confidence: {metric.confidence_pct}%.",
        ],
        sample_size=metric.games_played,
        confidence_pct=metric.confidence_pct,
        severity=metric.severity,
        metrics=metric.model_dump(mode="json"),
    )


def _endgame_frequency(games: list[Any]) -> dict[str, Any]:
    reached = sum(1 for game in games if _value(game, "reached_endgame"))
    return {
        "games": reached,
        "percentage": _percentage(reached, len(games)),
    }


def _player_move_count(game: Any) -> int:
    color = _value(game, "analyzed_player_color")
    if color == "white":
        return _value(game, "white_move_count", 0)
    if color == "black":
        return _value(game, "black_move_count", 0)
    return 0


def _player_capture_count(game: Any) -> int:
    color = _value(game, "analyzed_player_color")
    if color == "white":
        return _value(game, "white_capture_count", 0)
    if color == "black":
        return _value(game, "black_capture_count", 0)
    return 0


def _player_check_count(game: Any) -> int:
    color = _value(game, "analyzed_player_color")
    if color == "white":
        return _value(game, "white_check_count", 0)
    if color == "black":
        return _value(game, "black_check_count", 0)
    return 0


def _color_metrics(colors: ColorSection) -> list[ColorMetric]:
    return [colors.white, colors.black]


def _phase_metrics(phases: PhaseSection) -> list[PhaseMetric]:
    return [phases.opening, phases.middlegame, phases.endgame]


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


def _recommended_action(category: str, title: str) -> str:
    lowered = title.casefold()

    if category == "opening" or "opening" in lowered:
        return "Review the first 10-12 moves in this opening and build one safer main-line plan."
    if category == "color" or "white" in lowered or "black" in lowered:
        return "Compare your results by color and prepare one reliable setup for the weaker side."
    if category == "phase" or "middlegame" in lowered or "endgame" in lowered:
        return "Study three representative games from this phase and identify where the advantage changes."
    if "forcing" in lowered or "captures" in lowered or "checks" in lowered:
        return "Before forcing moves, add a blunder-check habit: opponent threats, loose pieces, king safety."
    if "losses" in lowered:
        return "Review every loss under 25 moves and tag the first avoidable decision."
    return "Review the supporting games and convert this pattern into one focused training block."


def _percentage(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _average_loss_length(games: list[Any]) -> float:
    losses = [_value(game, "fullmove_count", 0) for game in games if _value(game, "analyzed_player_result") == "loss"]
    return _average(losses)


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
