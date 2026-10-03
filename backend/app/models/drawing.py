from sqlalchemy import Column, Integer, String, ForeignKey

from app.db import Base


class DrawingRevision(Base):
    __tablename__ = "drawing_revisions"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    drawing_number = Column(
        String(100),
        nullable=False
    )

    revision = Column(
        String(50),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=True
    )

    discipline = Column(
        String(100),
        nullable=True,
    )

    previous_revision_id = Column(
        Integer,
        ForeignKey("drawing_revisions.id"),
        nullable=True
    )