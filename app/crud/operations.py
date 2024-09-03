from typing import List
from app.database.models import Operation
from app.schemas.operations import OperationIn, OperationOut
from pony.orm import db_session, select, commit
import pandas as pd

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

@db_session
def insert_operations(operations: List[OperationIn]) -> List[OperationOut]:
    from datetime import datetime, timedelta
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
        )
        results.append(OperationOut(
            component=new_operation.component,
            description=new_operation.description,
            type=new_operation.type,
            machine=new_operation.machine,
            start_time=new_operation.start_time,
            end_time=new_operation.end_time,
        ))
    commit()
    return results
