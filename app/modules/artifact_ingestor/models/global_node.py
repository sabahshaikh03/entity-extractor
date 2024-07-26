from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import VARCHAR
from common.mysql_declarative_base import Base
from app.modules.artifact_ingestor.enums.pfas_statuses import PfasStatus
from app.modules.artifact_ingestor.enums.global_node_types import GlobalNodeTypes
from app.modules.artifact_ingestor.enums.pfas_information_sources import (
    PfasInformationSource,
)
from app.modules.artifact_ingestor.models.manufacturer import Manufacturer
from app.modules.artifact_ingestor.models.global_node_hierarchy import GlobalNodeHierarchy 



class GlobalNode(Base):
    # DB : viridium_system_kb - system
    __tablename__ = "global_node"

    # __table_args__ = (
    #     {"postgresql_using": "btree"},  # Add specific index types if needed
    # )

    id = Column(
        String, primary_key=True
    )
    name = Column(String(244), nullable=False)
    description = Column(String(1000), nullable=True)
    manufacturer_id = Column(String, ForeignKey("manufacturer.id"), nullable=False)
    node_type = Column(VARCHAR(64), nullable=False)  # Use Enum if needed
    pfas_status = Column(VARCHAR(64), nullable=False, default="Pending")
    pfas_information_source = Column(VARCHAR(64), nullable=False, default="OECD")
    cas_number = Column(VARCHAR(64), nullable=True)

    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="global_nodes")
    documents = relationship("MaterialToDocumentMapping", back_populates="material")
    
    global_node_hierarchy_parent = relationship("GlobalNodeHierarchy", back_populates="parent_node", foreign_keys=[GlobalNodeHierarchy.parent_node_id])
    global_node_hierarchy_child = relationship("GlobalNodeHierarchy", back_populates="child_node", foreign_keys=[GlobalNodeHierarchy.child_node_id])

    # Constraints
    # __table_args__ = (
    #     {'postgresql_unique_constraints': [('name', 'node_type', 'manufacturer_id')]},
    #     {'indexes': [(name_index, 'name')]},  # Adjust for SQLAlchemy
    # )
