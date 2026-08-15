# Phase 3: Dialogue State Machine & Simulation Engine - Walkthrough

The Dialogue State Machine and Simulation endpoints have been successfully implemented.

## What Was Accomplished
1. **Schema Updates**:
   - Added `negotiation_iterations` (int) and `needs_human_review` (bool) to the `MaintenanceRequest` model to handle escalation logic and prevent endless loops.

2. **Dialogue Parsing**:
   - Created `app/ai_dialogue.py` leveraging OpenAI Structured Outputs (via OpenRouter).
   - `VendorReply` extracts the proposed slot.
   - `TenantReply` determines agreement or alternatives.
   - Both models calculate a `confidence_score` and flag `needs_human_escalation` if the reply is ambiguous.

3. **State Machine Logic**:
   - Implemented `app/state_machine.py` with strict transition paths (`TRIAGED` -> `DISPATCHED` -> `SCHEDULED`).
   - Uses **deterministic template strings** for all outbound communications.
   - Escapes to human review if parsing confidence is low, if the AI detects ambiguity, or if the max negotiation iterations (3) are reached.

4. **Simulation Setup**:
   - Added `POST /simulate/dispatch/{request_id}` to trigger the initial vendor dispatch.
   - Added `POST /simulate/message` to act as a webhook receiver for Vendor and Tenant replies.
   - Created `app/simulate_flow.py`, an end-to-end Python script that tests the entire back-and-forth negotiation successfully.

## How to Verify
Before running the simulation script, make sure your OpenRouter API key is exported:
```bash
export OPENAI_API_KEY="sk-or-v1-..."
```
Then run the simulation script in one terminal (make sure the FastAPI server is running in another):
```bash
venv/bin/python app/simulate_flow.py
```
This script will:
1. Submit an initial water leak request.
2. Dispatch the request to the first matching vendor.
3. Simulate the vendor proposing Thursday.
4. Simulate the tenant rejecting Thursday and proposing Friday.
5. Simulate the vendor agreeing to Friday.
6. Display the final `WorkOrder` and `CommunicationLog` thread.
