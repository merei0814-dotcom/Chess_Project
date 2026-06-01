from app.services.chess_dna import generate_chess_dna_report, infer_analyzed_player
from app.services.pgn_parser import parse_pgn_text


SAMPLE_PGN = """
[Event "Casual Game"]
[Site "https://example.com/game/1"]
[Date "2024.01.01"]
[Round "-"]
[White "TestPlayer"]
[Black "OpponentA"]
[Result "1-0"]
[WhiteElo "1500"]
[BlackElo "1450"]
[ECO "C20"]
[Opening "King's Pawn Game"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0

[Event "Casual Game"]
[Site "https://example.com/game/2"]
[Date "2024.01.02"]
[Round "-"]
[White "OpponentB"]
[Black "TestPlayer"]
[Result "0-1"]
[WhiteElo "1480"]
[BlackElo "1500"]
[ECO "B20"]
[Opening "Sicilian Defense"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be2 e5 7. Nb3 Be7 8. O-O O-O 9. Be3 Be6 10. f4 exf4 11. Bxf4 Nc6 12. Kh1 Rc8 13. Qd2 Ne5 14. Rad1 Qc7 15. Nd4 b5 16. a3 Rfd8 17. Qe3 Qb7 18. Qg3 Nxe4 19. Nxe4 Qxe4 20. c3 Qg6 21. Qe3 Bf6 22. Nxe6 fxe6 23. Qb6 Qc2 24. Rd2 Qb3 25. Qxa6 Nc4 26. Bxc4 Qxc4 27. Re1 Qxf4 28. Rde2 Be5 29. g3 Qf3+ 30. Kg1 Rf8 31. Qxb5 Bxg3 32. hxg3 Qxg3+ 33. Kh1 Rc5 34. Qxc5 dxc5 35. Rg2 Qxe1+ 36. Kh2 Rf1 37. Kh3 Rh1+ 38. Kg4 Qe4+ 39. Kg3 Rf1 40. Kh2 Qh4# 0-1
"""


def test_parse_pgn_and_generate_chess_dna():
    parsed = parse_pgn_text(SAMPLE_PGN)
    player = infer_analyzed_player(parsed.games, "TestPlayer")

    game_dicts = []
    for game in parsed.games:
        color = "white" if game.white == player else "black"
        result = "win"
        game_dicts.append({**game.__dict__, "analyzed_player_color": color, "analyzed_player_result": result})

    report = generate_chess_dna_report(game_dicts, player)

    expected_player_moves = sum(
        game.white_move_count if game.white == player else game.black_move_count
        for game in parsed.games
    )

    assert report["version"] == "chess_dna_v2"
    assert report["summary"]["total_games"] == 2
    assert report["analyzed_player"] == "TestPlayer"
    assert report["colors"]["white"]["wins"] == 1
    assert report["colors"]["black"]["wins"] == 1
    assert report["style"]["player_move_count"] == expected_player_moves
    assert "all_openings" in report["openings"]
    assert "best_openings" in report["openings"]
    assert "worst_openings" in report["openings"]
    assert "middlegame" in report["phases"]
    assert isinstance(report["strengths"], list)
    assert isinstance(report["weaknesses"], list)


def test_opening_weaknesses_are_ranked_by_sample_adjusted_severity():
    games = [
        _game(opening="Bad Large", eco="A00", result="loss")
        for _ in range(12)
    ]
    games += [
        _game(opening="Bad Small", eco="A01", result="loss")
        for _ in range(2)
    ]
    games += [
        _game(opening="Good Large", eco="B00", result="win")
        for _ in range(12)
    ]

    report = generate_chess_dna_report(games, "TestPlayer")
    worst_openings = report["openings"]["worst_openings"]

    assert worst_openings[0]["opening"] == "Bad Large"
    assert worst_openings[0]["severity"] > worst_openings[1]["severity"]
    assert "confidence_pct" in worst_openings[0]
    assert "score_delta_pct" in worst_openings[0]


def _game(opening: str, eco: str, result: str) -> dict:
    return {
        "white": "TestPlayer",
        "black": "Opponent",
        "opening": opening,
        "eco": eco,
        "fullmove_count": 34,
        "ply_count": 68,
        "reached_endgame": False,
        "analyzed_player_color": "white",
        "analyzed_player_result": result,
        "white_move_count": 34,
        "black_move_count": 34,
        "white_capture_count": 8,
        "black_capture_count": 8,
        "white_check_count": 1,
        "black_check_count": 1,
    }
