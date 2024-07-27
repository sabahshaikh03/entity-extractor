from sqlalchemy import Column, String, BigInteger, Integer, Text, Enum
from enum import Enum as PythonEnum
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base


# Define enums
class LocationType(PythonEnum):
    SHAREPOINT = "SHAREPOINT"
    DISK = "DISK"
    AZUREBLOBSTORAGE = "AZUREBLOBSTORAGE"


class ArtifactType(PythonEnum):
    MSDS = "MSDS"


class UploadStatus(PythonEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"


# Define the model
class FolderUpload(Base):
    __tablename__ = "folder_upload"

    id = Column(String(64), primary_key=True)
    created_at = Column(BigInteger, nullable=False)
    created_by = Column(String(255))
    tenant_id = Column(String(255))
    updated_at = Column(BigInteger, nullable=False)
    updated_by = Column(String(255))
    name = Column(String(255))
    folder_location = Column(Text)
    location_type = Column(Enum(LocationType))
    artifact_type = Column(Enum(ArtifactType))
    status = Column(Enum(UploadStatus))
    total_count = Column(Integer)
    running_count = Column(String(255))
    next_page_link = Column(Text)
    run_state_details = relationship(
        "ArtifactUploadRunStateDetails", back_populates="folder_upload"
    )
    # upload_details = relationship(
    #     "ArtifactUploadDetails", back_populates="folder_upload"
    # )
