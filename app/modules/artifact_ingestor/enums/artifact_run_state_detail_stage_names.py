from enum import Enum

class ArtifactRunStateDetailStageName(Enum):
    """Enum for arttiact_run_state_details stages"""
    ADD_ARTIFACT = "ADD_ARTIFACT"
    ANALYZING = "ANALYZING"
    SAVING = "SAVING"
    UPLOADING = "UPLOADING"