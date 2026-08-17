# AstroLab AI: AstroTriage Platform

AstroTriage is an intelligent, automated property maintenance triage and dispatch platform designed for high-volume residential, commercial, and government property portfolios. It intercepts multi-channel incoming requests (WhatsApp, Email, Web Portal), extracts structured entity and category data via LLMs, enforces deterministic safety guardrails, auto-dispatches domain-specific vendors, and orchestrates multi-party scheduling negotiations between tenants and suppliers.

---

## 🏗️ Design System & Architecture

AstroTriage follows an **API-First, Decoupled Microservice Architecture**. The user-facing Streamlit dashboard communicates with the backend exclusively via FastAPI HTTP REST endpoints, preserving strict service boundaries and enabling plug-and-play integrations with external webhook providers.

### Component Interaction Architecture

```text
                              +-------------------------------------------------------+
                              |                 INGESTION CHANNELS                    |
                              |             (Streamlit UI (Tabs 1 & 4))               |
                              +---------------------------+---------------------------+
                                                          |
                                                          v
+-------------------------------------------------------------------------------------------------------------------------+
| FASTAPI BACKEND (Uvicorn ASGI Server)                                                                                   | 
|                                                                                                                         |
|  1. Intake Endpoint (POST /requests)                                                                                    | 
|     └── Validates payload schema automatically via Pydantic                                                             | 
|                                                                                                                         |
|  2. AI Extraction Engine (OpenAI / OpenRouter API - GPT-4o-mini)                                                        | 
|     ├── Syntactically enforced via OpenAI Structured Outputs (client.beta.chat.completions.parse)                       | 
|     ├── Extracts: IssueCategory, UrgencyLevel, building_clue, unit_clue, confidence_score                               | 
|     └── Temporal Grounding: Injects server ISO timestamp into system prompt to eliminate relative date hallucination    | 
|                                                                                                                         |
|  3. Deterministic Safety & Guardrail Engine (app/triage_rules.py)                                                       | 
|     ├── Life-Safety Keyword Scan (e.g., "gas leak", "water coming through ceiling", "trapped")                          | 
|     ├── Overrides LLM: Escalates Urgency -> EMERGENCY & Category -> HAZARDOUS / ELEVATOR_HVAC                           | 
|     └── Ambiguity Trigger: If confidence < 0.7 or Unit FK cannot be resolved -> Flags needs_human_review & halts flow   | 
|                                                                                                                         |
|  4. Entity Resolution & Relational Persistence (SQLModel + SQLite)                                                      | 
|     ├── Substring/relational lookup maps extracted string clues to Building and Unit Foreign Keys                       | 
|     └── Creates MaintenanceRequest record (Status: NEW -> TRIAGED -> DISPATCHED)                                        | 
|                                                                                                                         |
|  5. Multi-Agent Dialogue & Negotiation State Machine                                                                    | 
|     ├── Auto-assigns domain vendor based on IssueCategory (e.g., PLUMBING -> Mario Bros Plumbing)                       | 
|     ├── Deterministic Templates: Emits standard supplier slot request notifications                                     | 
|     ├── Inbound Parser: Parses supplier availability proposals and verifies tenant schedule agreements                  | 
|     └── Work Order Finalization: Creates WorkOrder record and transitions state: DISPATCHED -> SCHEDULED -> COMPLETED   | 
+-------------------------------------------------------------------------------------------------------------------------+
                                                          |
                                                          v
                              +-------------------------------------------------------+
                              |                  PRESENTATION LAYER                   | 
                              |  - Streamlit Control Center (Port 8501)               | 
                              |  - Interactive Swagger OpenAPI Docs (Port 8000/docs)  | 
                              +-------------------------------------------------------+
```

---

## 🔄 End-to-End Request Lifecycle

