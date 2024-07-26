from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.artifact_ingestor.models.global_node_hierarchy import GlobalNodeHierarchy

class GlobalNodeHierarchyRepo:
    def __init__(self, session: Session):
        self.session = session

    def save(self,node_hierarchy:GlobalNodeHierarchy)->GlobalNodeHierarchy:
        self.session.add(node_hierarchy)
        return node_hierarchy
    
    def find_all_by_parent_id(self, parent_node_id: str) -> List[GlobalNodeHierarchy]:
        query = text("SELECT * FROM global_node_hierarchy WHERE parent_node_id = :parent_node_id")
        return self.session.execute(query, {"parent_node_id": parent_node_id}).scalars().all()

    def find_all_by_parent_and_child_id(self, parent_node_id: str, child_node_id: str) -> Optional[GlobalNodeHierarchy]:
        query = text("""
            SELECT * FROM global_node_hierarchy 
            WHERE parent_node_id = :parent_node_id AND child_node_id = :child_node_id
        """)
        result = self.session.execute(query, {"parent_node_id": parent_node_id, "child_node_id": child_node_id}).first()
        return result if result else None

    def find_hierarchy_all_by_material_ids(self, material_ids: List[str]) -> List[GlobalNodeHierarchy]:
        query = text("SELECT * FROM global_node_hierarchy WHERE parent_node_id IN :material_ids")
        return self.session.execute(query, {"material_ids": tuple(material_ids)}).scalars().all()

    def delete_by_id(self, id) -> None:
        query = text("""
            DELETE FROM global_node_hierarchy 
            WHERE parent_node_id = :parent_node_id AND child_node_id = :child_node_id
        """)
        self.session.execute(query, {"parent_node_id": id.parent_node_id, "child_node_id": id.child_node_id})
        self.session.commit()

    def find_all_by_child_id(self, child_node_id: str) -> List[GlobalNodeHierarchy]:
        query = text("SELECT * FROM global_node_hierarchy WHERE child_node_id = :child_node_id")
        return self.session.execute(query, {"child_node_id": child_node_id}).scalars().all()

    def find_hierarchy_by_material_name_and_manufacturer(self, name: str, manufacturer_name: str) -> List[GlobalNodeHierarchy]:
        query = text("""
            SELECT nh.* FROM global_node_hierarchy nh
            JOIN global_node gn ON nh.parent_node_id = gn.id
            JOIN manufacturer m ON gn.manufacturer_id = m.id
            WHERE replace(lower(gn.name), ' ', '') = replace(lower(:name), ' ', '')
            AND m.name = :manufacturer_name
        """)
        return self.session.execute(query, {"name": name, "manufacturer_name": manufacturer_name}).scalars().all()
