# AstroLab AI - Property Maintenance Triage System
## Project Overview
An automated end-to-end Property Maintenance Triage System for a property manager handling residential, commercial, and government buildings.

- **Primary Stack:** Python 3.11+, FastAPI, SQLModel, SQLite, Pydantic, Streamlit, Docker Compose
- **Target Interview Date:** Tuesday, August 18, 2026

---

## Technical Architecture & Design Principles
1. **API First:** FastAPI handles API endpoints and database initializations.
2. **Unified Schemas:** Use SQLModel to combine Pydantic data validation with SQLAlchemy ORM models without duplicate code.
3. **Structured AI Outputs:** OpenAI / Pydantic structured output models for zero-hallucination intake and triage parsing.
4. **Clean Domain Boundaries:** No magic strings, typed Python Enums for states and urgencies.

---

## Domain Data Model Schema

### Enums
- `RequestStatus`: `NEW`, `TRIAGED`, `DISPATCHED`, `SCHEDULED`, `COMPLETED`
- `UrgencyLevel`: `EMERGENCY`, `HIGH`, `ROUTINE`
- `BuildingType`: `RESIDENTIAL`, `COMMERCIAL`, `GOVERNMENT`
- `IssueCategory`: `PLUMBING`, `ELECTRICAL`, `ELEVATOR_HVAC`, `ACCESS_CONTROL`

### Core Entities
1. **Building:** `id` (int), `name` (str), `type` (BuildingType), `address` (str)
2. **Unit:** `id` (int), `building_id` (FK -> Building.id), `unit_identifier` (str, e.g. "Apt 3C", "Block B 5th floor")
3. **Vendor:** `id` (int), `name` (str), `category` (IssueCategory), `email` (str), `phone` (str)
4. **MaintenanceRequest:**
   - `id` (int)
   - `raw_message` (str)
   - `channel` (str, e.g. "WhatsApp", "Email")
   - `status` (RequestStatus, default: `NEW`)
   - `urgency` (UrgencyLevel, optional)
   - `category` (IssueCategory, optional)
   - `building_id` (FK -> Building.id, optional)
   - `unit_id` (FK -> Unit.id, optional)
   - `created_at` (datetime)
5. **WorkOrder:**
   - `id` (int)
   - `request_id` (FK -> MaintenanceRequest.id)
   - `vendor_id` (FK -> Vendor.id, optional)
   - `scheduled_slot` (str, optional)
   - `notes` (str, optional)
6. **CommunicationLog:**
   - `id` (int)
   - `request_id` (FK -> MaintenanceRequest.id)
   - `sender` (str, e.g. "TENANT", "SYSTEM", "VENDOR")
   - `message` (str)
   - `timestamp` (datetime)

---

## Implementation Roadmap

### Phase 1: Architecture & Data Schema Setup (COMPLETE)
- [x] Set up Python environment dependencies (`requirements.txt`: `fastapi`, `uvicorn`, `sqlmodel`, `pydantic`, `pydantic-settings`).
- [x] Create folder structure (`app/models.py`, `app/database.py`, `app/main.py`).
- [x] Implement all SQLModel data models and Python Enums in `app/models.py`.
- [x] Set up SQLite DB connection and startup script in `app/database.py`.
- [x] Implement a database seed script (`app/seed.py`) to prepopulate sample Buildings, Units, and Vendors.
- [x] Verify setup via FastAPI startup endpoint `/` or `/health`.

### Phase 2: Core AI Extraction Engine (COMPLETE)
- [x] Pydantic structured extraction model (`ExtractedTriage`).
- [x] OpenAI API integration for JSON parsing.
- [x] Rule-engine deterministic override layer.

### Phase 3: Dialogue State Machine & Simulation Engine (COMPLETE)
- [x] State Machine handler.
- [x] Automated Vendor-Tenant slot negotiation logic.

### Phase 4: Streamlit Dashboard UI (COMPLETE)
- [x] Tabbed interface for intake, work order tracking, and chat logs.

### Phase 5: Containerization & Documentation (CURRENT PHASE)
- [ ] `docker-compose.yml` and `README.md`.

---

## Future Polish & Edge Cases (Post-MVP)
1. **Manual Dispatch Override:** Update Tab 4's "Trigger Dispatch" button so it acts strictly as a manual override to release requests that were flagged for human review (after the human operator updates the missing building/unit info).
2. **Contextual UI Improvements:** Add more context to Tabs 2, 3, and 4 (such as showing the initial raw message directly or via an expander/tooltip) so the user understands the nature of the request without relying solely on the Request ID.
3. **Edge Case Testing:** Conduct rigorous testing with complex, ambiguous tenant replies (e.g. multi-part scheduling questions, uncooperative vendors) to ensure the AI fallback state machine handles them gracefully.