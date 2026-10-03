from pydantic import BaseModel, ConfigDict


class ContractSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_number: str
    title: str
    text: str
    source_page: int | None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    contract_number: str | None
    trade: str | None
    sections: list[ContractSectionResponse]