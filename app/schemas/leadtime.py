from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List


class LeadTimeIn(BaseModel):
    component: str
    due_date: datetime

class LeadTimeOut(BaseModel):
    component: str
    due_date: datetime

class ComponentStatusOut(BaseModel):
    component: str
    scheduled_end_time: datetime
    lead_time: Optional[datetime]
    on_time: bool
    completed_quantity: int
    total_quantity: int
    lead_time_provided: bool


class ComponentStatus(BaseModel):
    component: str
    scheduled_end_time: datetime
    lead_time: Optional[datetime]
    on_time: bool
    completed_quantity: int
    total_quantity: int
    lead_time_provided: bool
    delay: Optional[timedelta]

class ComponentStatusResponse(BaseModel):
    early_complete: List[ComponentStatus]
    on_time_complete: List[ComponentStatus]
    delayed_complete: List[ComponentStatus]

class LeadTimeResponse(BaseModel):
    component: str
    due_date: datetime
