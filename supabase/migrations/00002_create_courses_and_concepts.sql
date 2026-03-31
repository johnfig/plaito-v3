-- Courses table
CREATE TABLE courses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    course_code     TEXT,
    term            TEXT,
    current_grade   NUMERIC(5,2),
    target_grade    NUMERIC(5,2) DEFAULT 90.0,
    grading_scale   JSONB DEFAULT '{"A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77, "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0}'::jsonb,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_courses_user ON courses(user_id);

-- Concepts table (hierarchical via parent_concept_id)
CREATE TABLE concepts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    description         TEXT,
    weight              NUMERIC(4,3) NOT NULL DEFAULT 1.0,
    parent_concept_id   UUID REFERENCES concepts(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_concepts_course ON concepts(course_id);
CREATE INDEX idx_concepts_parent ON concepts(parent_concept_id);
