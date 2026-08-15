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
    building_clue: Optional[str] = Field(description="Any mention of the building name or address (e.g., 'Sunset Apartments', 'Block B')")
    unit_clue: Optional[str] = Field(description="Any mention of the apartment, floor, or unit (e.g., 'Apt 3C', '5th floor')")
    category: IssueCategory = Field(description="The identified issue category")
    urgency: UrgencyLevel = Field(description="The AI-determined urgency")
    reasoning: str = Field(description="Brief explanation for the categorization")

def extract_triage_info(raw_message: str) -> ExtractedTriage:
    completion = client.beta.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert AI triage agent for property maintenance. Extract structured information from the provided maintenance request."},
            {"role": "user", "content": raw_message}
        ],
        response_format=ExtractedTriage,
    )
    return completion.choices[0].message.parsed
