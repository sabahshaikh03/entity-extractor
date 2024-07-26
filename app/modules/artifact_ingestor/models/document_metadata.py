from sqlalchemy import Column, String, Integer
from common.mysql_declarative_base import Base
from sqlalchemy.orm import Session, relationship
from sqlalchemy import select, join
from typing import List


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    locator = Column(String(2048), nullable=False)
    document_category = Column(String, nullable=False)
    document_type = Column(String, nullable=False)

    materials = relationship("MaterialToDocumentMapping", back_populates="document")
