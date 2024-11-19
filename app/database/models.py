from pony.orm import Database, Required, Optional
from datetime import datetime

db = Database()

class Operation(db.Entity):
    component = Required(str)
    description = Required(str)
    type = Required(str)
    machine = Required(str)
    time = Required(float)
    start_time = Optional(datetime)
    end_time = Optional(datetime)
    # quantity = Required(int)

class ComponentQuantity(db.Entity):
    component = Required(str, unique=True)
    quantity = Required(int)

class LeadTime(db.Entity):
    component = Required(str, unique=True)
    due_date = Required(datetime)

class RawMaterial(db.Entity):
    name = Required(str, unique=True)
    available = Required(bool)
    available_from = Optional(datetime)  # New field

class MachineStatus(db.Entity):
    machine = Required(str, unique=True)
    status = Required(str)  # 'ON' or 'OFF'
    available_from = Optional(datetime)  # New field