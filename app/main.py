from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime, timezone
from app.database import create_db_and_tables, get_session
from app.models import MaintenanceRequest, RequestStatus, Building, Unit
from app.ai import extract_triage_info
from app.triage_rules import apply_overrides

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
    # 1. AI Extraction
    extracted = extract_triage_info(payload.message)
    
    # 2. Rule Engine Overrides
    triage = apply_overrides(extracted, payload.message)
    
    # 3. Resolve Building and Unit
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

    # 4. Create MaintenanceRequest
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
    
    return {
        "status": "success",
        "maintenance_request": new_request,
        "ai_reasoning": triage.reasoning
    }
