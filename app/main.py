from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

# Define a model for operations
class Operation(BaseModel):
    description: str
    type: str
    machine: str
    time: float  # Assuming time is in minutes


# Define a model for components
class Component(BaseModel):
    name: str
    quantity: int
    operations: List[Operation]


# Your component data
components_data = [
    {
        "name": "Component1",
        "quantity": 100,
        "operations": [
            {"description": "Facing A Side", "type": "Operation", "machine": "Turning Centre", "time": 1},
            {"description": "OD Turning from A side", "type": "Operation", "machine": "Turning Centre", "time": 2},
            {"description": "Centre Drilling Face A", "type": "Operation", "machine": "Turning Centre", "time": 1},
            {"description": "Job Rotation", "type": "Setup", "machine": "Turning Centre", "time": 0.5},
            {"description": "Facing B Side", "type": "Operation", "machine": "Turning Centre", "time": 1},
            {"description": "OD Turning from B side", "type": "Operation", "machine": "Turning Centre", "time": 2},
            {"description": "Centre Drilling Face B", "type": "Operation", "machine": "Turning Centre", "time": 1},
            {"description": "Hold Job between centres", "type": "Setup", "machine": "Turning Centre", "time": 0.5},
            {"description": "Step & Profile turning", "type": "Operation", "machine": "Turning Centre", "time": 4},
            {"description": "Through Drill", "type": "Operation", "machine": "Turning Centre", "time": 1.5},
            {"description": "ID Boring", "type": "Operation", "machine": "Turning Centre", "time": 4},
            {"description": "Thread Machining", "type": "Operation", "machine": "Turning Centre", "time": 3},
            {"description": "Clamping job in V Block/Vice", "type": "Setup", "machine": "VMC", "time": 1},
            {"description": "Face Milling", "type": "Operation", "machine": "VMC", "time": 1},
            {"description": "End Milling", "type": "Operation", "machine": "VMC", "time": 3},
            {"description": "Pocket Milling", "type": "Operation", "machine": "VMC", "time": 3},
            {"description": "Mount Job A Side Vertically", "type": "Setup", "machine": "VMC", "time": 0.5},
            {"description": "Drilling A Side", "type": "Operation", "machine": "VMC", "time": 1.5},
            {"description": "Rotate Job B Side Vertically", "type": "Setup", "machine": "VMC", "time": 0.5},
            {"description": "Drilling B Side", "type": "Operation", "machine": "VMC", "time": 1.5},
            {"description": "OD Grinding", "type": "Operation", "machine": "Cylindrical OD Grinder", "time": 2},
            {"description": "ID Grinding", "type": "Operation", "machine": "Cylindrical ID Grinder", "time": 2},
        ]
    },
    {
        "name": "Component2",
        "quantity": 200,
        "operations": [
            {"description": "Clamp Block in Vice", "type": "Setup", "machine": "HMC", "time": 2},
            {"description": "Face Mill M Side", "type": "Operation", "machine": "HMC", "time": 1.5},
            {"description": "Area Mill M Side", "type": "Operation", "machine": "HMC", "time": 4},
            {"description": "End Mill A B C & D Sides", "type": "Operation", "machine": "HMC", "time": 4},
            {"description": "Area Mill A, B, C and D Sides", "type": "Operation", "machine": "HMC", "time": 12},
            {"description": "Centre Drilling A Side", "type": "Operation", "machine": "HMC", "time": 1},
            {"description": "Through Drilling A Side", "type": "Operation", "machine": "HMC", "time": 3},
            {"description": "Centre Drilling B Side", "type": "Operation", "machine": "HMC", "time": 1},
            {"description": "Through Drilling B Side", "type": "Operation", "machine": "HMC", "time": 3},
            {"description": "Centre Drilling (2 small Holes) A Side", "type": "Operation", "machine": "HMC", "time": 1},
            {"description": "Through Drilling 2 Holes A Side", "type": "Operation", "machine": "HMC", "time": 2.5},
            {"description": "Centre Drilling (2 small Holes) C Side", "type": "Operation", "machine": "HMC", "time": 1},
            {"description": "Through Drilling 2 Holes C Side", "type": "Operation", "machine": "HMC", "time": 2.5},
            {"description": "Rotate Job with Face N Top", "type": "Setup", "machine": "HMC", "time": 2},
            {"description": "Face Milling N Side", "type": "Operation", "machine": "HMC", "time": 2},
            {"description": "Area Milling N Side", "type": "Operation", "machine": "HMC", "time": 4},
        ]
    },
    {
        "name": "Component3",
        "quantity": 150,
        "operations": [
            {"description": "Facing A Side", "type": "Operation", "machine": "Turning Centre", "time": 3},
            {"description": "OD Turning from A side", "type": "Operation", "machine": "Turning Centre", "time": 3},
            {"description": "Job Rotation", "type": "Setup", "machine": "Turning Centre", "time": 1},
            {"description": "Facing B Side", "type": "Operation", "machine": "Turning Centre", "time": 3},
            {"description": "OD Turning from B side", "type": "Operation", "machine": "Turning Centre", "time": 3},
            {"description": "Centre Drilling Face B", "type": "Operation", "machine": "Turning Centre", "time": 1.5},
            {"description": "Through Drill", "type": "Operation", "machine": "Turning Centre", "time": 4},
            {"description": "ID Boring", "type": "Operation", "machine": "Turning Centre", "time": 12},
            {"description": "Mounting on Fixture", "type": "Setup", "machine": "VMC", "time": 3},
            {"description": "PCD Holes drilling (Set 1)", "type": "Operation", "machine": "VMC", "time": 6},
            {"description": "PCD Holes drilling (Set 2)", "type": "Operation", "machine": "VMC", "time": 5},
            {"description": "Mount job on HMC with Rotary table", "type": "Setup", "machine": "HMC", "time": 3},
            {"description": "Face milling of outer periphery-360", "type": "Operation", "machine": "HMC", "time": 5},
            {"description": "Cavity Milling on outer periphery-360", "type": "Operation", "machine": "HMC", "time": 12},
            {"description": "Centre Holes drilling on Face C D E & F", "type": "Operation", "machine": "HMC",
             "time": 3.5},
            {"description": "Through Drilling on Face C D E & F", "type": "Operation", "machine": "HMC", "time": 8},
            {"description": "ID Thread Machining on Face C D E & F", "type": "Operation", "machine": "HMC", "time": 4},
            {"description": "ID Grind on Bore", "type": "Operation", "machine": "Grinding", "time": 3.5},
        ]
    }
]

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Endpoint to get scheduling results
@app.get("/schedule")
def get_schedule():
    schedule_results = {}
    current_time = datetime.now()

    for component_data in components_data:
        component_name = component_data["name"]
        schedule_results[component_name] = {"operations": []}

        for operation in component_data["operations"]:
            start_time = current_time
            end_time = start_time + timedelta(minutes=operation["time"])

            schedule_results[component_name]["operations"].append({
                "description": operation["description"],
                "machine": operation["machine"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            })

            current_time = end_time  # Update current time for next operation

    return schedule_results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="172.18.101.47", port=1234)

