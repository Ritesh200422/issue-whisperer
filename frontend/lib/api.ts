/**
 * api.ts — Typed API client for all Issue Whisperer backend endpoints.
 * All network calls go through this module so the backend URL is configured once.
 */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────────

export type HealthResponse = {
  status: string;
  app: string;
  version: string;
};

export type Candidate = {
  number: number;
  title: string;
  body: string;
  labels: string[];
  state: string;
  similarity_score: number;
};

export type TriageDecision = {
  label: string;
  is_duplicate: boolean;
  duplicate_of: number | null;
  confidence: number;
  evidence_quote: string | null;
  draft_reply: string;
};

export type VerificationDecision = {
  status: "confirmed" | "possibly_related" | "not_duplicate";
  reason: string;
  evidence_quote: string | null;
};

export type AnalyzeResponse = {
  label: string;
  is_duplicate: boolean;
  duplicate_of: number | null;
  confidence: number;
  evidence_quote: string | null;
  draft_reply: string;
  retrieved_candidates: Candidate[];
  triage: TriageDecision;
  verification: VerificationDecision;
};

export type ApproveResponse = {
  issue_number: number;
  action: string;
  success: boolean;
  simulated_actions: string[];
};

// ── API functions ──────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BACKEND_URL}/health`, {
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function analyzeIssue(
  title: string,
  body: string
): Promise<AnalyzeResponse> {
  const res = await fetch(`${BACKEND_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, body }),
    signal: AbortSignal.timeout(120_000), // LLM can be slow
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export async function submitApproval(
  issueNumber: number,
  action: "approve" | "reject" | "edit",
  suggestedLabel: string,
  duplicateOf: number | null,
  editedReply: string
): Promise<ApproveResponse> {
  const res = await fetch(`${BACKEND_URL}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      issue_number: issueNumber,
      action,
      suggested_label: suggestedLabel,
      duplicate_of: duplicateOf,
      edited_reply: editedReply,
    }),
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
