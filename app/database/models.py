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

