# Issue Whisperer — Demo Script

## Scenario

A maintainer receives a new GitHub issue:
> "Application crashes when uploading files larger than 100 MB via the web UI"

## Demo Flow (≈ 60 seconds)

### Step 1 — Paste Issue
Paste the new issue title and body into the Issue Whisperer UI.

### Step 2 — Analyze
Click **Analyze**. The system:
1. Embeds the new issue text locally (RTX 2050, no API call).
2. Queries the FAISS index of historical issues.
3. Returns the top-3 similar candidates with similarity scores.

### Step 3 — Triage
The **Triage Agent** receives:
- The new issue
- Top-3 retrieved candidates
- Repository context

It outputs structured JSON:
```json
{
  "label": "bug",
  "is_duplicate": true,
  "duplicate_of": 142,
  "confidence": 0.91,
  "evidence_quote": "CSV upload crashes above 100MB",
  "draft_reply": "This appears to be a duplicate of #142..."
}
```

### Step 4 — Verify
The **Verifier Agent** independently evaluates the duplicate claim.
It locates literal evidence from issue #142 that supports the claim.
The application then **programmatically verifies** the evidence quote exists
in the actual issue text — this is not just LLM self-reporting.

### Step 5 — Human Approval
The UI displays:
- Issue under review
- Suggested label + duplicate candidate
- Confidence score
- Verified evidence quote
- Draft reply

The maintainer clicks **Approve**, **Reject**, or **Edit**.

### Step 6 — Simulated Action
The application prints what it *would* do on GitHub (add label, post comment).
**No GitHub write permissions are used.**

## Key Talking Points for Judges

1. **Why retrieval?** — Historical context exceeds LLM context window.
2. **Why a Verifier?** — Triage agents hallucinate. Independent verification
   reduces false positives programmatically.
3. **Why human approval?** — Trust, safety, and maintainer autonomy.
4. **Zero cost** — Runs entirely on local hardware with Ollama + FAISS.
