# Architectural Decisions Log

This file records architectural and process decisions that should not be re-litigated
unless explicitly revisited in a later phase.

---

## AD-001 — Repo-Native Tracking as System of Record
**Date**: 2026-02-07  
**Decision**: Use markdown-based tracking inside the Git repository  
**Rationale**:
- Versioned with code
- Zero dependency on external tools
- Instant context recovery after long breaks  
**Revisit?** No

---

## AD-002 — Phase 1 Uses REST-Based Ingestion Only
**Date**: 2026-02-07  
**Decision**: All Phase 1 ingestion pipelines use REST polling  
**Rationale**:
- Deterministic behavior
- Easier debugging
- Lower cognitive load during bootstrap  
**Revisit?** Phase 3 (real-time)

---

## AD-003 — Aggregates Over Quote-Level Data
**Date**: 2026-02-07  
**Decision**: Use Polygon aggregate endpoints instead of quote-level feeds  
**Rationale**:
- Lower noise
- Lower data volume
- Cost-efficient for experimentation  
**Revisit?** Only for HFT or ultra-low-latency extensions

---

## AD-004 — Bootstrap with Simple Granularity
**Date**: 2026-02-07  
**Decision**: Start with coarse aggregation (daily or minute-level) before per-second data  
**Rationale**:
- Validate end-to-end pipeline first
- Reduce API friction during early testing  
**Revisit?** Within Phase 1 after baseline is stable
