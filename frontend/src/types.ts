export type Incident = { id: string; title: string; description: string };
export type Evidence = {
  id: string;
  path: string;
  start_line: number;
  end_line: number;
  excerpt: string;
  sha256: string;
};
export type SourceQuote = {
  evidence_id: string;
  line: number;
  quote: string;
  quote_truncated?: boolean;
};
export type Hypothesis = {
  id: string;
  alias?: string;
  claim: string;
  status: string;
  reason: string;
  evidence_ids: string[];
  check_ids: string[];
  trigger?: string;
  mechanism?: string;
  effect?: string;
  citations?: SourceQuote[];
  support_level?: string;
};
export type ExecutedCheck = {
  check_id: string;
  status: string;
  detail: string;
  kind?: string;
  baseline?: { status: string; detail: string };
  trial?: { status: string; detail: string };
  changes?: { path: string; value: unknown }[];
};
export type TraceEvent = {
  seq: number;
  timestamp: string;
  role: string;
  kind: string;
  message: string;
  data: Record<string, unknown>;
};
export type Diagnostic = {
  outcome: string;
  summary: string;
  hypothesis_ids?: string[];
  next_actions: string[];
  limitations: string[];
  evidence_ids: string[];
  support_level?: string;
  rendered_from_reviewed_records?: boolean;
};
export type Run = {
  id: string;
  incident_id: string;
  mode: string;
  provider: string;
  model: string;
  status: string;
  created_at: string;
  updated_at: string;
  engine_version?: string;
  cancel_requested: number;
  state: {
    engine_version?: string;
    role?: string;
    turn?: number;
    hypotheses?: Hypothesis[];
    checks?: ExecutedCheck[];
    diagnostic?: Diagnostic;
  };
  events: TraceEvent[];
  evidence: Evidence[];
  metrics: {
    model_calls: number;
    tool_calls: number;
    tool_successes: number;
    input_tokens: number | null;
    output_tokens: number | null;
    usage_complete: boolean;
  };
};
export type Health = {
  model: string;
  provider: string;
  available: boolean;
  detail: string;
  transport: string;
  persistence: string;
  limits: { model_calls: number; tool_calls: number };
};
export type Benchmark = {
  status: string;
  message?: string;
  model?: string;
  total_runs?: number;
  scheduled_runs?: number;
  methods?: {
    method: string;
    runs: number;
    correct?: number;
    correct_total?: number;
    correct_supported: number;
    unsupported: number;
    abstention_correct: number;
    median_latency_s: number;
    model_calls: number;
    tool_calls: number;
    input_tokens: number | null;
    output_tokens: number | null;
  }[];
};
export type View = "workbench" | "history" | "benchmark" | "system";
export type RunTab = "overview" | "activity" | "evidence";
