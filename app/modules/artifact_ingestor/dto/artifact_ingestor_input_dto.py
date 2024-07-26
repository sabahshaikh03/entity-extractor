from pydantic import BaseModel, Field, ValidationError

class ArtifactIngestorInputDTO(BaseModel):
    artifact_file_url: str = Field(..., description="Source name must not be null")
    artifact_upload_run_state_id: str = Field(
        ..., description="Source name must not be null"
    )
