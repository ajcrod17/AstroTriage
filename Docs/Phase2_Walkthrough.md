# Phase 2: Core AI Extraction Engine - Walkthrough

The AI Extractor and triage system has been fully implemented in this phase.

## What Was Accomplished
1. **OpenAI Integration via OpenRouter**:
   - Added `openai` to dependencies.
   - Created `app/ai.py` featuring a Pydantic structure (`ExtractedTriage`) to enforce structured outputs via `client.beta.chat.completions.parse`.
   - Pointed the OpenAI client directly to `https://openrouter.ai/api/v1` and used the `openai/gpt-4o-mini` model as requested.

2. **Rule Engine**:
   - Created `app/triage_rules.py` implementing strict deterministic rules to act as a guardrail against AI hallucination.
   - Added `HAZARDOUS` to the `IssueCategory` ENUM in `app/models.py`.
   - Rules include forcibly routing gas leaks to `HAZARDOUS` and `EMERGENCY`, as well as recognizing human safety keywords like "trapped" or "elderly" to force an `EMERGENCY` urgency level regardless of the AI's initial categorization.

3. **Integration and Endpoints**:
   - Rewrote `app/main.py` adding a new `POST /intake` route. 
   - The route parses the raw request through the LLM, applies overrides from the rule engine, attempts to resolve the `building_id` and `unit_id` from the DB using substring matching, and saves the final `MaintenanceRequest` to the database.

4. **Testing Setup**:
   - Created `app/test_ai.py` containing the four test messages from the take-home prompt to simulate and verify output without needing to start the full API.

## How to Verify
Before running the tests or hitting the endpoint, export your OpenRouter key:
```bash
export OPENAI_API_KEY="sk-or-v1-..."
```

Run the test script to see the AI extractions vs. Rule Engine overrides in action:
```bash
venv/bin/python -m app.test_ai
```

You can also run the FastAPI server and submit a POST request to `/intake`:
```bash
venv/bin/uvicorn app.main:app
```
Then send a CURL request with a test message:
```bash
curl -X POST http://127.0.0.1:8000/intake -H "Content-Type: application/json" -d '{"message": "I smell gas in apartment 1A", "channel": "Email"}'
```
