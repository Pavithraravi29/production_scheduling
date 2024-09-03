from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

class OperationIn(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    time: float

class OperationsIn(BaseModel):
    operations: List[OperationIn]

class OperationOut(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    start_time: datetime
    end_time: datetime

class OperationOut1(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    start_time: datetime
    end_time: datetime
    quantity: str

class DailyProductionOut(BaseModel):
    overall_end_time: str
    overall_time: str
    daily_production: Dict[str, Any]
    total_components: int

class MachineScheduleOut(BaseModel):
    component: str
    operation: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int

class MachineSchedulesOut(BaseModel):
    machine_schedules: Dict[str, List[MachineScheduleOut]]