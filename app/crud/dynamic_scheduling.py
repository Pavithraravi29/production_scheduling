from typing import List
from pony.orm import db_session, flush
from app.database.models import RawMaterial, MachineStatus
from app.schemas.dynamic_scheduling import RawMaterialIn, RawMaterialOut, MachineStatusIn, MachineStatusOut


@db_session
def insert_raw_materials(raw_materials: List[RawMaterialIn]) -> List[RawMaterialOut]:
    inserted = []
    for rm in raw_materials:
        # Insert the raw material into the database
        raw_material = RawMaterial(name=rm.name, available=rm.available, available_from=rm.available_from)

        # Ensure the object is flushed so the ID is generated
        flush()  # This forces the database to assign the ID

        # Now you can access the ID and append to the result list
        inserted.append(RawMaterialOut(id=raw_material.id, name=raw_material.name, available=raw_material.available, available_from=raw_material.available_from))

    return inserted

@db_session
def fetch_raw_materials() -> List[RawMaterialOut]:
    return [RawMaterialOut(id=rm.id, name=rm.name, available=rm.available, available_from=rm.available_from) for rm in RawMaterial.select()]

@db_session
def update_raw_material(raw_material_id: int, available: bool) -> RawMaterialOut:
    rm = RawMaterial[raw_material_id]
    rm.available = available
    return RawMaterialOut(id=rm.id, name=rm.name, available=rm.available, available_from=rm.available_from)

@db_session
def insert_machine_statuses(statuses: List[MachineStatusIn]) -> List[MachineStatusOut]:
    inserted = []
    for status in statuses:
        machine_status = MachineStatus(machine=status.machine, status=status.status, available_from=status.available_from)
        flush()  # Force the database to generate the ID immediately
        inserted.append(MachineStatusOut(id=machine_status.id, machine=machine_status.machine, status=machine_status.status, available_from=machine_status.available_from))
    return inserted

@db_session
def fetch_machine_statuses() -> List[MachineStatusOut]:
    return [MachineStatusOut(id=ms.id, machine=ms.machine, status=ms.status, available_from=ms.available_from) for ms in MachineStatus.select()]

@db_session
def update_machine_status(machine_id: int, status: str) -> MachineStatusOut:
    ms = MachineStatus[machine_id]
    ms.status = status
    return MachineStatusOut(id=ms.id, machine=ms.machine, status=ms.status, available_from=ms.available_from)