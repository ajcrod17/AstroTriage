# Phase 3: Dialogue State Machine & Simulation Engine

This plan covers the implementation of the dialogue state machine, which orchestrates the communication flow between the System, Vendor, and Tenant to negotiate a maintenance time slot and move the request from `TRIAGED` all the way to `SCHEDULED` (and eventually `COMPLETED`).

## Open Questions for the User
1. **Message Generation**: When the system sends a message to the vendor or tenant, should we use the LLM to generate a natural, context-aware message, or should we use deterministic template strings (e.g. `f"Dear {vendor.name}, we have a {category} issue..."`) to save tokens and ensure consistency?
2. **Vendor Selection**: For the pilot, if there are multiple vendors for a category, should we just pick the first one we find in the database, or do we need round-robin logic?
3. **AI Parsing**: I will use OpenAI structured outputs to parse the Vendor's proposed time slots and the Tenant's approval/rejection. Does this sound good?

## Proposed Changes

### AI Parsing for Dialogue
#### [NEW] `app/ai_dialogue.py`
This module will handle extracting intents from replies using OpenAI structured outputs.
- **`VendorReply`**: Extracts `proposed_slot` (str) from the vendor's message.
- **`TenantReply`**: Extracts `agreed` (bool) and `alternative_slot` (str | None) from the tenant's message.
- **Functions**: `parse_vendor_reply(msg)`, `parse_tenant_reply(msg)`, and potentially `generate_system_message(...)` if we use the LLM for generation.

### State Machine Logic
#### [NEW] `app/state_machine.py`
A module to handle state transitions and business logic.
- **`dispatch_to_vendor(request_id, db_session)`**: 
  - Finds a matching Vendor for the Request's category.
  - Generates a dispatch message and adds it to `CommunicationLog`.
  - Updates Request status from `TRIAGED` to `DISPATCHED`.
- **`handle_incoming_message(request_id, sender, raw_message, db_session)`**:
  - If `sender == "VENDOR"`: Parses the proposed slot, logs the message, and generates a message to the Tenant proposing the slot.
  - If `sender == "TENANT"`: Parses their response. If they agree, creates a `WorkOrder`, sets status to `SCHEDULED`, and notifies both parties. If they disagree, asks the vendor for a new slot.

### API Simulation Endpoints
#### [MODIFY] `app/main.py`
We will add endpoints to simulate the flow:
- **`POST /simulate/dispatch/{request_id}`**: Manually trigger dispatching a TRIAGED request to a vendor.
- **`POST /simulate/message`**: 
  Accepts `{"request_id": 1, "sender": "VENDOR" | "TENANT", "message": "..."}`. This simulates an incoming WhatsApp/Email reply and feeds it into the state machine.
- **`GET /requests/{request_id}`**: Retrieve the full state of a request, including its `CommunicationLog` and `WorkOrder`, so we can see the conversation thread.

## Verification Plan

### Automated Tests / Simulation Script
#### [NEW] `app/simulate_flow.py`
I will create a Python script that uses the existing database and `test_ai.py` messages to run an end-to-end simulation:
1. Intake a message (Phase 2).
2. Trigger dispatch to Vendor.
3. Simulate the Vendor replying with "I can come on Thursday afternoon".
4. Simulate the Tenant replying with "Thursday works for me".
5. Verify that the `WorkOrder` is created and the state is `SCHEDULED`.
