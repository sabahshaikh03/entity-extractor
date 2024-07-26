from sqlalchemy import Column, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from common.mysql_declarative_base import Base
from app.modules.artifact_ingestor.enums.artifact_upload_statuses import ArtifactUploadStatus
from app.modules.artifact_ingestor.models.upload_types import UploadTypes
from app.modules.artifact_ingestor.models.categories import Category
from app.modules.artifact_ingestor.models.artifact_types import ArtifactsType


class Artifacts(Base):
    # DB : "dev_data_mesh_builder" - Customer
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, default=str(uuid.uuid4)) # TODO: We have to remove hyphens from uuid
    context = Column(String)
    name = Column(String)
    source_name = Column(String)
    source_link = Column(String)
    data_format = Column(String)
    status = Column(String)
    upload_status = Column(Enum(ArtifactUploadStatus))
    enabled = Column(Boolean)
    organization = Column(String)
    trust_factor = Column(String)
    uploaded_location = Column(String)
    upload_id = Column(String, ForeignKey("upload_types.id"))
    category_id = Column(String, ForeignKey("categories.id"))
    type_id = Column(String, ForeignKey("artifacts_types.id"))
    region = Column(String)
    country = Column(String)
    state = Column(String)
    city = Column(String)
    domain = Column(String)
    sub_domain = Column(String)
    file_upload_type = Column(String)
    tags = Column(String)
    realm = Column(String)
    
    upload_type = relationship("UploadTypes", back_populates="artifacts")
    category = relationship("Category", back_populates="artifacts")
    artifacts_type = relationship("ArtifactsType", back_populates="artifacts")
