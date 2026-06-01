CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS game_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    filename TEXT,
    requested_player_name TEXT,
    analyzed_player_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    total_games INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id UUID NOT NULL REFERENCES game_imports(id) ON DELETE CASCADE,
    pgn_hash TEXT NOT NULL,
    source_game_id TEXT,
    event TEXT,
    site TEXT,
    played_at TEXT,
    round TEXT,
    white TEXT,
    black TEXT,
    result TEXT,
    white_elo INTEGER,
    black_elo INTEGER,
    time_control TEXT,
    eco TEXT,
    opening TEXT,
    ply_count INTEGER NOT NULL,
    fullmove_count INTEGER NOT NULL,
    white_move_count INTEGER NOT NULL DEFAULT 0,
    black_move_count INTEGER NOT NULL DEFAULT 0,
    white_capture_count INTEGER NOT NULL DEFAULT 0,
    black_capture_count INTEGER NOT NULL DEFAULT 0,
    white_check_count INTEGER NOT NULL DEFAULT 0,
    black_check_count INTEGER NOT NULL DEFAULT 0,
    first_white_move TEXT,
    black_response TEXT,
    final_fen TEXT,
    analyzed_player_color TEXT,
    analyzed_player_result TEXT,
    reached_endgame BOOLEAN NOT NULL DEFAULT false,
    capture_count INTEGER NOT NULL DEFAULT 0,
    check_count INTEGER NOT NULL DEFAULT 0,
    headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    pgn_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_games_import_hash UNIQUE (import_id, pgn_hash)
);

CREATE TABLE IF NOT EXISTS chess_dna_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id UUID NOT NULL UNIQUE REFERENCES game_imports(id) ON DELETE CASCADE,
    analyzed_player_name TEXT,
    total_games INTEGER NOT NULL DEFAULT 0,
    report_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS opponent_intelligence_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id UUID NOT NULL UNIQUE REFERENCES game_imports(id) ON DELETE CASCADE,
    opponent_name TEXT,
    total_games INTEGER NOT NULL DEFAULT 0,
    report_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_games_import_id ON games(import_id);
CREATE INDEX IF NOT EXISTS ix_games_opening ON games(opening);
CREATE INDEX IF NOT EXISTS ix_games_eco ON games(eco);
CREATE INDEX IF NOT EXISTS ix_reports_import_id ON chess_dna_reports(import_id);
CREATE INDEX IF NOT EXISTS ix_opponent_reports_import_id ON opponent_intelligence_reports(import_id);
