"""
Multi-Agent Dialogue & State Machine.

This module handles the core workflow logic post-triage. It orchestrates the 
dispatching of vendors and the automated negotiation loops between the System, Vendor, and Tenant.
It strictly enforces boundaries (like MAX_NEGOTIATIONS) to prevent infinite AI loops.
"""
from sqlmodel import Session, select
from app.models import MaintenanceRequest, RequestStatus, Vendor, CommunicationLog, WorkOrder
from app.ai_dialogue import parse_vendor_reply, parse_tenant_reply

MAX_NEGOTIATIONS = 3

def log_communication(request_id: int, sender: str, message: str, session: Session):
    """Helper to persist a message to the CommunicationLog audit trail."""
    log = CommunicationLog(request_id=request_id, sender=sender, message=message)
    session.add(log)
    return log

def dispatch_to_vendor(request_id: int, session: Session):
    """
    Attempts to auto-dispatch a TRIAGED request to the appropriate domain vendor.
    If the request requires human review (e.g., due to an ambiguous unit), it aborts 
    and leaves it in the queue for a human operator.
    """
    request = session.get(MaintenanceRequest, request_id)
    if not request or request.status != RequestStatus.TRIAGED:
        return {"error": "Invalid request or status"}
        
    if request.needs_human_review or not request.building_id or not request.unit_id:
        return {"error": "Cannot dispatch automatically. Missing building/unit or flagged for human review."}
    
    # Pick first matching vendor
    stmt = select(Vendor).where(Vendor.category == request.category)
    vendor = session.exec(stmt).first()
    
    if not vendor:
        request.needs_human_review = True
        session.commit()
        return {"error": "No vendor found"}
        
    b_str = request.building.name if request.building else f"Building {request.building_id}" if request.building_id else "the building"
    u_str = request.unit.unit_identifier if request.unit else f"Unit {request.unit_id}" if request.unit_id else "the unit"
    cat_str = request.category.value if request.category else "maintenance"
    
    msg = f"Dear {vendor.name}, we have a {cat_str} issue at {b_str}, {u_str}. Please confirm your earliest available slot for an inspection."
    log_communication(request_id, "SYSTEM->VENDOR", msg, session)
    
    request.status = RequestStatus.DISPATCHED
    session.commit()
    return {"status": "DISPATCHED", "message": msg}

def handle_incoming_message(request_id: int, sender: str, raw_message: str, session: Session):
    """
    The main multi-agent communication loop. 
    It receives a raw string from either VENDOR or TENANT, uses the AI Dialogue Parser 
    to extract intent, and progresses the state machine (e.g. DISPATCHED -> SCHEDULED).
    It implements a hard limit (MAX_NEGOTIATIONS) circuit breaker.
    """
    request = session.get(MaintenanceRequest, request_id)
    if not request:
        return {"error": "Request not found"}
        
    if request.needs_human_review:
        return {"error": "Request requires human review, automated flow halted"}
        
    log_communication(request_id, sender, raw_message, session)
    
    if request.negotiation_iterations >= MAX_NEGOTIATIONS:
        request.needs_human_review = True
        session.commit()
        return {"error": "Max negotiations reached. Escalated to human."}
        
    if sender == "VENDOR":
        parsed = parse_vendor_reply(raw_message)
        if parsed.needs_human_escalation or parsed.confidence_score < 0.7:
            request.needs_human_review = True
            session.commit()
            return {"status": "ESCALATED"}
            
        if parsed.proposed_slot:
            cat_str = request.category.value if request.category else "maintenance"
            msg = f"Dear Resident, we have scheduled a {cat_str} inspection for {parsed.proposed_slot}. Please confirm if this works for you."
            log_communication(request_id, "SYSTEM->TENANT", msg, session)
            session.commit()
            return {"status": "PROPOSED_TO_TENANT", "message": msg}
            
    elif sender == "TENANT":
        parsed = parse_tenant_reply(raw_message)
        if parsed.needs_human_escalation or parsed.confidence_score < 0.7:
            request.needs_human_review = True
            session.commit()
            return {"status": "ESCALATED"}
            
        if parsed.agreed:
            request.status = RequestStatus.SCHEDULED
            stmt = select(Vendor).where(Vendor.category == request.category)
            vendor = session.exec(stmt).first()
            
            wo = WorkOrder(request_id=request.id, vendor_id=vendor.id if vendor else None, scheduled_slot="Agreed slot")
            session.add(wo)
            
            msg = "The slot is confirmed. We will follow up once the work is complete."
            log_communication(request_id, "SYSTEM->TENANT", msg, session)
            log_communication(request_id, "SYSTEM->VENDOR", "The tenant has confirmed the slot.", session)
            
            session.commit()
            return {"status": "SCHEDULED"}
        else:
            request.negotiation_iterations += 1
            msg = f"The tenant proposed an alternative: {parsed.alternative_slot}. Can you accommodate this?"
            log_communication(request_id, "SYSTEM->VENDOR", msg, session)
            session.commit()
            return {"status": "RE_NEGOTIATING", "message": msg}
