# Phase 4: Streamlit Dashboard UI

This plan outlines the creation of the user-facing Streamlit dashboard for the operations team to intake, track, manage maintenance requests and communications, and simulate interactions.

## Design Decisions
1. **Data Access (API vs DB)**: Strictly adhere to the "API First" approach. The Streamlit app communicates exclusively via HTTP calls using the `requests` library.
2. **Simulation Tools**: A dedicated "Simulation Console" tab will be built to trigger vendor/tenant replies directly from the UI.
3. **Aesthetics**: Custom CSS is strictly bounded. We use `.streamlit/config.toml` to enforce a modern dark mode, clean typography, and a brand-aligned primary color (AstroLab AI's Indigo #4f46e5), avoiding extensive and hacky `st.markdown` injections.

## Refinements & Guardrails
1. **Expanding the API Scope**: Add `GET /requests` to fetch all requests for the tracking table. The existing `GET /requests/{request_id}` already fetches the specific work order and the timeline of the `CommunicationLog`.
2. **Handling State and Auto-Refresh**: Use `st.rerun()` immediately after a successful POST request (e.g. creating a new intake or triggering a simulation) so the dashboard instantly reflects the new data. A "Refresh" button will also be provided.
3. **Error Handling in the UI**: Wrap `requests.get()` and `requests.post()` calls in `try/except` blocks. Use `st.error()` or `st.toast()` to gracefully inform the user if the backend connection fails or times out.

## Proposed Changes

### Dependencies
#### [MODIFY] `requirements.txt`
- Add `streamlit` and `requests`.

### Configuration
#### [NEW] `.streamlit/config.toml`
- Add theme overrides for `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, and `textColor` to achieve a modern dark mode.

### API Endpoints
#### [MODIFY] `app/main.py`
- Add `GET /requests` endpoint to list all maintenance requests for the dashboard tracking table.

### Dashboard Application
#### [NEW] `app/dashboard.py`
The main Streamlit application containing the UI.
- **Tab 1: New Intake**: Form to submit a new raw message and channel.
- **Tab 2: Request Tracking**: High-level data table of all `MaintenanceRequests` with color-coded urgencies.
- **Tab 3: Communication & Details**: Renders the `CommunicationLog` as a chat timeline.
- **Tab 4: Simulation Console**: Trigger `POST /simulate/dispatch` and `POST /simulate/message` endpoints.
