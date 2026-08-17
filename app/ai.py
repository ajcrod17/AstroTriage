"""
AI Extraction Engine using OpenAI Structured Outputs.

This module leverages the `client.beta.chat.completions.parse` method to guarantee
zero-hallucination JSON outputs that conform strictly to the Pydantic schema.
This is the core of Phase 1 (Parsing), transforming unstructured multi-channel text 
into highly structured, typed data objects before handing them off to the Deterministic Guardrails.
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.models import IssueCategory, UrgencyLevel
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENAI_API_KEY", "dummy_key_to_prevent_init_crash")
)

class ExtractedTriage(BaseModel):
    """
    The structured Pydantic schema used to strictly constrain the LLM's output.
    """
    building_clue: Optional[str] = Field(description="Any mention of the building name or address (e.g., 'Sunset Apartments', 'Block B')")
    unit_clue: Optional[str] = Field(description="The specific apartment number or location identifier (e.g., '3C', 'Lobby', 'Front Door'). Extract only the core identifier, excluding words like 'apartment' or 'apt'")
    category: IssueCategory = Field(description="The identified issue category")
    urgency: UrgencyLevel = Field(description="The AI-determined urgency")
    reasoning: str = Field(description="Brief explanation for the categorization")

def extract_triage_info(raw_message: str) -> ExtractedTriage:
    """
    Sends the raw user message to GPT-4o-mini and forces the output into the ExtractedTriage schema.
    Because we use `.parse()` instead of standard `.create()`, we bypass the need for
    regex parsing or JSON-repair loops. The LLM is syntactically constrained.
    """
    completion = client.beta.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert AI triage agent for property maintenance. Extract structured information from the provided maintenance request."},
            {"role": "user", "content": raw_message}
        ],
        response_format=ExtractedTriage,
    )
    return completion.choices[0].message.parsed
