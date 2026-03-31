-- Mastery scores: one row per user-concept pair
CREATE TABLE mastery_scores (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id          UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    score               NUMERIC(4,3) NOT NULL DEFAULT 0.0,  -- 0.0 to 1.0
    confidence          NUMERIC(4,3) NOT NULL DEFAULT 0.0,  -- 0.0 to 1.0
    attempt_count       INTEGER NOT NULL DEFAULT 0,
    last_practiced_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, concept_id)
);

CREATE INDEX idx_mastery_user_concept ON mastery_scores(user_id, concept_id);

-- Append-only history of mastery changes
CREATE TABLE mastery_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mastery_score_id    UUID NOT NULL REFERENCES mastery_scores(id) ON DELETE CASCADE,
    score               NUMERIC(4,3) NOT NULL,
    confidence          NUMERIC(4,3) NOT NULL,
    source              TEXT NOT NULL,  -- 'session', 'quiz', 'manual'
    session_id          UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mastery_history_score ON mastery_history(mastery_score_id);
CREATE INDEX idx_mastery_history_time ON mastery_history(created_at);
