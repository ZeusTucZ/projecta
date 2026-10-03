from pydantic import BaseModel, ConfigDict


class RFIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    rfi_number: str | None
    date_issued: str | None
    drawing_reference: str | None
    subject: str | None
    question: str | None
    response: str | None
    potential_impact: str | None
    source_page: int | None