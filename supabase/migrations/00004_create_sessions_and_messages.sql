-- Tutoring sessions
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id       UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    session_type    TEXT NOT NULL DEFAULT 'homework_help',  -- homework_help, warmup, quest, practice
    status          TEXT NOT NULL DEFAULT 'active',         -- active, completed
    xp_earned       INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user_course ON sessions(user_id, course_id);
CREATE INDEX idx_sessions_status ON sessions(status);

-- Chat messages within sessions
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,  -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    image_url       TEXT,
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(session_id, created_at);
