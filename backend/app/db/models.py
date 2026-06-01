import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GameImport(Base):
    __tablename__ = "game_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    requested_player_name: Mapped[Optional[str]] = mapped_column(String(255))
    analyzed_player_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now, nullable=False)

    games: Mapped[list["Game"]] = relationship(
        back_populates="game_import",
        cascade="all, delete-orphan",
    )
    report: Mapped[Optional["ChessDNAReport"]] = relationship(
        back_populates="game_import",
        cascade="all, delete-orphan",
    )
    opponent_report: Mapped[Optional["OpponentIntelligenceReport"]] = relationship(
        back_populates="game_import",
        cascade="all, delete-orphan",
    )


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("import_id", "pgn_hash", name="uq_games_import_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    import_id: Mapped[str] = mapped_column(ForeignKey("game_imports.id", ondelete="CASCADE"), nullable=False)
    pgn_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_game_id: Mapped[Optional[str]] = mapped_column(String(500))
    event: Mapped[Optional[str]] = mapped_column(String(500))
    site: Mapped[Optional[str]] = mapped_column(String(500))
    played_at: Mapped[Optional[str]] = mapped_column(String(50))
    round: Mapped[Optional[str]] = mapped_column(String(100))
    white: Mapped[Optional[str]] = mapped_column(String(255))
    black: Mapped[Optional[str]] = mapped_column(String(255))
    result: Mapped[Optional[str]] = mapped_column(String(20))
    white_elo: Mapped[Optional[int]] = mapped_column(Integer)
    black_elo: Mapped[Optional[int]] = mapped_column(Integer)
    time_control: Mapped[Optional[str]] = mapped_column(String(100))
    eco: Mapped[Optional[str]] = mapped_column(String(20))
    opening: Mapped[Optional[str]] = mapped_column(String(500))
    ply_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fullmove_count: Mapped[int] = mapped_column(Integer, nullable=False)
    white_move_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    black_move_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    white_capture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    black_capture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    white_check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    black_check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_white_move: Mapped[Optional[str]] = mapped_column(String(50))
    black_response: Mapped[Optional[str]] = mapped_column(String(50))
    final_fen: Mapped[Optional[str]] = mapped_column(Text)
    analyzed_player_color: Mapped[Optional[str]] = mapped_column(String(10))
    analyzed_player_result: Mapped[Optional[str]] = mapped_column(String(20))
    reached_endgame: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    capture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headers_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    pgn_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    game_import: Mapped[GameImport] = relationship(back_populates="games")


class ChessDNAReport(Base):
    __tablename__ = "chess_dna_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("game_imports.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    analyzed_player_name: Mapped[Optional[str]] = mapped_column(String(255))
    total_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    game_import: Mapped[GameImport] = relationship(back_populates="report")


class OpponentIntelligenceReport(Base):
    __tablename__ = "opponent_intelligence_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("game_imports.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    opponent_name: Mapped[Optional[str]] = mapped_column(String(255))
    total_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    game_import: Mapped[GameImport] = relationship(back_populates="opponent_report")
