from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List
from app.database.config import configure_database
from app.database.models import Operation
from pony.orm import db_session, select, commit
import pandas as pd

app = FastAPI()

configure_database()

# Pydantic models
class OperationIn(BaseModel):
    component: str
    description: str
    type: str
    machine: str
    time: float
    quantity: str

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
    quantity: str



# Function to fetch operations from the database
@db_session
def fetch_operations():
    operations = select(op for op in Operation).order_by(lambda op: op.id)[:]  # Order by 'id'

    operations_list = [
        (op.id, op.component, op.description, op.type, op.machine, op.time, op.start_time, op.end_time, op.quantity) for op in
        operations
    ]

    df = pd.DataFrame(
        operations_list,
        columns=["id", "component", "description", "type", "machine", "time", "start_time", "end_time", "quantity"],
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
            quantity=operation.quantity,
        )
        results.append(OperationOut(
            component=new_operation.component,
            description=new_operation.description,
            type=new_operation.type,
            machine=new_operation.machine,
            start_time=new_operation.start_time,
            end_time=new_operation.end_time,
            quantity=new_operation.quantity,
        ))
    commit()
    return results


# Function to schedule operations
def schedule_operations(df: pd.DataFrame) -> (pd.DataFrame, datetime, float):
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0

    # Sort DataFrame by 'id' to maintain the sequence as stored in the database
    df_sorted = df.sort_values(by='id')

    schedule = []
    machine_end_times = {machine: df_sorted['start_time'].min() for machine in df_sorted["machine"].unique()}
    component_end_times = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}
    component_last_end_time = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}

    for component, component_df in df_sorted.groupby('component'):
        component_df = component_df.sort_values(by='id')  # Ensure operations within component are in order

        for _, row in component_df.iterrows():
            description, op_type, machine, time, start_time, quantity = row[
                ["description", "type", "machine", "time", "start_time", "quantity"]
            ]
            start_time = max(start_time, component_last_end_time[component])  # Use last end time for the component

            # Check machine availability
            if start_time < machine_end_times[machine]:
                start_time = machine_end_times[machine]

            end_time = start_time + timedelta(minutes=time)
            schedule.append(
                [
                    component,
                    description,
                    op_type,
                    machine,
                    start_time,
                    end_time,
                    quantity  # Include quantity in the schedule
                ]
            )
            component_last_end_time[component] = end_time
            machine_end_times[machine] = end_time
            component_end_times[component] = max(component_end_times[component], end_time)

    schedule_df = pd.DataFrame(
        schedule,
        columns=[
            "component",
            "description",
            "type",
            "machine",
            "start_time",
            "end_time",
            "quantity"  # Add quantity column to DataFrame columns
        ],
    )

    # Calculate total time
    overall_end_time = max(component_end_times.values())
    overall_time = (overall_end_time - df_sorted['start_time'].min()).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time



# def schedule_operations(df: pd.DataFrame) -> (pd.DataFrame, datetime, float):
#     if df.empty:
#         return pd.DataFrame(), datetime.now(), 0.0
#
#     # Convert 'quantity' to numeric type (float or int)
#     df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')  # Convert to numeric, coerce errors to NaN
#
#     # Drop rows where 'quantity' could not be converted (if any)
#     df = df.dropna(subset=['quantity'])
#
#     # Calculate total workload for each operation
#     df['total_workload'] = df['time'] * df['quantity']
#
#     # Sort operations by total workload in descending order
#     df_sorted = df.sort_values(by=['component', 'total_workload'], ascending=[True, False])
#
#     schedule = []
#     machine_end_times = {machine: df_sorted['start_time'].min() for machine in df_sorted["machine"].unique()}
#     component_end_times = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}
#     component_last_end_time = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}
#
#     for component, component_df in df_sorted.groupby('component'):
#         component_df = component_df.sort_values(by='total_workload', ascending=False)  # Sort by workload
#
#         for _, row in component_df.iterrows():
#             description, op_type, machine, time, start_time, quantity = row[
#                 ["description", "type", "machine", "time", "start_time", "quantity"]
#             ]
#             start_time = max(start_time, component_last_end_time[component])  # Use last end time for the component
#
#             # Check machine availability
#             if start_time < machine_end_times[machine]:
#                 start_time = machine_end_times[machine]
#
#             end_time = start_time + timedelta(minutes=time * quantity)
#             schedule.append(
#                 [
#                     component,
#                     description,
#                     op_type,
#                     machine,
#                     start_time,
#                     end_time,
#                     quantity
#                 ]
#             )
#             component_last_end_time[component] = end_time
#             machine_end_times[machine] = end_time
#             component_end_times[component] = max(component_end_times[component], end_time)
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
#     # Calculate total time
#     overall_end_time = max(component_end_times.values())
#     overall_time = (overall_end_time - df_sorted['start_time'].min()).total_seconds() / 60
#
#     return schedule_df, overall_end_time, overall_time



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


@app.get("/schedule/", response_model=List[OperationOut])
async def schedule():
    df = fetch_operations()
    schedule_df, overall_end_time, overall_time = schedule_operations(df)
    scheduled_operations = schedule_df.to_dict(orient="records")
    return scheduled_operations
