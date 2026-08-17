from app.ai import ExtractedTriage
from app.models import UrgencyLevel, IssueCategory

def apply_overrides(triage: ExtractedTriage, raw_message: str) -> ExtractedTriage:
    text = raw_message.lower()
    original_urgency = triage.urgency
    original_category = triage.category
    
    # Override: Gas leak -> HAZARDOUS and EMERGENCY
    if "smell gas" in text or "gas leak" in text:
        triage.category = IssueCategory.HAZARDOUS
        triage.urgency = UrgencyLevel.EMERGENCY
        return triage # Return early as this is absolute highest priority
        
    # Override: Elderly or Trapped -> EMERGENCY
    if "elderly" in text or "trapped" in text:
        triage.urgency = UrgencyLevel.EMERGENCY
        
    # Override: Water and ceiling -> HIGH
    if "water" in text and "ceiling" in text:
        if triage.urgency == UrgencyLevel.ROUTINE:
            triage.urgency = UrgencyLevel.HIGH

    overrides_applied = []
    if triage.category != original_category:
        overrides_applied.append(f"category from {original_category.value} to {triage.category.value}")
    if triage.urgency != original_urgency:
        overrides_applied.append(f"urgency from {original_urgency.value} to {triage.urgency.value}")
        
    if overrides_applied:
        triage.reasoning += f"\n\n🚨 **[SYSTEM OVERRIDE]:** Rules engine automatically escalated " + " and ".join(overrides_applied) + " due to critical keyword detection."

    return triage
