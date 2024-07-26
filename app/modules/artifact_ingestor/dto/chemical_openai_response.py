from pydantic import BaseModel, Field
from typing import Optional
from app.modules.artifact_ingestor.enums.pfas_information_sources import PfasInformationSource

class ChemicalsOpenAiResponse(BaseModel):
    chemical_name: Optional[str] = Field(None, alias="chemical_name")
    tag: Optional[str] = None
    cas_no: Optional[str] = Field(None, alias="cas_no")
    composition: Optional[str] = None
    pfas_information_source: Optional[PfasInformationSource] = Field(
        None, alias="pfas_information_source"
    )
    ec_no: Optional[str] = Field(None, alias="ec_no")
