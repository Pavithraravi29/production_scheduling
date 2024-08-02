import heapq
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, date
from typing import List, Dict

from fastapi.middleware.cors import CORSMiddleware

from app.database.config2 import configure_database
from app.database.models2 import Operation, ComponentQuantity
from pony.orm import db_session, select, commit
import pandas as pd

app = FastAPI()


# CORS Configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_database()

# Pydantic models
class OperationIn(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    time: float
    # quantity: int

# Define a model to handle multiple operations
class OperationsIn(BaseModel):
    operations: List[OperationIn]

class OperationOut(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    start_time: datetime
    end_time: datetime
    # quantity: str

class OperationOut1(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    start_time: datetime
    end_time: datetime
    quantity: str

class DailyProductionOut(BaseModel):
    overall_end_time: datetime
    overall_time: float
    daily_production: Dict[str, Dict[date, int]]

class ComponentQuantityIn(BaseModel):
    component: str
    quantity: int

class ComponentQuantityOut(BaseModel):
    component: str
    quantity: int


# Function to fetch operations from the database
@db_session
def fetch_operations():
    operations = select(op for op in Operation).order_by(lambda op: op.id)[:]  # Order by 'id'

    operations_list = [
        (op.id, op.component, op.description, op.type, op.machine, op.time, op.start_time, op.end_time) for op in
        operations
    ]

    df = pd.DataFrame(
        operations_list,
        columns=["id", "component", "description", "type", "machine", "time", "start_time", "end_time"],
    )
    return df


# Function to insert a new operation into the database
@db_session
def insert_operations(operations: List[OperationIn]) -> List[OperationOut]:
    now = datetime.now()
    results = []
    for operation in operations:
        end_time = now + timedelta(minutes=operation.time)
        new_operation = Operation(
            component=operation.component,
            description=operation.description,
            type=operation.type,
            machine=operation.machine,
            time=operation.time,
            start_time=now,
            end_time=end_time,
            # quantity=operation.quantity,
        )
        results.append(OperationOut(
            component=new_operation.component,
            description=new_operation.description,
            type=new_operation.type,
            machine=new_operation.machine,
            start_time=new_operation.start_time,
            end_time=new_operation.end_time,
            # quantity=new_operation.quantity,
        ))
    commit()
    return results

# Fetch quantities from the database
@db_session
def fetch_component_quantities() -> Dict[str, int]:
    quantities = select(cq for cq in ComponentQuantity)[:]
    return {cq.component: cq.quantity for cq in quantities}

# Insert or update component quantities
@db_session
def insert_component_quantities(quantities: List[ComponentQuantityIn]) -> List[ComponentQuantityOut]:
    results = []
    for qty in quantities:
        component = qty.component
        quantity = qty.quantity

        existing = ComponentQuantity.get(component=component)
        if existing:
            existing.quantity = quantity
        else:
            ComponentQuantity(component=component, quantity=quantity)

        results.append(ComponentQuantityOut(component=component, quantity=quantity))

    commit()
    return results

#
# def schedule_operations(df: pd.DataFrame, component_quantities: dict) -> (pd.DataFrame, datetime, float, dict):
#     if df.empty:
#         return pd.DataFrame(), datetime.now(), 0.0, {}
#
#     df_sorted = df.sort_values(by=['component', 'id'])
#
#     # Get the start date from the database
#     start_date = df_sorted['start_time'].min()
#     if pd.isnull(start_date):
#         start_date = datetime.now()
#
#     schedule = []
#     machine_end_times = {machine: start_date for machine in df_sorted["machine"].unique()}
#     current_time = start_date
#     daily_production = {}
#     remaining_quantities = component_quantities.copy()
#
#     while any(remaining_quantities.values()):
#         day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
#         day_end = day_start + timedelta(days=1)
#
#         for component, quantity in list(remaining_quantities.items()):
#             if quantity <= 0:
#                 continue
#
#             component_ops = df_sorted[df_sorted["component"] == component]
#             units_today = 0
#
#             while remaining_quantities[component] > 0:
#                 unit_start_time = max(machine_end_times.values())
#                 if unit_start_time >= day_end:
#                     break
#
#                 unit_completed = True
#                 unit_operations = []
#                 for _, row in component_ops.iterrows():
#                     description, op_type, machine, time = row[["description", "type", "machine", "time"]]
#
#                     start_time = max(unit_start_time, machine_end_times[machine])
#                     end_time = start_time + timedelta(minutes=time)
#
#                     if end_time > day_end:
#                         unit_completed = False
#                         break
#
#                     unit_operations.append([
#                         component,
#                         description,
#                         op_type,
#                         machine,
#                         start_time,
#                         end_time,
#                         f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
#                     ])
#
#                     machine_end_times[machine] = end_time
#                     unit_start_time = end_time
#
#                 if unit_completed:
#                     schedule.extend(unit_operations)
#                     units_today += 1
#                     remaining_quantities[component] -= 1
#                 else:
#                     break
#
#             if component not in daily_production:
#                 daily_production[component] = {}
#             if units_today > 0:
#                 daily_production[component][current_time.date()] = units_today
#
#         current_time = day_end
#
#     schedule_df = pd.DataFrame(
#         schedule,
#         columns=[
#             "component",
#             "description",
#             "type",
#             "machine",
#             "start_time",
#             "end_time",
#             "quantity"
#         ],
#     )
#
#     overall_end_time = max(schedule_df['end_time'])
#     overall_time = (overall_end_time - start_date).total_seconds() / 60
#
#     return schedule_df, overall_end_time, overall_time, daily_production




def schedule_operations(df: pd.DataFrame, component_quantities: dict) -> (pd.DataFrame, datetime, float, dict):
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0, {}

    df_sorted = df.sort_values(by=['component', 'id'])
    start_date = df_sorted['start_time'].min()
    if pd.isnull(start_date):
        start_date = datetime.now()

    # Adjust start_date to the next 9 AM if it's not within shift hours
    if start_date.hour < 9 or start_date.hour >= 17:
        start_date = (start_date + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    schedule = []
    machine_end_times = {machine: start_date for machine in df_sorted["machine"].unique()}
    current_time = start_date
    daily_production = {}
    remaining_quantities = component_quantities.copy()

    def schedule_component(component, start_time):
        component_ops = df_sorted[df_sorted["component"] == component]
        unit_operations = []
        end_time = start_time  # Initialize end_time

        for _, row in component_ops.iterrows():
            description, op_type, machine, time = row[["description", "type", "machine", "time"]]
            start_time = max(start_time, machine_end_times[machine])

            # Adjust start_time to next shift if it's outside shift hours
            if start_time.hour < 9 or start_time.hour >= 17:
                start_time = (start_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            end_time = start_time + timedelta(minutes=time)

            # If operation ends after shift, split it
            if end_time.hour >= 17:
                remaining_time = (end_time - start_time).total_seconds() / 60
                today_end = start_time.replace(hour=17, minute=0, second=0, microsecond=0)
                today_duration = (today_end - start_time).total_seconds() / 60

                # Add operation for today
                unit_operations.append([
                    component, description, op_type, machine, start_time, today_end,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = today_end

                # Schedule remaining time for next day
                next_day_start = (today_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                next_day_end = next_day_start + timedelta(minutes=remaining_time - today_duration)
                unit_operations.append([
                    component, description, op_type, machine, next_day_start, next_day_end,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = next_day_end
                end_time = next_day_end
            else:
                unit_operations.append([
                    component, description, op_type, machine, start_time, end_time,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = end_time

            start_time = end_time

        return unit_operations, end_time

    while any(remaining_quantities.values()):
        day_start = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=17, minute=0, second=0, microsecond=0)

        for component in list(remaining_quantities.keys()):
            if remaining_quantities[component] <= 0:
                continue

            while remaining_quantities[component] > 0:
                unit_start_time = max(min(machine_end_times.values()), day_start)
                if unit_start_time >= day_end:
                    break

                unit_operations, unit_end_time = schedule_component(component, unit_start_time)
                schedule.extend(unit_operations)
                remaining_quantities[component] -= 1

                # Update daily production based on the completion time of the last operation
                if unit_operations:
                    completion_day = unit_operations[-1][5].date()  # end_time of the last operation
                    if component not in daily_production:
                        daily_production[component] = {}
                    if completion_day not in daily_production[component]:
                        daily_production[component][completion_day] = 0
                    daily_production[component][completion_day] += 1

        current_time = (day_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    schedule_df = pd.DataFrame(
        schedule,
        columns=[
            "component", "description", "type", "machine", "start_time", "end_time", "quantity"
        ],
    )
    overall_end_time = max(schedule_df['end_time'])
    overall_time = (overall_end_time - start_date).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time, daily_production





# Routes
@app.get("/operations/", response_model=List[OperationOut])
async def read_operations():
    df = fetch_operations()
    operations = df.to_dict(orient="records")
    return operations


@app.post("/operations/",  response_model=List[OperationOut])
async def create_operations(operations: OperationsIn):
    op_out = insert_operations(operations.operations)
    return op_out


@app.get("/schedule/", response_model=List[OperationOut1])
async def schedule():
    df = fetch_operations()
    # component_quantities = {"Component1": 10, "Component2": 10, "Component3": 10, "Component 4": 10, "Component 5": 10,"Component 6": 10, "Component 7": 10, "Component 8": 10}  # Define the quantities here
    component_quantities = fetch_component_quantities()  # Fetch quantities from DB
    schedule_df, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)
    scheduled_operations = schedule_df.to_dict(orient="records")
    return scheduled_operations

@app.get("/daily_production/", response_model=DailyProductionOut)
async def daily_production():
    df = fetch_operations()
    # component_quantities = {"Component1": 10, "Component2": 10, "Component3": 10, "Component 4": 10, "Component 5": 10,"Component 6": 10, "Component 7": 10, "Component 8": 10}  # Define the quantities here
    component_quantities = fetch_component_quantities()
    _, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)
    return {
        "overall_end_time": overall_end_time,
        "overall_time": overall_time,
        "daily_production": daily_production
    }

@app.post("/component_quantities/", response_model=List[ComponentQuantityOut])
async def create_component_quantities(quantities: List[ComponentQuantityIn]):
    return insert_component_quantities(quantities)

@app.get("/component_quantities/", response_model=Dict[str, int])
async def read_component_quantities():
    return fetch_component_quantities()


# TO RUN
# uvicorn app.main3:app --host 172.18.101.47 --port 4567 --reload
