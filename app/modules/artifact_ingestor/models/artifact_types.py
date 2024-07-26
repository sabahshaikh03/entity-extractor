from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base


class ArtifactsType(Base):
    __tablename__ = "artifacts_types"
    
    id = Column(String, primary_key=True, default=str(uuid.uuid4))
    type = Column(String)
    enabled = Column(Boolean)
    context = Column(String)
    is_default = Column(Boolean, default=False)

    artifacts = relationship("Artifacts", back_populates="artifacts_type")
