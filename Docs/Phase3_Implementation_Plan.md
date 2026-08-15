# Phase 3: Dialogue State Machine & Simulation Engine

This plan covers the implementation of the dialogue state machine, which orchestrates the communication flow between the System, Vendor, and Tenant to negotiate a maintenance time slot and move the request from `TRIAGED` all the way to `SCHEDULED` (and eventually `COMPLETED`).

## Design Decisions
1. **Message Generation**: The system uses deterministic template strings for outbound messages to vendors and tenants to save tokens and ensure consistency.
2. **Vendor Selection**: The system picks the first vendor that matches the issue category.
3. **AI Parsing**: OpenAI structured outputs with Pydantic are used to parse replies.

## Refinements & Guardrails
1. **State Fallbacks for Ambiguity**: The Pydantic schemas include a `confidence_score` (0.0-1.0) and a `needs_human_escalation` boolean. If the tenant's reply is ambiguous (e.g. "maybe Friday morning?"), the system gracefully halts automated scheduling and flags it for manual review instead of forcing a `SCHEDULED` state.
2. **Avoid Endless Loops**: The negotiation process includes a counter. If the vendor and tenant fail to agree after 3 attempts, the request is marked for manual escalation to prevent an infinite loop.

## Proposed Changes

### Database Changes
#### [MODIFY] `app/models.py`
- Add `negotiation_iterations: int` and `needs_human_review: bool` to `MaintenanceRequest` to support the new guardrails.

### AI Parsing for Dialogue
#### [NEW] `app/ai_dialogue.py`
This module handles extracting intents from replies using OpenAI structured outputs.
- **`VendorReply`**: Extracts `proposed_slot` (str | None), `confidence_score` (float), and `needs_human_escalation` (bool).
- **`TenantReply`**: Extracts `agreed` (bool), `alternative_slot` (str | None), `confidence_score` (float), and `needs_human_escalation` (bool).
- **Functions**: `parse_vendor_reply(msg)`, `parse_tenant_reply(msg)`.

### State Machine Logic
#### [NEW] `app/state_machine.py`
A module to handle state transitions and business logic.
- **`dispatch_to_vendor(request_id, db_session)`**: 
  - Finds a matching Vendor for the Request's category (picks the first one).
  - Generates a templated dispatch message and adds it to `CommunicationLog`.
  - Updates Request status from `TRIAGED` to `DISPATCHED`.
- **`handle_incoming_message(request_id, sender, raw_message, db_session)`**:
  - Validates endless loop condition (max 3 negotiation iterations). If exceeded, flags for manual review.
  - If `sender == "VENDOR"`: Parses the proposed slot. If confident, logs and generates a templated message to the Tenant proposing the slot.
  - If `sender == "TENANT"`: Parses their response. If confident and agreed, creates a `WorkOrder`, sets status to `SCHEDULED`, and notifies both parties. If they disagree, asks the vendor for a new slot (incrementing iteration count). If ambiguous (`needs_human_escalation`), it stops the loop.

### API Simulation Endpoints
#### [MODIFY] `app/main.py`
- **`POST /simulate/dispatch/{request_id}`**: Manually trigger dispatching a TRIAGED request to a vendor.
- **`POST /simulate/message`**: Accepts `{"request_id": 1, "sender": "VENDOR" | "TENANT", "message": "..."}`. This simulates an incoming WhatsApp/Email reply and feeds it into the state machine.
- **`GET /requests/{request_id}`**: Retrieve the full state of a request, including its `CommunicationLog` and `WorkOrder`.

## Verification Plan

### Automated Tests / Simulation Script
#### [NEW] `app/simulate_flow.py`
A Python script that uses the existing database to run an end-to-end simulation, demonstrating both successful slot negotiation and fallback behavior for ambiguity.
