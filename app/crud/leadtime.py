from datetime import datetime
from typing import List, Dict
from app.database.models import LeadTime
from app.schemas.leadtime import LeadTimeIn, LeadTimeOut
from pony.orm import db_session, select, commit

@db_session
def fetch_lead_times() -> Dict[str, datetime]:
    lead_times = select(lt for lt in LeadTime)[:]
    return {lt.component: lt.due_date for lt in lead_times}

@db_session
def insert_lead_times(lead_times: List[LeadTimeIn]) -> List[LeadTimeOut]:
    results = []
    for lt in lead_times:
        component = lt.component
        due_date = lt.due_date
        existing = LeadTime.get(component=component)
        if existing:
            existing.due_date = due_date
        else:
            LeadTime(component=component, due_date=due_date)
        results.append(LeadTimeOut(component=component, due_date=due_date))
    commit()
    return results