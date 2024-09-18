from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.config import configure_database
from app.routers import operations, component_quantities, leadtime

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


app.include_router(operations.router, tags=["operations/production"])
app.include_router(component_quantities.router, tags=["component_quantities"])
app.include_router(leadtime.router, tags=["leadtime"])


# TO RUN
# uvicorn app.main:app --host 172.18.101.47 --port 4567 --reload