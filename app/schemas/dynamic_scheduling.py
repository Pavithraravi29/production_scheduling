from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# Raw Material Schemas
class RawMaterialBase(BaseModel):
    name: str
    available: bool
    available_from: Optional[datetime] = None

class RawMaterialIn(RawMaterialBase):
    pass

class RawMaterialOut(RawMaterialBase):
    id: int

    class Config:
        orm_mode = True

# Machine Status Schemas
class MachineStatusBase(BaseModel):
    machine: str
    status: str
    available_from: Optional[datetime] = None

class MachineStatusIn(MachineStatusBase):
    pass

class MachineStatusOut(MachineStatusBase):
    id: int

    class Config:
        orm_mode = True

# Scheduling Output Schemas
class DailyProductionOut(BaseModel):
    overall_end_time: str
    overall_time: str
    daily_production: Dict[str, Dict[datetime, int]]
    total_components: int

class MachineSchedulesOut(BaseModel):
    machine_schedules: Dict[str, List[Dict[str, str]]]

# Component Status Schema
class ComponentStatus(BaseModel):
    scheduled_end_time: datetime
    lead_time: Optional[datetime]
    on_time: bool
    completed_quantity: int
    total_quantity: int
    lead_time_provided: bool

# Component Status Response Schema
class ComponentStatusResponse(BaseModel):
    early_complete: List[ComponentStatus]
    on_time_complete: List[ComponentStatus]
    delayed_complete: List[ComponentStatus]

class OperationOut1(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    start_time: datetime
    end_time: datetime
    quantity: str

