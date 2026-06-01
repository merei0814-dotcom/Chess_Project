from fastapi.testclient import TestClient


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

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be2 e5 7. Nb3 Be7 8. O-O O-O 9. Be3 Be6 10. f4 exf4 11. Bxf4 Nc6 12. Kh1 Rc8 13. Qd2 Ne5 14. Rad1 Qc7 15. Nd4 b5 16. a3 Rfd8 17. Qe3 Qb7 18. Qg3 Nxe4 19. Nxe4 Qxe4 20. c3 Qg6 21. Qe3 Bf6 22. Nxe6 fxe6 23. Qb6 Qc2 24. Rd2 Qb3 25. Qxa6 Nc4 26. Bxc4 Qxc4 27. Re1 Qxf4 28. Rxe6 Be5 29. g3 Qf3+ 30. Kg1 Rf8 31. Rexd6 Bxd6 32. Qxd6 Qf1# 0-1
"""


def test_upload_pgn_stores_games_and_returns_report(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")

    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/api/imports/pgn",
            data={"player_name": "TestPlayer"},
            files={"file": ("sample.pgn", SAMPLE_PGN, "application/x-chess-pgn")},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["total_games"] == 2
        assert payload["report"]["version"] == "chess_dna_v2"
        assert payload["report"]["summary"]["total_games"] == 2

        report_response = client.get(f"/api/reports/{payload['import_id']}")

        opponent_response = client.post(
            "/api/opponents/pgn",
            data={"opponent_name": "TestPlayer"},
            files={"file": ("opponent.pgn", SAMPLE_PGN, "application/x-chess-pgn")},
        )

    assert report_response.status_code == 200
    assert report_response.json()["report"]["analyzed_player"] == "TestPlayer"
    assert opponent_response.status_code == 201
    assert opponent_response.json()["report"]["version"] == "opponent_intelligence_v1"
