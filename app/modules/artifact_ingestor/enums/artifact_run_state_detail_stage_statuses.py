from enum import Enum

class ArtifactRunStateDetailStageStatus(Enum):
    """Enum for arttiact_run_state_details stages"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"