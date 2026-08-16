# Phase 4: Streamlit Dashboard UI - Walkthrough

The Streamlit Dashboard has been fully implemented, providing a beautiful and functional UI for the operations team.

## What Was Accomplished
1. **Premium Aesthetics via Config**:
   - Created `.streamlit/config.toml` configuring a modern dark mode, using AstroLab AI's indigo (`#4f46e5`) as the primary brand color.
   - Kept the CSS bounded to configurations, avoiding hacky HTML injections.
2. **API First & Error Handling**:
   - Upgraded `app/main.py` by adding the `GET /requests` endpoint to list all items.
   - Built `app/dashboard.py` interacting with the backend strictly via HTTP calls using the `requests` library.
   - Wrapped API calls in `try/except` blocks to display graceful `st.error()` messages instead of python tracebacks if the FastAPI server is down.
3. **The Four Tabs**:
   - **Tab 1: New Intake**: A form to submit requests that automatically triggers `st.rerun()` upon successful intake, pulling the fresh state.
   - **Tab 2: Request Tracking**: A dataframe rendering all requests, with a customized function mapping urgency levels to distinct colors (e.g. Red for Emergency).
   - **Tab 3: Communication Details**: Fetches details for a specific request ID and renders the `CommunicationLog` as an attractive chat interface showing the System, Vendor, and Tenant thread.
   - **Tab 4: Simulation Console**: Fully functional UI to trigger `dispatch` and simulate `Vendor/Tenant` messages, which also triggers `st.rerun()` so you instantly see the negotiation unfold.

## How to Verify
To test the dashboard, you will need two terminal windows running side-by-side.

**Terminal 1 (Backend API):**
```bash
venv/bin/uvicorn app.main:app
```

**Terminal 2 (Streamlit UI):**
```bash
# Remember to export your API key so AI extraction works on new intakes/simulations!
export OPENAI_API_KEY="sk-or-v1-..."

venv/bin/streamlit run app/dashboard.py
```
Open the provided `localhost` link in your browser and explore the tabs!
