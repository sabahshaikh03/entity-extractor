from sqlalchemy import text
from sqlalchemy.orm import Session
from app.modules.artifact_ingestor.models.global_node import GlobalNode
from typing import List


class GlobalNodeRepo:
    def __init__(self, session: Session):
        self.session = session

    def save(self, node: GlobalNode):
        self.session.add(node)
        return node
    
    def find_by_id(self, id: str)-> GlobalNode:
        query = text(
            """
        SELECT * FROM global_node gn 
        WHERE gn.node_type = 'MATERIAL' 
        AND gn.id = :id
        """
        )
        return self.session.execute(query, {"id": id}).scalars().first()

    def find_material_by_name(self, name: str):
        query = text(
            """
        SELECT * FROM global_node gn 
        WHERE replace(lower(gn.name), ' ', '') = replace(lower(:name), ' ', '') 
        AND gn.node_type = 'MATERIAL' 
        AND trim(gn.name) != ''
        """
        )
        return self.session.execute(query, {"name": name}).scalars().all()

    def find_material_by_name_and_manufacturer_id(
        self, name: str, manufacturer_id: str
    ):
        query = text(
            """
        SELECT * FROM global_node gn 
        WHERE replace(lower(gn.name), ' ', '') = replace(lower(:name), ' ', '') 
        AND gn.node_type = 'MATERIAL' 
        AND gn.manufacturer_id = :manufacturer_id
        """
        )
        return (
            self.session.execute(
                query, {"name": name, "manufacturer_id": manufacturer_id}
            )
            .scalars()
            .all()
        )

    def find_material_by_name_substring(self, name: str):
        query = text(
            """
        SELECT * FROM global_node gn 
        WHERE gn.name LIKE '%' || :name || '%' 
        AND gn.node_type = 'MATERIAL'
        """
        )
        return self.session.execute(query, {"name": name}).scalars().all()

    def find_chemical_by_name_and_manufacturer_id(
        self, name: str, manufacturer_id: str
    )-> List[GlobalNode]:
        query = text(
            """
        SELECT * FROM global_node gn 
        WHERE gn.name = :name 
        AND gn.node_type = 'CHEMICAL' 
        AND gn.manufacturer_id = :manufacturer_id
        """
        )
        return (
            self.session.execute(
                query, {"name": name, "manufacturer_id": manufacturer_id}
            )
            .scalars()
            .all()
        )

    def find_chemical_by_cas_number_and_manufacturer_id(
        self, cas_number: str, manufacturer_id: str
    ) -> List[GlobalNode]:
        query = text(
            """
        SELECT * FROM global_node 
        WHERE cas_number = :cas_number 
        AND node_type = 'CHEMICAL' 
        AND manufacturer_id = :manufacturer_id
        """
        )
        return (
            self.session.execute(
                query, {"cas_number": cas_number, "manufacturer_id": manufacturer_id}
            )
            .scalars()
            .all()
        )

    def find_cas_number_for_chemicals_using_material_name(self, names: list):
        query = text(
            """
        SELECT gn.cas_number FROM global_node gn 
        JOIN global_node_hierarchy gnh ON gn.id = gnh.child_node_id 
        JOIN global_node gn2 ON gnh.parent_node_id = gn2.id 
        WHERE replace(lower(gn2.name), ' ', '') IN :names
        """
        )
        return self.session.execute(query, {"names": tuple(names)}).scalars().all()

    def find_all_using_material_name(self, names: list):
        query = text(
            """
        SELECT gn.* FROM global_node gn 
        JOIN global_node_hierarchy gnh ON gn.id = gnh.child_node_id 
        JOIN global_node gn2 ON gnh.parent_node_id = gn2.id 
        WHERE replace(lower(gn2.name), ' ', '') IN :names
        """
        )
        return self.session.execute(query, {"names": tuple(names)}).scalars().all()

    def find_count_by_manufacturer_id_and_not_in_nodes(
        self, manufacturer_id: str, node_ids: list
    ):
        query = text(
            """
        SELECT count(*) FROM global_node gn 
        WHERE gn.manufacturer_id = :manufacturer_id 
        AND gn.id NOT IN :node_ids
        """
        )
        return self.session.execute(
            query, {"manufacturer_id": manufacturer_id, "node_ids": tuple(node_ids)}
        ).scalar()

    def find_material_by_name_and_manufacturer_name(
        self, name: str, manufacturer_name: str
    ):
        query = text(
            """
        SELECT gn.* FROM global_node gn 
        JOIN manufacturer m ON gn.manufacturer_id = m.id
        WHERE replace(lower(gn.name), ' ', '') = replace(lower(:name), ' ', '') 
        AND gn.node_type = 'MATERIAL' 
        AND trim(gn.name) != '' 
        AND m.name = :manufacturer_name
        """
        )
        return (
            self.session.execute(
                query, {"name": name, "manufacturer_name": manufacturer_name}
            )
            .scalars()
            .first()
        )

    def find_material_supplier_list(self):
        query = text(
            """
        SELECT DISTINCT gn.name, gn.id, gn.cas_number, gn.pfas_information_source, gn.pfas_status, m.name as manufacturer_name, gn.manufacturer_id, dm.locator 
        FROM global_node gn 
        INNER JOIN material_to_document_mapping mdm ON mdm.material_node_id = gn.id 
        INNER JOIN document_metadata dm ON dm.id = mdm.document_metadata_id
        JOIN manufacturer m ON gn.manufacturer_id = m.id
        """
        )
        return self.session.execute(query).scalars().all()

    def find_material_supplier_list_with_substring(self, name: str):
        query = text(
            """
        SELECT DISTINCT gn.name, gn.id, gn.cas_number, gn.pfas_information_source, gn.pfas_status, m.name as manufacturer_name, gn.manufacturer_id, dm.locator 
        FROM global_node gn 
        INNER JOIN material_to_document_mapping mdm ON mdm.material_node_id = gn.id 
        INNER JOIN document_metadata dm ON dm.id = mdm.document_metadata_id 
        JOIN manufacturer m ON gn.manufacturer_id = m.id
        WHERE lower(gn.name) LIKE '%' || lower(:name) || '%'
        """
        )
        return self.session.execute(query, {"name": name}).scalars().all()

    def find_material_msds_locators(self, material_id: str):
        query = text(
            """
        SELECT DISTINCT dm.locator 
        FROM global_node gn 
        INNER JOIN material_to_document_mapping mdm ON mdm.material_node_id = gn.id 
        INNER JOIN document_metadata dm ON dm.id = mdm.document_metadata_id 
        WHERE gn.id = :material_id
        """
        )
        return self.session.execute(query, {"material_id": material_id}).scalars().all()

    def find_materials_by_chemical_id(self, id: str)-> List[GlobalNode]:
        query = text(
            """
        SELECT gnc.* 
        FROM global_node gnc 
        INNER JOIN global_node_hierarchy gnh ON gnc.id = gnh.child_node_id 
        WHERE gnc.node_type = 'CHEMICAL' 
        AND gnh.parent_node_id = :id
        """
        )
        return self.session.execute(query, {"id": id}).scalars().all()

    def find_chemicals_by_material(self, id: str)-> List[GlobalNode]:
        query = text(
            """
        SELECT gnc.* 
        FROM global_node gnc 
        INNER JOIN global_node_hierarchy gnh ON gnc.id = gnh.child_node_id 
        WHERE gnc.node_type = 'CHEMICAL' 
        AND gnh.parent_node_id = :id
        """
        )
        return self.session.execute(query, {"id": id}).scalars().all()
