from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.db import Base


class RFI(Base):
    __tablename__ = "rfis"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
        unique=True,
    )

    rfi_number = Column(String(100))
    date_issued = Column(String(50))
    drawing_reference = Column(Text)
    subject = Column(Text)
    question = Column(Text)
    response = Column(Text)
    potential_impact = Column(Text)
    source_page = Column(Integer)