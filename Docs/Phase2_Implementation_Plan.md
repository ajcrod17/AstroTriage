# Phase 2: Core AI Extraction Engine

This plan covers the implementation of the AI extraction and triage pipeline, which will parse incoming maintenance requests into structured data using OpenAI, and then apply deterministic rules to ensure safety and correctness.

## Open Questions for the User
1. **OpenAI Model**: I plan to use `gpt-4o-mini` as it's fast, cost-effective, and supports Structured Outputs natively. Is this acceptable, or would you prefer `gpt-4o`?
2. **API Key**: Ensure you have an `OPENAI_API_KEY` exported in your environment. If one is not present, should I build a "mock" mode for local development without a key?
3. **Rule Engine specifics**: Should the rule engine strictly override the AI's urgency, or also its category routing?

## Proposed Changes

### Dependencies
- Add `openai` to `requirements.txt`.

---

### AI Service Component
#### [NEW] `app/ai.py`
This module will handle OpenAI interactions and defining the Extraction schema.
- **`ExtractedTriage` (Pydantic Model)**:
  - `building_clue` (str | None): Any mention of the building name or address.
  - `unit_clue` (str | None): Any mention of the apartment, floor, or unit.
  - `category` (IssueCategory): The identified issue category.
  - `urgency` (UrgencyLevel): The AI-determined urgency.
  - `reasoning` (str): Brief explanation for the categorization.
- **`extract_triage_info(raw_message: str)`**:
  - Uses `client.beta.chat.completions.parse` with the `ExtractedTriage` schema to guarantee perfectly structured JSON extraction from the LLM.

---

### Rule Engine & Overrides
#### [NEW] `app/triage_rules.py`
A deterministic layer to enforce business rules over the AI's output.
- **`apply_overrides(triage: ExtractedTriage, raw_message: str) -> ExtractedTriage`**:
  - E.g. Rule 1: If `raw_message` contains "elderly" or "trapped" and category is `ELEVATOR_HVAC`, force urgency to `EMERGENCY`.
  - E.g. Rule 2: If `raw_message` mentions "water" and "ceiling", force urgency to at least `HIGH`.

---

### API Integration
#### [MODIFY] `app/main.py`
- Add a new endpoint `POST /intake` that accepts a JSON body with `{"message": "...", "channel": "..."}`.
- The endpoint will:
  1. Call `extract_triage_info`.
  2. Pass the result through `apply_overrides`.
  3. Attempt to resolve the `building_clue` and `unit_clue` to actual DB entities using simple substring matching against the database.
  4. Create a new `MaintenanceRequest` in the database with the resolved data and `status="TRIAGED"`.
  5. Return the created request.

## Verification Plan

### Automated Tests
- Since we don't have a test suite set up yet, I will write a simple `app/test_ai.py` script (or integrate pytest) to verify that the structured output parser and the rule engine behave as expected given the 4 example messages from the take-home prompt.

### Manual Verification
- You will be able to start the API and use `curl` or FastAPI's `/docs` to submit the sample messages and observe the created `MaintenanceRequest` entities in the SQLite database.
