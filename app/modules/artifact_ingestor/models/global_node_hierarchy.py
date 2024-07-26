from pydantic import BaseModel
from sqlalchemy import Column, Enum as SQLAlchemyEnum, Index,ForeignKey,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base
from app.modules.artifact_ingestor.enums.node_use_sub_types import NodeUseSubType
from app.modules.artifact_ingestor.enums.node_use_types import NodeUseType


class GlobalNodeHierarchyCompositeKey(BaseModel):
    parent_node_id: str
    child_node_id: str

    class Config:
        from_attributes = True


class GlobalNodeHierarchy(Base):
    __tablename__ = "global_node_hierarchy"

    __table_args__ = (
        Index("parent_node_id_index", "parent_node_id"),
        Index("child_node_id_index", "child_node_id"),
    )

    parent_node_id = Column(String, ForeignKey("global_node.id"), primary_key=True)
    child_node_id = Column(String, ForeignKey("global_node.id") , primary_key=True)
    chemical_weight_percent =  Column(String(255))

    # use_type = Column(
    #     SQLAlchemyEnum(NodeUseType), default=NodeUseType.UNKNOWN, nullable=False
    # )
    # use_sub_type = Column(
    #     SQLAlchemyEnum(NodeUseSubType), default=NodeUseSubType.NONE, nullable=False
    # )

    parent_node = relationship("GlobalNode", back_populates="global_node_hierarchy_parent", foreign_keys=[parent_node_id])
    child_node = relationship("GlobalNode", back_populates="global_node_hierarchy_child", foreign_keys=[child_node_id])
    
