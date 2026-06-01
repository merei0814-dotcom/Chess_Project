from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass

import chess
import chess.pgn


@dataclass(frozen=True)
class ParsedGame:
    pgn_hash: str
    source_game_id: str | None
    event: str | None
    site: str | None
    played_at: str | None
    round: str | None
    white: str | None
    black: str | None
    result: str | None
    white_elo: int | None
    black_elo: int | None
    time_control: str | None
    eco: str | None
    opening: str | None
    ply_count: int
    fullmove_count: int
    white_move_count: int
    black_move_count: int
    white_capture_count: int
    black_capture_count: int
    white_check_count: int
    black_check_count: int
    first_white_move: str | None
    black_response: str | None
    final_fen: str | None
    reached_endgame: bool
    capture_count: int
    check_count: int
    headers: dict[str, str]
    pgn_text: str


@dataclass(frozen=True)
class PgnParseResult:
    games: list[ParsedGame]
    skipped_games: int = 0


def parse_pgn_bytes(content: bytes) -> PgnParseResult:
    text = _decode_pgn(content)
    return parse_pgn_text(text)


def parse_pgn_text(text: str) -> PgnParseResult:
    pgn_io = io.StringIO(text)
    games: list[ParsedGame] = []
    skipped_games = 0

    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break

        try:
            games.append(_parse_game(game))
        except Exception:
            skipped_games += 1

    return PgnParseResult(games=games, skipped_games=skipped_games)


def _parse_game(game: chess.pgn.Game) -> ParsedGame:
    headers = {key: value for key, value in game.headers.items()}
    moves = list(game.mainline_moves())
    board = game.board()
    capture_count = 0
    check_count = 0
    white_move_count = 0
    black_move_count = 0
    white_capture_count = 0
    black_capture_count = 0
    white_check_count = 0
    black_check_count = 0
    first_white_move: str | None = None
    black_response: str | None = None
    reached_endgame = False

    for ply_index, move in enumerate(moves, start=1):
        moving_color = board.turn
        san = board.san(move)

        if ply_index == 1:
            first_white_move = san
        elif ply_index == 2:
            black_response = san

        if moving_color == chess.WHITE:
            white_move_count += 1
        else:
            black_move_count += 1

        if board.is_capture(move):
            capture_count += 1
            if moving_color == chess.WHITE:
                white_capture_count += 1
            else:
                black_capture_count += 1
        if board.gives_check(move):
            check_count += 1
            if moving_color == chess.WHITE:
                white_check_count += 1
            else:
                black_check_count += 1

        board.push(move)

        if ply_index >= 30 and _non_king_piece_count(board) <= 12:
            reached_endgame = True

    pgn_text = _export_clean_pgn(game)

    return ParsedGame(
        pgn_hash=hashlib.sha256(pgn_text.encode("utf-8")).hexdigest(),
        source_game_id=headers.get("Site"),
        event=_clean_header(headers.get("Event")),
        site=_clean_header(headers.get("Site")),
        played_at=_clean_header(headers.get("Date")),
        round=_clean_header(headers.get("Round")),
        white=_clean_header(headers.get("White")),
        black=_clean_header(headers.get("Black")),
        result=_clean_header(headers.get("Result")),
        white_elo=_parse_int(headers.get("WhiteElo")),
        black_elo=_parse_int(headers.get("BlackElo")),
        time_control=_clean_header(headers.get("TimeControl")),
        eco=_clean_header(headers.get("ECO")),
        opening=_clean_header(headers.get("Opening")),
        ply_count=len(moves),
        fullmove_count=math.ceil(len(moves) / 2),
        white_move_count=white_move_count,
        black_move_count=black_move_count,
        white_capture_count=white_capture_count,
        black_capture_count=black_capture_count,
        white_check_count=white_check_count,
        black_check_count=black_check_count,
        first_white_move=first_white_move,
        black_response=black_response,
        final_fen=board.fen() if moves else None,
        reached_endgame=reached_endgame,
        capture_count=capture_count,
        check_count=check_count,
        headers=headers,
        pgn_text=pgn_text,
    )


def _decode_pgn(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _export_clean_pgn(game: chess.pgn.Game) -> str:
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter).strip()


def _clean_header(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped or stripped in {"?", "??", "????.??.??"}:
        return None

    return stripped


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def _non_king_piece_count(board: chess.Board) -> int:
    piece_types = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
    colors = (chess.WHITE, chess.BLACK)
    return sum(len(board.pieces(piece_type, color)) for piece_type in piece_types for color in colors)
