from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.document import DocumentResponse


router = APIRouter(
    tags=["Documents"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse
)
def upload_document(
    project_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Make sure the project exists
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # 2. Validate document type
    allowed_types = {"drawing", "rfi", "contract"}

    if document_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="document_type must be drawing, rfi, or contract"
        )

    # 3. Create a folder for this project
    project_upload_dir = UPLOAD_DIR / str(project_id)
    project_upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # 4. Create destination path
    file_path = project_upload_dir / file.filename

    # 5. Save the uploaded file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    # 6. Save metadata in PostgreSQL
    new_document = Document(
        project_id=project_id,
        filename=file.filename,
        document_type=document_type,
        file_path=str(file_path),
        status="uploaded"
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document

@router.get(
    "/projects/{project_id}/documents",
    response_model=list[DocumentResponse]
)
def list_documents(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return db.query(Document).filter(
        Document.project_id == project_id
    ).order_by(Document.id).all()