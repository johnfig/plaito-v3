-- Grade prediction snapshots (append-only timeline)
CREATE TABLE grade_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id           UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    predicted_grade     NUMERIC(5,2) NOT NULL,
    predicted_letter    TEXT NOT NULL,
    confidence          NUMERIC(4,3) NOT NULL,
    factors             JSONB NOT NULL DEFAULT '[]'::jsonb,
    calibration_offset  NUMERIC(5,2) DEFAULT 0.0,
    snapshot_type       TEXT NOT NULL DEFAULT 'auto',  -- auto, on_demand, post_session, calibration
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_grade_snapshots_user_course ON grade_snapshots(user_id, course_id);
CREATE INDEX idx_grade_snapshots_timeline ON grade_snapshots(user_id, course_id, created_at DESC);
