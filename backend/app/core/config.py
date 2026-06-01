from __future__ import annotations

import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "CHESS AI COACH API")
    max_pgn_upload_bytes: int = int(os.getenv("MAX_PGN_UPLOAD_BYTES", "5242880"))

    @property
    def database_url(self) -> str:
        url = os.getenv("DATABASE_URL", "sqlite:///./chess_ai_coach.db")

        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)

        return url


settings = Settings()

