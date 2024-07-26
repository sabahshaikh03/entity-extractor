from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class ArtifactInputDTO(BaseModel):
    source_name: str = Field(..., description="Source name must not be null")
    source_link: str = Field(..., description="Source link must not be null")
    data_format: str = Field(..., description="Data format must not be null")
    upload_type: str = Field(..., description="Upload type must not be null")
    domain: str = Field(..., description="Domain must not be null")
    sub_domain: str = Field(..., description="Sub domain must not be null")
    category: str = Field(..., description="Category must not be null")
    type: str = Field(..., description="Type must not be null")
    region: str = Field(..., description="Region must not be null")
    country: str = Field(..., description="Country must not be null")
    state: str = Field(..., description="State must not be null")
    city: str = Field(..., description="City must not be null")
    organization: str = Field(..., description="Organization must not be null")
    trust_factor: str = Field(..., description="Trust factor must not be null")
    status: str = Field(..., description="Status must not be null")
    enabled: bool = Field(..., description="Enabled must not be null")
    name: str = Field(..., description="Name must not be null")
    file_upload_type: str = Field(..., description="File upload type must not be null")
    file_url: Optional[str] = None
    tags: Optional[List[str]] = None