```text
[ Unstructured Raw Message ] (Streamlit UI / Direct API POST) 
│
▼
[ Phase 1: Intake & AI Parsing ] ────► Extracted Schema (Category, Urgency, Location, Confidence) 
│
▼
[ Phase 2: Guardrail Engine ]
├── Ambiguous Unit OR Confidence < 0.7 ──► [ Flag: needs_human_review ] ──► (Halted at TRIAGED) 
└── Safety Hazard Detected ──────────────► [ Override: Force EMERGENCY / HAZARD ] 
│
▼ (Resolved & Validated)
[ Phase 3: Automated Dispatch ] ───────► Auto-Assign Domain Vendor ──► Status: DISPATCHED 
│
▼
[ Phase 4: Negotiation Loop ] ────────► Supplier Slot Proposal ──► Tenant Confirmation 
│
▼
[ Phase 5: Work Order Finalized ] ────► Status: SCHEDULED ──► Execution ──► Status: COMPLETED 
```

### Lifecycle Stage Breakdown
1. **`NEW` (Intake)**: Raw message payload is received alongside metadata (communication channel, timestamp) via `POST /requests`.
2. **`TRIAGED` (Parsing & Safety Gate)**: GPT-4o-mini parses unstructured entities into typed Pydantic models. The deterministic rule engine evaluates hazard keywords. If details are incomplete or confidence is < 0.7, `needs_human_review` is flagged and automated dispatch is blocked.
3. **`DISPATCHED` (Vendor Routing)**: Valid requests match the portfolio vendor responsible for the issue category. An outbound dispatch record is generated.
4. **`SCHEDULED` (Negotiation Machine)**: The system negotiates appointment windows between vendor and tenant using deterministic notification templates to eliminate hallucination.
5. **`COMPLETED` (Resolution)**: Once the work order is signed off, the request state is closed.

---

## 🛠️ Tech Stack Rationale & Architectural Decisions

| Layer / Component | Selected Technology | Technical Rationale & Tradeoffs |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI + Uvicorn** | **Native Asynchronous Performance**: Built on ASGI (Starlette + uvloop), FastAPI provides non-blocking concurrency for I/O-bound LLM API calls, database operations, and external webhooks. It automatically generates interactive OpenAPI/Swagger documentation (`/docs`) directly from code definitions. |
| **Data Layer & ORM** | **SQLModel + SQLite** | **Unified Data Modeling**: SQLModel integrates SQLAlchemy ORM with Pydantic type validation, eliminating code duplication across API schemas and database models. SQLite offers zero-configuration local evaluation with containerized volume persistence (`./data`). |
| **AI Model & Inference** | **GPT-4o-mini** (via OpenRouter/OpenAI) | **Cost vs. Latency Optimization**: Maintenance triage is a high-volume, low-latency operational task. At ≈ $0.15 per 1M input tokens, `gpt-4o-mini` delivers sub-second structured extraction at a fraction of the cost of heavier frontier models (e.g., GPT-4o, Claude 3.5 Sonnet), avoiding architectural overkill. |
| **Reliability Layer** | **OpenAI Structured Outputs + Pydantic** | **Zero-Hallucination Schemas**: Restricts model responses to strictly enforced JSON schemas (`ExtractedTriage`, `VendorReply`), eliminating parsing errors and non-deterministic text variations. |
| **Presentation Dashboard** | **Streamlit** | **Rapid Operational UI**: Provides a clean, dark-mode control center (intake testbed, active work order grids, multi-agent communication threads, simulation consoles) without the build tooling, state management, and configuration overhead of React/Node. |
| **Infrastructure** | **Docker Compose + Makefile** | **Standardized Evaluation Environment**: Single-command startup (`make up`). Uses `python:3.11-slim` base images to balance small image size (~150MB) with standard Debian `glibc` pre-compiled wheel compatibility, avoiding Alpine `musl` build failures. |

---

## 🛡️ Guardrails, Safety & Reliability

* **Deterministic Life-Safety Overrides**: If tenant messages contain hazard terms (e.g., *"smell gas"*, *"flooding"*, *"elevator trapped"*), `triage_rules.py` bypasses LLM categorization, forcing urgency to `EMERGENCY` and routing to hazardous/emergency protocols.
* **Temporal Context Grounding**: To eliminate date hallucinations, the backend dynamically provides the server's ISO timestamp in the system prompt, ensuring relative dates (e.g., *"tomorrow at 2 PM"*) are mapped to accurate calendar slots.
* **Confidence Scoring & Deadlock Prevention**: The parser assigns confidence scores to extracted entities. If confidence is < 0.7, or if tenant-vendor negotiations exceed step limits, the system escalates the request to a human queue (`needs_human_review`) rather than risking faulty dispatches or circular messaging loops.

