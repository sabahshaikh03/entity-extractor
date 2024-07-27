from sqlalchemy import Column, String, BigInteger, Text, Enum, ForeignKey, Index
import enum
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base


# Define the Enum class for status
class Status(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"


class ArtifactUploadDetails(Base):
    __tablename__ = "artifact_upload_details"

    id = Column(String(64), primary_key=True)
    created_at = Column(BigInteger, nullable=False)
    created_by = Column(String(255))
    tenant_id = Column(String(255))
    updated_at = Column(BigInteger, nullable=False)
    updated_by = Column(String(255))
    folder_upload_id = Column(String(64), ForeignKey("folder_upload.id"))
    full_path = Column(Text)
    status = Column(Enum(Status))
    status_reason = Column(Text)
    artifact_id = Column(String(64), ForeignKey("artifacts.id"))
    started_at = Column(BigInteger, nullable=False)
    completed_at = Column(BigInteger, nullable=False)
    
    # folder_upload = relationship("FolderUpload", back_populates="upload_details")

    # Define indexes
    __table_args__ = (
        Index(
            "ix_folder_upload_id_full_path",
            "folder_upload_id",
            "full_path",
            unique=True,
        ),
    )
