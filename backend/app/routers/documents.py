from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.document import DocumentResponse

from app.models.rfi import RFI
from app.schemas.rfi import RFIResponse
from app.services.pdf_parser import extract_pdf_text
from app.services.rfi_parser import extract_rfi_data

from app.models.drawing import DrawingRevision
from app.schemas.drawing import DrawingResponse
from app.services.drawing_parser import extract_drawing_data

from app.models.contract import Contract, ContractSection
from app.schemas.contract import ContractResponse
from app.services.contract_parser import extract_contract_data


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

@router.post(
    "/documents/{document_id}/process-rfi",
    response_model=RFIResponse,
)
def process_rfi(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.document_type != "rfi":
        raise HTTPException(
            status_code=400,
            detail="Processing currently supports only RFI documents",
        )

    if not Path(document.file_path).is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    pages = extract_pdf_text(document.file_path)

    if not any(page["text"].strip() for page in pages):
        raise HTTPException(
            status_code=422,
            detail="No readable text was extracted",
        )

    data = extract_rfi_data(pages)

    if not data["rfi_number"]:
        raise HTTPException(
            status_code=422,
            detail="Could not identify an RFI number; review the document",
        )

    rfi = db.query(RFI).filter(
        RFI.document_id == document_id
    ).first()

    if rfi is None:
        rfi = RFI(document_id=document_id)
        db.add(rfi)

    for field, value in data.items():
        setattr(rfi, field, value)

    document.status = "processed"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(rfi)
    return rfi

@router.post(
    "/documents/{document_id}/process-drawings",
    response_model=list[DrawingResponse],
)
def process_drawings(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.document_type != "drawing":
        raise HTTPException(
            status_code=400,
            detail="Document must have type drawing",
        )

    if not Path(document.file_path).is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    existing = db.query(DrawingRevision).filter(
        DrawingRevision.document_id == document_id
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This document already has saved drawing revisions",
        )

    pages = extract_pdf_text(document.file_path)
    extracted_drawings = extract_drawing_data(pages)

    if not extracted_drawings:
        raise HTTPException(
            status_code=422,
            detail="No drawing pages found",
        )

    # Validate all pages before saving any records.
    for data in extracted_drawings:
        if not data["drawing_number"] or not data["revision"]:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Missing drawing number or revision "
                    f"on page {data['source_page']}"
                ),
            )

        if (
            len(data["drawing_number"]) > 100
            or len(data["revision"]) > 50
            or len(data["title"] or "") > 255
            or len(data.get("discipline") or "") > 100
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Extracted fields exceed database limits "
                    f"on page {data['source_page']}"
                ),
            )

    drawings = [
        DrawingRevision(
            document_id=document_id,
            drawing_number=data["drawing_number"],
            revision=data["revision"],
            title=data["title"],
            discipline=data.get("discipline"),
        )
        for data in extracted_drawings
    ]

    try:
        db.add_all(drawings)
        document.status = "processed"
        db.commit()
    except Exception:
        db.rollback()
        raise

    for drawing in drawings:
        db.refresh(drawing)

    return drawings

@router.post(
    "/documents/{document_id}/process-contract",
    response_model=ContractResponse,
)
def process_contract(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.document_type != "contract":
        raise HTTPException(
            status_code=400,
            detail="Document must have type contract",
        )

    if not Path(document.file_path).is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    existing = db.query(Contract).filter(
        Contract.document_id == document_id
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This document already has a saved contract",
        )

    pages = extract_pdf_text(document.file_path)

    if not any(page["text"].strip() for page in pages):
        raise HTTPException(
            status_code=422,
            detail="No readable text was extracted",
        )

    data = extract_contract_data(pages)

    if not data["sections"]:
        raise HTTPException(
            status_code=422,
            detail="No contract sections recognized; review the document format",
        )

    if (
        len(data["contract_number"] or "") > 100
        or len(data["trade"] or "") > 100
    ):
        raise HTTPException(
            status_code=422,
            detail="Contract fields exceed database limits",
        )

    for section in data["sections"]:
        if (
            not section["text"]
            or len(section["section_number"]) > 50
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Section {section['section_number']} has empty text "
                    "or a section number exceeding database limits"
                ),
            )

    contract = Contract(
        document_id=document_id,
        contract_number=data["contract_number"],
        trade=data["trade"],
    )

    contract.sections = [
        ContractSection(
            section_number=section["section_number"],
            title=section["title"],
            text=section["text"],
            source_page=section["source_page"],
        )
        for section in data["sections"]
    ]

    try:
        db.add(contract)
        document.status = "processed"
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(contract)
    return contract
