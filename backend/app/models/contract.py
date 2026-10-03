from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
        unique=True,
    )

    contract_number = Column(String(100), nullable=True)
    trade = Column(String(100), nullable=True)

    sections = relationship(
        "ContractSection",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractSection.id",
    )


class ContractSection(Base):
    __tablename__ = "contract_sections"

    id = Column(Integer, primary_key=True)

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False,
        index=True,
    )

    section_number = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    text = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)

    contract = relationship(
        "Contract",
        back_populates="sections",
    )