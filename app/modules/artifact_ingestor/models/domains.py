from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from common.mysql_declarative_base import Base

class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(String, primary_key=True, default=str(uuid.uuid4))
    domain = Column(String)
    sub_domain = Column(String)
    enabled = Column(Boolean)
    context = Column(String)
    is_default = Column(Boolean, default=False)
