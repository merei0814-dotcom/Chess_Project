ALTER TABLE games
    ADD COLUMN IF NOT EXISTS first_white_move TEXT;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS black_response TEXT;

CREATE TABLE IF NOT EXISTS opponent_intelligence_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_id UUID NOT NULL UNIQUE REFERENCES game_imports(id) ON DELETE CASCADE,
    opponent_name TEXT,
    total_games INTEGER NOT NULL DEFAULT 0,
    report_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_opponent_reports_import_id ON opponent_intelligence_reports(import_id);

