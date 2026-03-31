// Plaito shared types — mirrors Python Pydantic schemas

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

export interface Concept {
  id: string;
  course_id: string;
  name: string;
  description?: string;
  weight: number;
  parent_concept_id?: string;
}

export interface MasteryScore {
  id: string;
  user_id: string;
  concept_id: string;
  score: number; // 0-1 internal scale
  confidence: number; // 0-1
  attempt_count: number;
  last_practiced_at?: string;
}

export interface GradeFactor {
  concept_name: string;
  concept_id: string;
  weight: number;
  effective_mastery: number; // 0-100 display scale
  impact: number;
  days_since_practice?: number;
}

export interface GradePrediction {
  predicted_grade: number; // 0-100
  predicted_letter: string;
  confidence: number; // 0-1
  factors: GradeFactor[];
  recommended_actions: string[];
  sessions_to_target?: number;
  trend: "improving" | "stable" | "declining" | "new";
}

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface ReportActualGradeRequest {
  actual_grade: number;
  assessment_type?: string;
}

export interface UpdateMasteryRequest {
  user_id: string;
  concept_id: string;
  signal_type:
    | "correct_answer"
    | "incorrect_answer"
    | "needed_hint"
    | "confusion_detected";
  signal_value: number; // 0-1
  session_id?: string;
}

export interface LLMCompleteRequest {
  prompt: string;
  system_prompt?: string;
  task_type?: "standard" | "reasoning";
  max_tokens?: number;
}

export interface ExtractConceptsRequest {
  text: string;
  course_name?: string;
}

export interface AnalyzeRequest {
  prompt: string;
  context?: Record<string, unknown>;
  max_tokens?: number;
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

export interface GradePredictionResponse {
  prediction: GradePrediction;
  course_id: string;
  snapshot_id?: string;
}

export interface MasteryMapEntry {
  concept_id: string;
  concept_name: string;
  weight: number;
  raw_score: number;
  effective_score: number;
  confidence: number;
  attempt_count: number;
  days_since_practice?: number;
}

export interface MasteryMapResponse {
  course_id: string;
  concepts: MasteryMapEntry[];
  gaps: MasteryMapEntry[];
  strengths: MasteryMapEntry[];
  overall_mastery: number; // 0-100
}

export interface GradeSnapshot {
  id: string;
  predicted_grade: number;
  predicted_letter: string;
  confidence: number;
  snapshot_type: string;
  created_at: string;
}

export interface GradeHistoryResponse {
  course_id: string;
  snapshots: GradeSnapshot[];
}

export interface MasteryUpdateResponse {
  concept_id: string;
  old_score: number;
  new_score: number;
  new_confidence: number;
  attempt_count: number;
}

export interface LLMCompleteResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ExtractConceptsResponse {
  concepts: Array<{
    name: string;
    description: string;
    estimated_weight: number;
  }>;
  course_name?: string;
}

export interface AnalyzeResponse {
  analysis: string;
  model: string;
}
