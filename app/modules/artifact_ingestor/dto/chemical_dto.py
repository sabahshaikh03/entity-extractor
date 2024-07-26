from pydantic import BaseModel, Field
from typing import List, Optional
from app.modules.artifact_ingestor.enums.pfas_information_sources import (
    PfasInformationSource,
)
from app.modules.artifact_ingestor.enums.violation_types import ViolationType
from app.modules.artifact_ingestor.enums.violation_statuses import ViolationStatus
from app.modules.artifact_ingestor.enums.information_sources import InformationSource


class Violations(BaseModel):
    violation_type: Optional[ViolationType] = Field(None, alias="violationType")
    information_source: Optional[InformationSource] = Field(
        None, alias="informationSource"
    )
    violation_status: Optional[ViolationStatus] = Field(None, alias="violationStatus")
    category: Optional[List[str]] = None


class Chemical(BaseModel):
    chemical_name: Optional[str] = Field(None, alias="chemical_name")
    tag: Optional[str] = None
    cas_no: Optional[str] = Field(None, alias="cas_no")
    composition: Optional[str] = None
    pfas_information_source: Optional[PfasInformationSource] = Field(
        None, alias="pfas_information_source"
    )
    ec_no: Optional[str] = Field(None, alias="ec_no")
    violations: Optional[List[Violations]] = None
