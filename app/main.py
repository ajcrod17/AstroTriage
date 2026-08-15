from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import create_db_and_tables, get_session
from app.models import MaintenanceRequest, RequestStatus, Building, Unit, CommunicationLog, WorkOrder
from app.ai import extract_triage_info
from app.triage_rules import apply_overrides
from app.state_machine import dispatch_to_vendor, handle_incoming_message

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="AstroTriage API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

class IntakePayload(BaseModel):
    message: str
    channel: str

@app.post("/intake")
def intake_request(payload: IntakePayload, session: Session = Depends(get_session)):
    extracted = extract_triage_info(payload.message)
    triage = apply_overrides(extracted, payload.message)
    
    building_id = None
    if triage.building_clue:
        stmt = select(Building).where(Building.name.contains(triage.building_clue))
        building = session.exec(stmt).first()
        if not building:
            stmt = select(Building).where(Building.address.contains(triage.building_clue))
            building = session.exec(stmt).first()
        if building:
            building_id = building.id
            
    unit_id = None
    if building_id and triage.unit_clue:
        stmt = select(Unit).where(Unit.building_id == building_id).where(Unit.unit_identifier.contains(triage.unit_clue))
        unit = session.exec(stmt).first()
        if unit:
            unit_id = unit.id

    new_request = MaintenanceRequest(
        raw_message=payload.message,
        channel=payload.channel,
        status=RequestStatus.TRIAGED,
        urgency=triage.urgency,
        category=triage.category,
        building_id=building_id,
        unit_id=unit_id,
        created_at=datetime.now(timezone.utc)
    )
    
    session.add(new_request)
    session.commit()
    session.refresh(new_request)
    
    return {"status": "success", "maintenance_request": new_request, "ai_reasoning": triage.reasoning}

@app.post("/simulate/dispatch/{request_id}")
def simulate_dispatch(request_id: int, session: Session = Depends(get_session)):
    res = dispatch_to_vendor(request_id, session)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

class MessagePayload(BaseModel):
    request_id: int
    sender: str
    message: str

@app.post("/simulate/message")
def simulate_message(payload: MessagePayload, session: Session = Depends(get_session)):
    res = handle_incoming_message(payload.request_id, payload.sender, payload.message, session)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.get("/requests/{request_id}")
def get_request(request_id: int, session: Session = Depends(get_session)):
    request = session.get(MaintenanceRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Not found")
        
    logs = session.exec(select(CommunicationLog).where(CommunicationLog.request_id == request_id).order_by(CommunicationLog.timestamp)).all()
    work_orders = session.exec(select(WorkOrder).where(WorkOrder.request_id == request_id)).all()
    
    return {
        "request": request,
        "logs": logs,
        "work_orders": work_orders
    }
