from app.services.opponent_intelligence import generate_opponent_intelligence_report


def test_opponent_intelligence_detects_repertoire_risks_and_recommendations():
    games = []
    games.extend(
        _game(
            color="black",
            result="loss",
            opening="Sicilian Defense",
            eco="B20",
            first_white_move="e4",
            black_response="c5",
            fullmove_count=20,
            rating=1720,
        )
        for _ in range(8)
    )
    games.extend(
        _game(
            color="black",
            result="draw",
            opening="Slav Defense",
            eco="D10",
            first_white_move="d4",
            black_response="d5",
            fullmove_count=42,
            rating=1740,
        )
        for _ in range(4)
    )
    games.extend(
        _game(
            color="white",
            result="win",
            opening="Italian Game",
            eco="C50",
            first_white_move="e4",
            black_response="e5",
            fullmove_count=36,
            rating=1760,
        )
        for _ in range(6)
    )

    report = generate_opponent_intelligence_report(games, "Opponent")

    assert report["version"] == "opponent_intelligence_v1"
    assert report["summary"]["total_games"] == 18
    assert report["summary"]["rating_range"] == "1720-1760"
    assert report["summary"]["preferred_color"] == "black"
    assert report["opening_repertoire"]["as_black"]["responses_against_e4"][0]["black_response"] == "c5"
    assert report["best_performing_openings"][0]["opening"] == "Italian Game"
    assert report["worst_performing_openings"][0]["opening"] == "Sicilian Defense"
    assert any(risk["id"].startswith("weak_opening") for risk in report["risk_areas"])
    assert any(risk["id"] == "poor_black_performance" for risk in report["risk_areas"])
    assert any(item["source_rule"] == "weak_opening_score_rate_lte_40" for item in report["preparation_recommendations"])
    assert all("confidence_pct" in item for item in report["preparation_recommendations"])


def _game(
    color: str,
    result: str,
    opening: str,
    eco: str,
    first_white_move: str,
    black_response: str,
    fullmove_count: int,
    rating: int,
) -> dict:
    return {
        "white": "Opponent" if color == "white" else "Player",
        "black": "Opponent" if color == "black" else "Player",
        "white_elo": rating if color == "white" else 1600,
        "black_elo": rating if color == "black" else 1600,
        "opening": opening,
        "eco": eco,
        "first_white_move": first_white_move,
        "black_response": black_response,
        "fullmove_count": fullmove_count,
        "ply_count": fullmove_count * 2,
        "reached_endgame": fullmove_count >= 42,
        "analyzed_player_color": color,
        "analyzed_player_result": result,
    }

