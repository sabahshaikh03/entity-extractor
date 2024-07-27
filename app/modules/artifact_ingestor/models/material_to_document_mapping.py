from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Index, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base
from sqlalchemy.types import String
from sqlalchemy.ext.declarative import declared_attr
from app.modules.artifact_ingestor.models.document_metadata import DocumentMetadata
from app.modules.artifact_ingestor.models.global_node import GlobalNode

class MaterialToDocumentCompositeKey(BaseModel):
    document_id: str
    material_id: str

    class Config:
        from_attributes = True

class MaterialToDocumentMapping(Base):
    __tablename__ = 'material_to_document_mapping'

    @declared_attr
    def __table_args__(cls):
        return (
            Index('material_id_index', 'material_id'),
            UniqueConstraint('document_id', 'material_id', name='document_material_constraint'),
            PrimaryKeyConstraint('document_id', 'material_id', name='material_to_document_pk'),
        )

    document_id = Column(String, ForeignKey('document_metadata.id'), nullable=False)
    material_id = Column(String, ForeignKey('global_node.id'), nullable=False)
    
    document = relationship("DocumentMetadata", back_populates="materials")
    material = relationship("GlobalNode", back_populates="documents")
