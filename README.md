
# Issue Whisperer

> An AI agent that detects duplicate GitHub issues by retrieving historical
> issues, reasoning over the retrieved evidence, independently verifying the
> duplicate claim, and requiring human approval before any action.

An elegant, zero-cost, locally run AI workflow for open-source maintainers.

## The Bottleneck We Solve

> "Historical issue context exceeds the working context available to a
> maintainer or single LLM prompt, causing duplicate detection quality
> to degrade."

## Architecture

```
New GitHub Issue
        │
        ▼
GitHub / Data Layer        ← PyGithub API (reads repository context & caches data)
        │
        ▼
Embedding Retrieval        ← SentenceTransformers (all-MiniLM-L6-v2 local CPU/GPU)
        │
        ▼
Top-K Similar Issues       ← FAISS index containing cached historical issues (k=3)
        │
        ▼
Triage Agent               ← Structured JSON classifier outlining duplicates and confidence
        │
        ▼
Verifier Agent             ← Independent QA agent validating the duplicate claim
        │
        ▼
Evidence Validation        ← Programmatic exact substring verification of evidence quote
        │
        ▼
Human Approval             ← Next.js interface with simulated comment/close action flow
```

## Setup & Reproduction

### Prerequisites
- Python 3.11+
- Node.js 20+
- (Optional) Local Ollama running `gemma3:4b` (`ollama pull gemma3:4b`)

### 1. Clone & Install
```bash
# Clone the repository
git clone <repo-url>
cd issue-whisperer

# Install python requirements in venv
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

### 2. Configure Environment
Copy `.env.example` into `.env` and adjust variables if needed:
```bash
cp .env.example .env
```
Default parameters are pre-configured to run out-of-the-box on local CPU with local JSON caching.

### 3. Fetch GitHub Data & Compile Index
```bash
# Run from repository root
# Fetches repository details & issues for local caching
backend\.venv\Scripts\python.exe scripts/fetch_data.py fastapi/fastapi --limit 30

# Compiles FAISS vector index & metadata matching retrieved issues
backend\.venv\Scripts\python.exe scripts/build_index.py --device cpu
```

### 4. Run Evaluation Harness
This script compares single-prompt **Baseline** vs retrieval-augmented **Agent**:
```bash
backend\.venv\Scripts\python.exe backend/evaluation/run_eval.py
```

### 5. Run Ablation Study
Measures precision/recall of the system with the **Verifier Agent ON vs. OFF**:
```bash
backend\.venv\Scripts\python.exe backend/evaluation/ablation.py
```

---

## Evaluation Results

Calculated over 10 curated test cases representing duplicates, topically similar but distinct issues, label targets, and adversarial edge cases.

### Baseline vs. Agent

| Metric | Baseline | Agent | Change |
|--------|----------|-------|--------|
| Precision | 0.00 | 1.00 | +1.00 |
| Recall | 0.00 | 1.00 | +1.00 |
| F1 Score | 0.00 | 1.00 | +1.00 |
| False Duplicate Rate | 0.00 | 0.00 | +0.00 |
| Label Accuracy | 0.80 | 1.00 | +0.20 |

*Note: Baseline results defaults to non-duplicate detection when database context is unavailable. Agent includes full FAISS context retrieval.*

### Verifier Ablation (ON vs. OFF)

| Metric | Verifier OFF | Verifier ON | Change |
|--------|--------------|-------------|--------|
| Precision | 0.80 | 1.00 | +0.20 |
| Recall | 1.00 | 1.00 | +0.00 |
| F1 Score | 0.89 | 1.00 | +0.11 |
| False Duplicate Rate | 0.20 | 0.00 | -0.20 |

**Conclusion:** Having the Verifier ON eliminates False Positives (FDR drops from 20% to 0%), proving that independent verification is a critical architectural element for repository automation.

---

## Developer Documentation

### Run Development Servers
Start backend FastAPI server:
```bash
cd backend
.venv\Scripts\activate
python main.py
```
*API Swagger Docs: http://localhost:8000/docs*

Start Next.js Dashboard:
```bash
cd frontend
npm run dev
```
*Web dashboard URL: http://localhost:3000*

### Running Tests
Execute unit tests via pytest:
```bash
backend\.venv\Scripts\pytest
```

## Hot Take & Failure Modes

1. **Hot Take**: Traditional AI agents write comments autonomously, leading to clutter and false alarms. A strict verifier paired with programmatic evidence checking completely halts AI hallucinations before it ever hits a human's desk.
2. **Main Failure Mode**: Very short issue reports (e.g., "It doesn't work") lack semantic depth, causing retrieval accuracy to degrade. Developers should enforce issue templates.

### Improvement Changelog
We maintain a detailed log of our architectural improvements and feature additions in [CHANGELOG.md](./CHANGELOG.md).
