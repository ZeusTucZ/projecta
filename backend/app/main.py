from fastapi import FastAPI

from app.db import Base, engine

from app.models.project import Project
from app.models.document import Document
from app.models.drawing import DrawingRevision
from app.models.potential_change import PotentialChange
from app.models.rfi import RFI
from app.models.contract import Contract, ContractSection

from app.routers import projects, documents


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(projects.router)
app.include_router(documents.router)

@app.get("/")
def root():
    return {"message": "Construction Change AI API"}