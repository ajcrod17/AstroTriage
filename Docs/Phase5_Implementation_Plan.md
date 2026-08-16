# Phase 5 Implementation Plan: Containerization & Documentation

This document outlines the final steps to prepare AstroTriage for deployment and evaluation.

## 1. Containerization (Docker)
We will use Docker Compose to orchestrate both the FastAPI backend and the Streamlit frontend. This ensures a consistent environment for the evaluators.

### Configuration
We will use a **single `Dockerfile`** for both services since they share the same `requirements.txt` and Python environment. The `docker-compose.yml` will define two separate services (`api` and `dashboard`) that build from this single image but run different startup commands.

### Files to Create
1. **`Dockerfile`**:
   - Base image: `python:3.11-slim`
   - Copy `requirements.txt` and install dependencies.
   - Copy the `app/` directory.
   - Expose ports `8000` (FastAPI) and `8501` (Streamlit).

2. **`docker-compose.yml`**:
   - **`api` service**:
     - Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
     - Ports: `8000:8000`
     - Environment Variables: `OPENAI_API_KEY`
   - **`dashboard` service**:
     - Command: `streamlit run app/dashboard.py --server.address 0.0.0.0`
     - Ports: `8501:8501`
     - Environment Variables: `API_URL=http://api:8000`

3. **`.env`** (ignored in git):
   - We will instruct the user/evaluator to create a `.env` file containing their `OPENAI_API_KEY` so it's not hardcoded in the repo.

## 2. Documentation
A comprehensive `README.md` is critical for a take-home assessment.

### Outline for `README.md`
- **Project Overview**: High-level summary of AstroTriage's purpose and value proposition.
- **Architecture**: Explanation of the "API-first" design, the deterministic Rule Engine guardrails over AI extraction, and the State Machine for negotiation.
- **Setup & Execution**: 
  - Clear instructions on how to add the `OPENAI_API_KEY`.
  - Instructions for running via Docker (`docker-compose up`).
  - Instructions for running locally via `venv` (fallback).
- **Testing Walkthrough**: Step-by-step guide for the evaluator to test the "Happy Path" (auto-dispatch) and the "Edge Cases" (human review flags).

## 3. Verification
- Stop all local instances.
- Run `docker-compose up --build`.
- Verify the FastAPI server responds at `localhost:8000`.
- Verify the Streamlit dashboard loads at `localhost:8501`.
- Verify internal networking (Streamlit can talk to FastAPI).