---

## 🚀 Quick Start

### 1. Configure Environment
Create a `.env` file in the project root:
```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

(OpenRouter API keys or GitHub Models tokens are also supported by configuring `OPENAI_BASE_URL`).

### 2. Launch Services

Start the full stack with a single command:
```bash
make up
```

The backend API boots first, initializes the SQLite database with sample data, and passes a container healthcheck before Streamlit starts.

**Core Management Commands:**
* `make up` - Build and start containers in detached mode.
* `make logs` - Tail live container logs.
* `make clean` - Stop containers and safely wipe database state without permission errors.
* `make restart` - Wipe state and relaunch a fresh instance.
* `make down` - Stop running containers.

*(Windows PowerShell Fallback without `make`):*
```powershell
docker compose up --build -d
docker compose down
docker run --rm -v "${PWD}/data:/data" python:3.11-slim bash -c "rm -rf /data/*"
```

### 3. Application Endpoints

* **Triage Dashboard (Streamlit UI)**: [http://localhost:8501](http://localhost:8501) 
* **Interactive OpenAPI Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs) (Root `http://localhost:8000` redirects automatically to `/docs`).

### 4. Dashboard Overview

| Tab | Name | Role in the System |
| :--- | :--- | :--- |
| **Tab 1** | New Intake | **Ingestion**: Submits initial maintenance issues to the API. |
| **Tab 2** | Request Tracking | **Visualization**: Displays active work orders, statuses, and review flags. |
| **Tab 3** | Communication Details | **Audit**: Shows the multi-agent chat thread between System, Vendor, and Tenant. |
| **Tab 4** | Simulation Console | **Simulation**: Simulates back-and-forth vendor/tenant messages for scheduling. |

---

## 🧪 Testing Walkthrough

Open [http://localhost:8501](http://localhost:8501) in your browser and run through these test scenarios:

### Scenario 1: Zero-Touch Auto-Dispatch & Scheduling (Happy Path)
1. Navigate to **Tab 1: New Intake**.
2. Submit: *"Hi, there is water pouring through the ceiling in apartment 3C."* 
3. Navigate to **Tab 2: Request Tracking**. The request is parsed, unit resolved to Apt 3C, urgency escalated, and status set to `DISPATCHED`.
4. Open **Tab 4: Simulation Console**, pick the active request, and send a message as `VENDOR`: *"We can do Thursday between 14:00 and 17:00."* 
5. Send a message as `TENANT`: *"Confirmed, I will be home."* 
6. Open **Tab 3: Communication Details** to inspect the chronological multi-agent audit trail and finalized `SCHEDULED` Work Order.

### Scenario 2: Ambiguity Handling (Human Review Flag)
1. Navigate to **Tab 1: New Intake**.
2. Submit an incomplete message: *"The ceiling is leaking."* (Missing building/unit identifiers).
3. Navigate to **Tab 2: Request Tracking**. The request is flagged with `needs_human_review = True` and remains in the `TRIAGED` state, preventing accidental dispatch.

---

## 🔮 Production Roadmap & Scaling

* **Direct Webhook Ingestion**: Add dedicated `/webhooks/whatsapp` (Twilio / Meta Cloud API) and `/webhooks/email` (Postmark / SendGrid Inbound Parse) endpoints to ingest requests directly from external communications into FastAPI.
* **Asynchronous Task Workers**: Offload heavy LLM extraction and vendor email dispatches to a distributed queue (Celery, ARQ, or Redis Streams) to prevent webhook timeouts.
* **Advanced Vendor Routing**: Upgrade vendor allocation from rule-based category matching to a multi-criteria scoring engine factoring in contractor availability calendars, SLAs, pricing tiers, and geographic proximity.
