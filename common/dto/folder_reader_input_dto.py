from pydantic import BaseModel, Field, ValidationError


class FolderReaderInputDTO(BaseModel):
    artifact_type: str = Field(..., description="Source name must not be null")
    location_type: str = Field(..., description="Source name must not be null")
    folder_location: str = Field(..., description="Source name must not be null")
    folder_upload_id: str = Field(..., description="Source name must not be null")
