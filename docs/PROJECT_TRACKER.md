# Stock Options Intelligence — Project Tracker

## Project Metadata
- Repo: stock-options-intelligence
- Owner: Pallab Basu Roy
- System Type: Data + ML Trading Intelligence Platform
- Canonical Design Doc: Stock Trading Design document.pdf
- Tracking Mode: Repo-native (Git versioned)
- Current Phase: Phase 1 — Local Data Ingestion (TEST)
- Last Updated: 2026-02-07

---

## Phase Overview

| Phase | Description | Status |
|------|------------|--------|
| Phase 0 | Architecture & Design | ✅ Complete |
| Phase 1 | Local Data Ingestion (REST, TEST) | 🟡 In Progress |
| Phase 2 | Feature Engineering + Offline ML | ⏳ Planned |
| Phase 3 | Real-time Streaming + Orchestration | ⏳ Planned |
| Phase 4 | Dashboard + Alerts | ⏳ Planned |

---

## Phase 1 — Local Data Ingestion (TEST)

### Milestone 1.1 — Stock Data Pipeline (SPY)

**Objective**  
Implement REST-based SPY stock aggregate ingestion using Polygon.io in TEST mode, with local storage and logging.

**Scope**
- REST polling only
- No WebSockets
- No Kafka
- No ML
- Local filesystem output

| Task ID | Task | Tools | Status | Tests |
|------|------|------|------|------|
| 1.1.1 | Stock ingestion module | Python, requests, pandas, Polygon REST | ✅ Complete | Manual |
| 1.1.2 | File storage (CSV / JSONL) | pandas | ✅ Complete  | Manual |
| 1.1.3 | Logging & error handling | logging | ✅ Complete | Manual |
| 1.1.4 | CLI runner | argparse | ✅ Complete | Manual |
| 1.1.5 | Rate-limit & empty-data guards | requests | ✅ Complete | Manual |

**Exit Criteria**
- [x] Can fetch SPY data via Polygon REST
- [x] Writes data under ./data/stocks/YYYY-MM-DD/
- [x] Logs success, failures, and retries
- [x] Re-runnable without duplication
- [x] Works on non-trading day without crashing

---
### Milestone 1.2 — Options Data Pipeline (REST)

**Objective**  
Implement robust REST-based SPY options chain ingestion with explicit failure contracts and deterministic persistence behavior.

**Scope**
- Polygon REST (options contracts endpoint)
- No streaming / WebSockets
- No ML or feature derivation
- Local filesystem output only
- Contract-first testing before pagination

| Task ID | Task | Tools | Status | Tests |
|------|------|------|------|------|
| 1.2.1 | Options chain ingestion (core) | Python, requests, pandas, Polygon REST | ✅ Complete | Contract tests (pytest) |

**Ingestion Guarantees**
- Deterministic DataFrame schema for all fetches
- Hard failure on malformed API responses
- Hard failure on missing required fields
- Hard failure on API rate limiting (HTTP 429)
- Safe handling of empty result sets

**Exit Criteria**
- [x] Fetches options contracts for SPY via Polygon REST
- [x] Returns stable schema even when API returns no results
- [x] Fails fast on malformed JSON responses
- [x] Fails fast on missing required fields
- [x] Fails fast on API rate limits (HTTP 429)
- [x] Safe to extend with pagination & batching

---

### Milestone 1.3 — News Data Pipeline (REST)
🔒 Locked until Milestone 1.1 complete

---

## Known Risks / Open Questions
- Polygon REST behavior on weekends / holidays
- File format standard (CSV vs JSONL)
- Timezone normalization standard (UTC only)

---

## Next Immediate Action
👉 Implement `src/data_ingestion/stock_prices.py`

