from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship

class RequestStatus(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    DISPATCHED = "DISPATCHED"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"

class UrgencyLevel(str, Enum):
    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"

class BuildingType(str, Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    GOVERNMENT = "GOVERNMENT"

class IssueCategory(str, Enum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    ELEVATOR_HVAC = "ELEVATOR_HVAC"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    HAZARDOUS = "HAZARDOUS"

class Building(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: BuildingType
    address: str

    units: List["Unit"] = Relationship(back_populates="building")
    maintenance_requests: List["MaintenanceRequest"] = Relationship(back_populates="building")

class Unit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    building_id: int = Field(foreign_key="building.id")
    unit_identifier: str

    building: Optional[Building] = Relationship(back_populates="units")
    maintenance_requests: List["MaintenanceRequest"] = Relationship(back_populates="unit")

class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: IssueCategory
    email: str
    phone: str

    work_orders: List["WorkOrder"] = Relationship(back_populates="vendor")

class MaintenanceRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_message: str
    channel: str
    status: RequestStatus = Field(default=RequestStatus.NEW)
    urgency: Optional[UrgencyLevel] = Field(default=None)
    category: Optional[IssueCategory] = Field(default=None)
    building_id: Optional[int] = Field(default=None, foreign_key="building.id")
    unit_id: Optional[int] = Field(default=None, foreign_key="unit.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    building: Optional[Building] = Relationship(back_populates="maintenance_requests")
    unit: Optional[Unit] = Relationship(back_populates="maintenance_requests")
    work_orders: List["WorkOrder"] = Relationship(back_populates="request")
    communications: List["CommunicationLog"] = Relationship(back_populates="request")

class WorkOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="maintenancerequest.id")
    vendor_id: Optional[int] = Field(default=None, foreign_key="vendor.id")
    scheduled_slot: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    request: Optional[MaintenanceRequest] = Relationship(back_populates="work_orders")
    vendor: Optional[Vendor] = Relationship(back_populates="work_orders")

class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="maintenancerequest.id")
    sender: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    request: Optional[MaintenanceRequest] = Relationship(back_populates="communications")
