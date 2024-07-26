from pydantic import BaseModel
from enum import Enum
from app.modules.artifact_ingestor.enums.pfas_statuses import PfasStatus
from app.modules.artifact_ingestor.enums.pfas_information_sources import (
    PfasInformationSource,
)


class ArtifactMSDSMaterials(BaseModel):
    material_name: str
    pfas_status: PfasStatus
    pfas_information_source: PfasInformationSource
    manufacturer_name: str
    locator: str
    artifact_name: str
    artifact_type: str

    class Config:
        use_enum_values = (
            True  # This will ensure that enum values are represented as strings
        )
