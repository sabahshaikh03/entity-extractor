from app.modules.artifact_ingestor.enums.pfas_statuses import PfasStatus
from app.modules.artifact_ingestor.enums.pfas_information_sources import (
    PfasInformationSource,
)
from pydantic import BaseModel


class PFASResolution(BaseModel):
    pfas_status: PfasStatus
    pfas_information_source: PfasInformationSource
