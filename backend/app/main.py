from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ChessDNAReport, Game, GameImport, OpponentIntelligenceReport
from app.db.session import get_db, init_db
from app.services.chess_dna import (
    generate_chess_dna_report,
    infer_analyzed_player,
    player_appears_in_games,
    player_color_for_game,
    result_for_color,
)
from app.services.opponent_intelligence import (
    generate_opponent_intelligence_report,
    infer_opponent_name,
    opponent_appears_in_games,
)
from app.services.pgn_parser import ParsedGame, parse_pgn_bytes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/imports/pgn", status_code=status.HTTP_201_CREATED)
async def upload_pgn(
    file: UploadFile = File(...),
    player_name: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PGN file is empty.")
    if len(content) > settings.max_pgn_upload_bytes:
        raise HTTPException(status_code=413, detail="PGN file is too large for the MVP upload limit.")

    parse_result = parse_pgn_bytes(content)
    if not parse_result.games:
        raise HTTPException(status_code=400, detail="No valid games were found in the PGN.")

    if player_name and not player_appears_in_games(parse_result.games, player_name):
        raise HTTPException(
            status_code=422,
            detail="The requested player_name does not appear as White or Black in this PGN.",
        )

    analyzed_player = infer_analyzed_player(parse_result.games, player_name)

    game_import = GameImport(
        source_type="pgn_upload",
        filename=file.filename,
        requested_player_name=player_name,
        analyzed_player_name=analyzed_player,
        status="processing",
    )
    db.add(game_import)
    db.flush()

    games = _build_game_models(parse_result.games, game_import.id, analyzed_player)
    db.add_all(games)
    db.flush()

    report_payload = generate_chess_dna_report(games, analyzed_player)
    report = ChessDNAReport(
        import_id=game_import.id,
        analyzed_player_name=analyzed_player,
        total_games=len(games),
        report_json=report_payload,
    )
    db.add(report)

    game_import.status = "completed"
    game_import.total_games = len(games)
    db.commit()

    return {
        "import_id": game_import.id,
        "filename": file.filename,
        "analyzed_player": analyzed_player,
        "total_games": len(games),
        "skipped_games": parse_result.skipped_games,
        "report": report_payload,
    }


@app.post("/api/opponents/pgn", status_code=status.HTTP_201_CREATED)
async def upload_opponent_pgn(
    file: UploadFile = File(...),
    opponent_name: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PGN file is empty.")
    if len(content) > settings.max_pgn_upload_bytes:
        raise HTTPException(status_code=413, detail="PGN file is too large for the MVP upload limit.")

    parse_result = parse_pgn_bytes(content)
    if not parse_result.games:
        raise HTTPException(status_code=400, detail="No valid games were found in the PGN.")

    if opponent_name and not opponent_appears_in_games(parse_result.games, opponent_name):
        raise HTTPException(
            status_code=422,
            detail="The requested opponent_name does not appear as White or Black in this PGN.",
        )

    opponent = infer_opponent_name(parse_result.games, opponent_name)

    game_import = GameImport(
        source_type="opponent_pgn_upload",
        filename=file.filename,
        requested_player_name=opponent_name,
        analyzed_player_name=opponent,
        status="processing",
    )
    db.add(game_import)
    db.flush()

    games = _build_game_models(parse_result.games, game_import.id, opponent)
    db.add_all(games)
    db.flush()

    report_payload = generate_opponent_intelligence_report(games, opponent)
    report = OpponentIntelligenceReport(
        import_id=game_import.id,
        opponent_name=opponent,
        total_games=len(games),
        report_json=report_payload,
    )
    db.add(report)

    game_import.status = "completed"
    game_import.total_games = len(games)
    db.commit()

    return {
        "import_id": game_import.id,
        "filename": file.filename,
        "opponent_name": opponent,
        "total_games": len(games),
        "skipped_games": parse_result.skipped_games,
        "report": report_payload,
    }


@app.get("/api/reports/{import_id}")
def get_report(import_id: str, db: Session = Depends(get_db)) -> dict:
    report = db.query(ChessDNAReport).filter(ChessDNAReport.import_id == import_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    return {
        "import_id": report.import_id,
        "analyzed_player": report.analyzed_player_name,
        "total_games": report.total_games,
        "report": report.report_json,
    }


@app.get("/api/opponents/reports/{import_id}")
def get_opponent_report(import_id: str, db: Session = Depends(get_db)) -> dict:
    report = (
        db.query(OpponentIntelligenceReport)
        .filter(OpponentIntelligenceReport.import_id == import_id)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Opponent report not found.")

    return {
        "import_id": report.import_id,
        "opponent_name": report.opponent_name,
        "total_games": report.total_games,
        "report": report.report_json,
    }


def _build_game_models(parsed_games: list[ParsedGame], import_id: str, analyzed_player: str) -> list[Game]:
    games: list[Game] = []
    seen_hashes: set[str] = set()

    for parsed_game in parsed_games:
        if parsed_game.pgn_hash in seen_hashes:
            continue

        seen_hashes.add(parsed_game.pgn_hash)
        color = player_color_for_game(parsed_game, analyzed_player)

        games.append(
            Game(
                import_id=import_id,
                pgn_hash=parsed_game.pgn_hash,
                source_game_id=parsed_game.source_game_id,
                event=parsed_game.event,
                site=parsed_game.site,
                played_at=parsed_game.played_at,
                round=parsed_game.round,
                white=parsed_game.white,
                black=parsed_game.black,
                result=parsed_game.result,
                white_elo=parsed_game.white_elo,
                black_elo=parsed_game.black_elo,
                time_control=parsed_game.time_control,
                eco=parsed_game.eco,
                opening=parsed_game.opening,
                ply_count=parsed_game.ply_count,
                fullmove_count=parsed_game.fullmove_count,
                white_move_count=parsed_game.white_move_count,
                black_move_count=parsed_game.black_move_count,
                white_capture_count=parsed_game.white_capture_count,
                black_capture_count=parsed_game.black_capture_count,
                white_check_count=parsed_game.white_check_count,
                black_check_count=parsed_game.black_check_count,
                first_white_move=parsed_game.first_white_move,
                black_response=parsed_game.black_response,
                final_fen=parsed_game.final_fen,
                analyzed_player_color=color,
                analyzed_player_result=result_for_color(parsed_game.result, color),
                reached_endgame=parsed_game.reached_endgame,
                capture_count=parsed_game.capture_count,
                check_count=parsed_game.check_count,
                headers_json=parsed_game.headers,
                pgn_text=parsed_game.pgn_text,
            )
        )

    return games
