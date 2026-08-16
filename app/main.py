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
from app.seed import seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_data()
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
    needs_review = False
    if triage.unit_clue:
        stmt = select(Unit).where(Unit.unit_identifier.contains(triage.unit_clue))
        if building_id:
            stmt = stmt.where(Unit.building_id == building_id)
            unit = session.exec(stmt).first()
            if unit:
                unit_id = unit.id
        else:
            units = session.exec(stmt).all()
            if len(units) == 1:
                unit_id = units[0].id
                building_id = units[0].building_id
            elif len(units) > 1:
                needs_review = True # Ambiguous unit without a building

    if not building_id or not unit_id:
        needs_review = True

    new_request = MaintenanceRequest(
        raw_message=payload.message,
        channel=payload.channel,
        status=RequestStatus.TRIAGED,
        urgency=triage.urgency,
        category=triage.category,
        building_id=building_id,
        unit_id=unit_id,
        needs_human_review=needs_review,
        created_at=datetime.now(timezone.utc)
    )
    
    session.add(new_request)
    session.commit()
    session.refresh(new_request)
    
    dispatch_info = None
    if not needs_review:
        dispatch_res = dispatch_to_vendor(new_request.id, session)
        if "error" not in dispatch_res:
            session.refresh(new_request) # Refresh to get updated status
            dispatch_info = dispatch_res.get("message")
    
    return {
        "status": "success", 
        "maintenance_request": new_request, 
        "ai_reasoning": triage.reasoning,
        "auto_dispatched": dispatch_info is not None
    }

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

@app.get("/requests")
def list_requests(session: Session = Depends(get_session)):
    reqs = session.exec(
        select(MaintenanceRequest, Building, Unit)
        .join(Building, MaintenanceRequest.building_id == Building.id, isouter=True)
        .join(Unit, MaintenanceRequest.unit_id == Unit.id, isouter=True)
        .order_by(MaintenanceRequest.created_at.desc())
    ).all()
    
    result = []
    for req, bldg, unit in reqs:
        req_dict = req.model_dump()
        req_dict["building_name"] = bldg.name if bldg else None
        req_dict["unit_identifier"] = unit.unit_identifier if unit else None
        result.append(req_dict)
        
    return {"requests": result}

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
