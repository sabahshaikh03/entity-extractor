from enum import Enum

class ArtifactUploadStatus(Enum):
    """Enum for upload statuses."""
    STARTED = "STARTED"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    UPLOADED = "UPLOADED"
