from pydantic import BaseModel, Field
from typing import Optional
from app.ai import client
from datetime import datetime

class VendorReply(BaseModel):
    proposed_slot: Optional[str] = Field(description="The date/time slot proposed. Format as a clean, highly human-readable string using the 24-hour time format (e.g. 'Thursday, August 20th between 14:00 and 17:00'). Do NOT use ISO dates.")
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0 in parsing this slot.")
    needs_human_escalation: bool = Field(description="True if the message is ambiguous or requires human intervention.")

class TenantReply(BaseModel):
    agreed: bool = Field(description="True if the tenant agreed to the proposed slot.")
    alternative_slot: Optional[str] = Field(description="If they disagreed, the alternative slot proposed. Format as a clean, highly human-readable string using the 24-hour time format (e.g. 'Friday at 09:00'). Do NOT use ISO dates.")
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0 in parsing this response.")
    needs_human_escalation: bool = Field(description="True if the message is ambiguous or requires human intervention.")

def parse_vendor_reply(raw_message: str) -> VendorReply:
    now_str = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    completion = client.beta.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are parsing a vendor's reply to a maintenance dispatch. Extract their proposed time slot. Today's date and time is {now_str}."},
            {"role": "user", "content": raw_message}
        ],
        response_format=VendorReply,
    )
    return completion.choices[0].message.parsed

def parse_tenant_reply(raw_message: str) -> TenantReply:
    now_str = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    completion = client.beta.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are parsing a tenant's reply to a proposed maintenance time slot. Determine if they agreed or proposed an alternative. Today's date and time is {now_str}."},
            {"role": "user", "content": raw_message}
        ],
        response_format=TenantReply,
    )
    return completion.choices[0].message.parsed
