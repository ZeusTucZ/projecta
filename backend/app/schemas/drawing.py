from pydantic import BaseModel, ConfigDict


class DrawingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    drawing_number: str
    revision: str
    title: str | None
    discipline: str | None = None
    previous_revision_id: int | None