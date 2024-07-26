from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from common.mysql_declarative_base import Base

class UploadTypes(Base):
    __tablename__ = "upload_types"
    
    id = Column(String, primary_key=True, default=str(uuid.uuid4))
    upload_type = Column(String)
    enabled = Column(Boolean)
    context = Column(String)
    is_default = Column(Boolean, default=False)

    artifacts = relationship("Artifacts", back_populates="upload_type")
    
