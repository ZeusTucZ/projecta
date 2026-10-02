from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    document_type: str
    file_path: str
    status: str

    class Config:
        from_attributes = True