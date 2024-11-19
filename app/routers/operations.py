from datetime import datetime, timedelta
import pandas as pd
import pytz
from fastapi import APIRouter, Query
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel
from app.schemas.operations import OperationOut, OperationsIn, DailyProductionOut, MachineSchedulesOut
from app.crud.operations import fetch_operations, insert_operations
from app.algorithms.scheduling import schedule_operations
from app.crud.component_quantities import fetch_component_quantities
from app.crud.leadtime import fetch_lead_times
from app.schemas.dynamic_scheduling import OperationOut1
from app.crud.dynamic_scheduling import fetch_raw_materials, fetch_machine_statuses

router = APIRouter()

@router.get("/fetch_operations/", response_model=List[OperationOut])
async def read_operations():
    df = fetch_operations()
    operations = df.to_dict(orient="records")
    return operations

@router.post("/post_operations/", response_model=List[Union[OperationOut, Dict[str, Any]]])
async def create_operations(operations: OperationsIn):
    op_out = insert_operations(operations.operations)
    return op_out

@router.get("/schedule/", response_model=List[OperationOut1])
async def schedule():
    df = fetch_operations()
    component_quantities = fetch_component_quantities()
    lead_times = fetch_lead_times()
    schedule_df, overall_end_time, overall_time, daily_production, component_status, removed_components = schedule_operations(df, component_quantities, lead_times)
    scheduled_operations = schedule_df.to_dict(orient="records")
    return scheduled_operations

# @router.get("/removed_components/", response_model=List[str])
# async def get_removed_components():
#     df = fetch_operations()
#     component_quantities = fetch_component_quantities()
#     lead_times = fetch_lead_times()
#     _, _, _, _, _, removed_components = schedule_operations(df, component_quantities, lead_times)
#     return removed_components


@router.get("/machine_schedules/", response_model=MachineSchedulesOut)
async def get_machine_schedules(
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None)
):
    # Fetch necessary data
    df = fetch_operations()
    component_quantities = fetch_component_quantities()
    lead_times = fetch_lead_times()  # Fetch the lead times for components

    # Call schedule_operations with the required lead_times argument
    schedule_df, overall_end_time, overall_time, daily_production, component_status, removed_components = schedule_operations(
        df, component_quantities, lead_times
    )

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
    component_quantities = fetch_component_quantities()
    lead_times = fetch_lead_times()  # Add this line to fetch lead times
    _, overall_end_time, overall_time, daily_production, _, _ = schedule_operations(df, component_quantities, lead_times)  # Update this line

    # Convert overall_end_time from Timestamp to string
    formatted_end_time = overall_end_time.strftime("%Y-%m-%d %H:%M") if isinstance(overall_end_time, datetime) else str(overall_end_time)

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


class ScheduleValidationItem(BaseModel):
    datetime: datetime
    machine: str
    component: str
    quantity: int


class ScheduleValidationRequest(BaseModel):
    items: List[ScheduleValidationItem]


class ValidationResult(BaseModel):
    datetime: datetime
    machine: str
    component: str
    requested_quantity: int
    scheduled_quantity: int
    status: str
    message: str


@router.post("/validate-schedule", response_model=List[ValidationResult])
async def validate_schedule(request: ScheduleValidationRequest):
    # Fetch necessary data
    operations_df = fetch_operations()
    component_quantities = fetch_component_quantities()
    lead_times = fetch_lead_times()

    # Generate schedule
    schedule_df, _, _, _, _ = schedule_operations(operations_df, component_quantities, lead_times)

    # Ensure all datetime columns in schedule_df are tz-aware
    for col in ['start_time', 'end_time']:
        if schedule_df[col].dt.tz is None:
            schedule_df[col] = schedule_df[col].dt.tz_localize(pytz.UTC)

    results = []

    for item in request.items:
        # Convert request datetime to pandas Timestamp
        request_datetime = pd.Timestamp(item.datetime)

        # If request_datetime is naive, assume it's in UTC
        if request_datetime.tz is None:
            request_datetime = request_datetime.tz_localize(pytz.UTC)

        # Filter schedule for the given datetime, machine, and component
        filtered_schedule = schedule_df[
            (schedule_df['start_time'] <= request_datetime) &
            (schedule_df['end_time'] > request_datetime) &
            (schedule_df['machine'] == item.machine) &
            (schedule_df['component'] == item.component)
            ]

        print(filtered_schedule)

        if filtered_schedule.empty:
            results.append(ValidationResult(
                datetime=item.datetime,
                machine=item.machine,
                component=item.component,
                requested_quantity=item.quantity,
                scheduled_quantity=0,
                status="Not OK",
                message="No matching schedule found for the given parameters"
            ))
        else:
            # Extract the scheduled quantity
            scheduled_quantity = filtered_schedule['quantity'].iloc[0]

            # Parse the quantity string (e.g., "1/5") to get the current quantity
            current_quantity = int(scheduled_quantity.split('/')[0])

            if current_quantity == item.quantity:
                results.append(ValidationResult(
                    datetime=item.datetime,
                    machine=item.machine,
                    component=item.component,
                    requested_quantity=item.quantity,
                    scheduled_quantity=current_quantity,
                    status="OK",
                    message="The requested quantity matches the schedule"
                ))
            else:
                results.append(ValidationResult(
                    datetime=item.datetime,
                    machine=item.machine,
                    component=item.component,
                    requested_quantity=item.quantity,
                    scheduled_quantity=current_quantity,
                    status="Not OK",
                    message=f"Quantity mismatch. Scheduled: {current_quantity}, Requested: {item.quantity}"
                ))

    return results