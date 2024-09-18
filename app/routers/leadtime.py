from datetime import datetime
from typing import List
from fastapi import APIRouter
from numpy import select
from pony.orm import db_session

from app.algorithms.scheduling import schedule_operations
from app.crud.component_quantities import fetch_component_quantities
from app.crud.leadtime import fetch_lead_times, insert_lead_times
from app.crud.operations import fetch_operations
from app.schemas.leadtime import ComponentStatusOut, LeadTimeOut, LeadTimeIn, ComponentStatusResponse, ComponentStatus, \
    LeadTimeResponse
from app.database.models import LeadTime

router = APIRouter()

@router.get("/component_status/", response_model=ComponentStatusResponse)
async def get_component_status():
    df = fetch_operations()
    component_quantities = fetch_component_quantities()
    lead_times = fetch_lead_times()
    _, _, _, _, component_status = schedule_operations(df, component_quantities, lead_times)

    early_complete = []
    on_time_complete = []
    delayed_complete = []

    for comp, status in component_status.items():
        component = ComponentStatus(
            component=comp,
            scheduled_end_time=status['scheduled_end_time'],
            lead_time=status['lead_time'],
            on_time=status['on_time'],
            completed_quantity=status['completed_quantity'],
            total_quantity=status['total_quantity'],
            lead_time_provided=status['lead_time'] is not None,
            delay=None
        )

        if status['lead_time_provided']:
            if status['scheduled_end_time'] < status['lead_time']:
                early_complete.append(component)
            elif status['scheduled_end_time'] == status['lead_time']:
                on_time_complete.append(component)
            else:
                component.delay = status['scheduled_end_time'] - status['lead_time']
                delayed_complete.append(component)
        else:
            on_time_complete.append(component)

    return ComponentStatusResponse(
        early_complete=early_complete,
        on_time_complete=on_time_complete,
        delayed_complete=delayed_complete
    )

@router.post("/insert_lead_times/", response_model=List[LeadTimeOut])
async def create_lead_times(lead_times: List[LeadTimeIn]):
    return insert_lead_times(lead_times)


@router.get("/lead-time-table", response_model=List[LeadTimeResponse])
@db_session
def get_lead_times():
    lead_times = LeadTime.select()

    result = []
    for lt in lead_times:
        result.append(LeadTimeResponse(
            component=lt.component,
            due_date=lt.due_date
        ))

    return result



