from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.modules.artifact_ingestor.dto.chemical_dto import Chemical


# MSDS OpenAI Response Data Class
class MSDSAnalysis(BaseModel):
    material_name: str
    upc_number: str
    chemicals: List[Chemical]
    manufacturer_name: str
    manufacturer_address: str
    manufacturer_city: str
    manufacturer_postal_code: str
    manufacturer_country: str
    manufacturer_state: str
    product_number: Optional[str] = None
    manufacturer_region: Optional[str] = None
    material_id: Optional[str] = None
    artifact_id: Optional[str] = None
    analysis_identifier: Optional[str] = None
    artifact_locator: Optional[str] = None
    pfas_status: Optional[str] = None
    pfas_information_source: Optional[str] = None
    violations: List[Any] = []
