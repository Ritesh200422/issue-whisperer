# Changelog

All notable changes to Issue Whisperer are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Phase 1 — Foundation ✅
- FastAPI backend with `/health` endpoint
- Pydantic configuration system (`config.yaml` + environment variable overlays)
- Structured coloured logging
- Next.js + Tailwind CSS frontend showing backend connection status
- Full project directory scaffold
- `requirements.txt` with pinned versions
- `.env.example` with all required variables documented
- `.gitignore` excluding secrets and generated data
- `README.md` skeleton

### Phases 2 to 16 - Complete Pipeline & Agents
- **GitHub Data Pipeline**: Implemented PyGithub fetching with local caching (no GitHub write actions).
- **Embeddings/Retrieval**: Added FAISS vector store with local ll-MiniLM-L6-v2 execution on RTX 2050.
- **Baseline**: Established single-call LLM baseline for evaluation comparisons.
- **Triage Agent**: Added structured reasoning agent mapping issues to candidates with confidence.
- **Verifier Agent**: Integrated independent agent to validate evidence strings programmatically.
- **Evaluation Harness**: Created 10 specific testing cases across real duplicates, label checks, and adversarial examples.
- **Verifier Ablation**: Documented Verifier impact (FDR dropped from 20% to 0%).
- **Human Approval UI**: Finished the Next.js dashboard mimicking GitHub issue resolutions.
- **Tests**: Reached 100% pass rate on all Phase 1-13 PyTest test units.
