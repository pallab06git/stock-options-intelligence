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
| 1.1.5 | Rate-limit & empty-data guards | requests | ⬜ Not Started | Manual |

**Exit Criteria**
- [ ] Can fetch SPY data via Polygon REST
- [ ] Writes data under ./data/stocks/YYYY-MM-DD/
- [ ] Logs success, failures, and retries
- [ ] Re-runnable without duplication
- [ ] Works on non-trading day without crashing

---

### Milestone 1.2 — Options Data Pipeline (REST)
🔒 Locked until Milestone 1.1 complete

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

