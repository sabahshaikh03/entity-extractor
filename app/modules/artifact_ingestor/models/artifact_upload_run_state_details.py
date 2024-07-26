from sqlalchemy import Column, String, BigInteger, Text, Enum, Integer, ForeignKey
import enum
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base


# Define the Enum class for completed_stage_status
class CompletedStageStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"


class ArtifactUploadRunStateDetails(Base):
    __tablename__ = "artifact_upload_run_state_details"

    id = Column(String(64), primary_key=True)
    created_at = Column(BigInteger, nullable=False)
    created_by = Column(String(255))
    tenant_id = Column(String(255))
    updated_at = Column(BigInteger, nullable=False)
    updated_by = Column(String(255))
    folder_upload_id = Column(String(64), ForeignKey("folder_upload.id"))
    full_path = Column(Text)
    message_id = Column(String(255))
    queue_name = Column(String(255))
    folder_upload_type = Column(String(255))
    completed_stage_name = Column(String(255))
    completed_stage_status = Column(Enum(CompletedStageStatus))
    completed_stage_status_reason = Column(Text)
    attempt_count = Column(Integer)
    processing_duration = Column(BigInteger)
    
    folder_upload = relationship("FolderUpload", back_populates="run_state_details")
