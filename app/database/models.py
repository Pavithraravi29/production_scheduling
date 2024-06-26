from pony.orm import Database, Required, Optional, db_session, select
from datetime import datetime, timedelta

# Define your database connection
db = Database()


# Define models
class Operation(db.Entity):
    component = Required(str)
    description = Required(str)
    type = Required(str)
    machine = Required(str)
    time = Required(float)
    start_time = Optional(datetime)
    end_time = Optional(datetime)
    quantity = Required(str)



