from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from typing import List, Optional
from app.schemas.operations import OperationOut, OperationsIn, OperationOut1, DailyProductionOut, MachineSchedulesOut
from app.crud.operations import fetch_operations, insert_operations
from app.algorithms.scheduling import schedule_operations
from app.crud.component_quantities import fetch_component_quantities


router = APIRouter()

@router.get("/fetch_operations/", response_model=List[OperationOut])
async def read_operations():
    df = fetch_operations()
    operations = df.to_dict(orient="records")
    return operations

@router.post("/post_operations/", response_model=List[OperationOut])
async def create_operations(operations: OperationsIn):
    op_out = insert_operations(operations.operations)
    return op_out

@router.get("/schedule/", response_model=List[OperationOut1])
async def schedule():
    df = fetch_operations()
    component_quantities = fetch_component_quantities()
    schedule_df, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)
    scheduled_operations = schedule_df.to_dict(orient="records")
    return scheduled_operations

@router.get("/machine_schedules/", response_model=MachineSchedulesOut)
async def get_machine_schedules(
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None)
):
    df = fetch_operations()
    component_quantities = fetch_component_quantities()

    schedule_df, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)

    # Ensure that start_date and end_date are handled as inclusive
    if start_date:
        schedule_df = schedule_df[schedule_df['start_time'] >= start_date]
    if end_date:
        # Ensure end_date is inclusive
        end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
        schedule_df = schedule_df[schedule_df['end_time'] <= end_date]

    # Create machine schedule dictionary
    machine_schedules = {}
    for _, row in schedule_df.iterrows():
        machine = row['machine']
        if machine not in machine_schedules:
            machine_schedules[machine] = []
        machine_schedules[machine].append({
            "component": row['component'],
            "operation": row['description'],
            "start_time": row['start_time'].isoformat(),
            "end_time": row['end_time'].isoformat(),
            "duration_minutes": int((row['end_time'] - row['start_time']).total_seconds() / 60)
        })

    return {"machine_schedules": machine_schedules}

@router.get("/daily_production/", response_model=DailyProductionOut)
async def daily_production():
    df = fetch_operations()
    # component_quantities = {"Component1": 10, "Component2": 10, "Component3": 10, "Component 4": 10, "Component 5": 10,"Component 6": 10, "Component 7": 10, "Component 8": 10}  # Define the quantities here
    component_quantities = fetch_component_quantities()
    _, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)

    # Convert overall_end_time from Timestamp to string
    formatted_end_time = overall_end_time.strftime("%Y-%m-%d %H:%M") if isinstance(overall_end_time, datetime) else str(
        overall_end_time)

    # Convert overall_time from minutes to d h m format
    delta = timedelta(minutes=overall_time)
    days, seconds = delta.days, delta.seconds
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    formatted_overall_time = f"{days}d {hours:02d}h {minutes:02d}m"

    # Calculate the total number of unique components
    total_components = len(component_quantities)  # Count unique components

    # Return the response with the total component count
    return {
        "overall_end_time": formatted_end_time,
        "overall_time": formatted_overall_time,
        "daily_production": daily_production,
        "total_components": total_components
    }