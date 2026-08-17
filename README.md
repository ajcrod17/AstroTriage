# AstroLab AI: AstroTriage Platform

AstroTriage is an intelligent, automated triage and dispatch platform designed specifically for property management operations. It intercepts incoming maintenance requests across omni-channel sources (Email, WhatsApp, Portal), extracts structured location and category data using AI, and autonomously dispatches vendors while managing end-to-end scheduling negotiations with tenants.

## Quick Start

AstroTriage is fully containerized for a frictionless setup. We provide a `Makefile` for absolute ease of use.

1. **Create an Environment File**: In the root of the repository, create a `.env` file containing your OpenRouter/OpenAI API key.
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

2. **Run the Application**:
   Simply run the following command to build and launch the environment in the background:
   ```bash
   make up
   ```
   *Note: The backend API will boot first, generate the local SQLite database in a persistent volume, and seed it with test data. The Streamlit dashboard relies on a healthcheck and will only boot once the API is fully ready to receive traffic.*

   **Other useful commands:**
   - `make logs`: Tail the live logs of both services.
   - `make clean`: Completely wipe the database state and shut down containers.
   - `make restart`: Wipe state and boot a fresh instance.
   - `make down`: Stop the containers.

   *(Fallback if `make` is not installed, or for native Windows PowerShell users):*
   ```bash
   # Start the environment
   docker compose up --build -d
   
   # Stop the environment
   docker compose down
   
   # Wipe the database (equivalent to make clean)
   docker run --rm -v "${PWD}/data:/data" python:3.11-slim bash -c "rm -rf /data/*"
   ```

3. **Access the Application**:
   - **Triage Dashboard (UI)**: [http://localhost:8501](http://localhost:8501)
   - **FastAPI Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## AI Execution Architecture

The core philosophy of AstroTriage is **"API-First with Deterministic Guardrails"**. 

While Large Language Models are exceptional at natural language parsing, relying purely on an LLM for routing mission-critical real-world operations (like dispatching emergency services) is a liability. 

AstroTriage solves this by combining the unstructured reasoning power of AI with the absolute certainty of a Deterministic Rule Engine:
1. **Extraction (AI Layer)**: The LLM reads the raw message and extracts structured fields (e.g., `IssueCategory`, `UrgencyLevel`, `building_clue`, `unit_clue`).
2. **Override Guardrails (Deterministic Layer)**: The extraction output is immediately passed through `triage_rules.py`. If a tenant types "I smell gas," the LLM might classify it as an HVAC issue, but the deterministic rule engine detects the hazard keyword, overrides the LLM, forces the category to `HAZARDOUS`, escalates the urgency to `EMERGENCY`, and routes it appropriately.
3. **Ambiguity Flags**: If the AI extraction fails to identify a precise unit, or if the unit is ambiguous (e.g., multiple "Apt 3C" across different buildings), the automated flow is immediately halted, and the request is flagged for human review.

This hybrid architecture maximizes operational efficiency while minimizing safety and routing risks.

### Cost vs. Latency Tradeoffs

AstroTriage utilizes **GPT-4o-mini** via OpenRouter for its core extraction and dialogue parsing. 

In property management triage, volume is exceptionally high, and latency expectations are near-instantaneous. A heavier model (like GPT-4-turbo or Claude 3.5 Sonnet) introduces unnecessary latency and exorbitant costs at scale. Because the LLM in AstroTriage is strictly constrained to *parsing and structuring* (rather than generating creative logic), `gpt-4o-mini` provides the perfect balance: rapid sub-second inference at a fraction of the cost, making the platform financially viable for high-volume enterprise deployment.

### Guardrails & Reliability

To completely eliminate output hallucination, AstroTriage enforces strict **OpenAI Structured Outputs** bound by **Pydantic Schemas**. 

- The LLM cannot return raw text; it is syntactically constrained to return JSON objects matching the predefined data models (`ExtractedTriage`, `VendorReply`, `TenantReply`).
- **Confidence Scoring & Fallbacks**: During automated negotiations, the LLM assigns a confidence score to its extraction (e.g., parsing "Thursday doesn't work, maybe Friday morning?" from a tenant). If the score falls below a threshold (`0.7`) or the message is overly complex, the AI gracefully yields control and escalates the request back to a human operator, entirely avoiding infinite negotiation loops or bad parsing.
- **Chronological Grounding**: To prevent "date hallucination" (where the LLM assumes a default date from its training cutoff), the system dynamically injects the server's exact current date and time into the system prompt, ensuring "tomorrow at 10 AM" is always resolved accurately.

---

## Testing Walkthrough

Once the containers are running, navigate to [http://localhost:8501](http://localhost:8501) and follow these steps to test the system:

### 1. The Happy Path (Zero-Touch Dispatch)
1. Go to **Tab 1: New Intake**.
2. Type: *"Hi, there is water pouring through the ceiling in apartment 3C."*
3. Click **Submit Request**.
4. Navigate to **Tab 2: Request Tracking**. You will see the request automatically parsed and instantly set to the `DISPATCHED` state. (Because the AI successfully identified the issue and unit, the system auto-dispatched the vendor without human intervention).
5. Navigate to **Tab 4: Simulation Console**.
6. Select your request under **2. Simulate Incoming Message**. Send a message as `VENDOR` (e.g., *"We can come by tomorrow morning at 10 AM"*).
7. Send a message as `TENANT` (e.g., *"Perfect, see you then"*).
8. Navigate to **Tab 3: Communication Details** to see the fully automated, chronological chat history and the finalized `SCHEDULED` Work Order.

### 2. The Edge Case (Human Review Flag)
1. Go back to **Tab 1: New Intake**.
2. Type an ambiguous message: *"The ceiling is leaking."* (No unit or building mentioned).
3. Click **Submit Request**.
4. Navigate to **Tab 2: Request Tracking**. The request will be highlighted in yellow with the `needs_human_review` flag activated, and it will remain in the `TRIAGED` state, preventing a faulty dispatch.
