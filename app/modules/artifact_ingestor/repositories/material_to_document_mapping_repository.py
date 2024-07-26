from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.artifact_ingestor.models.material_to_document_mapping import (
    MaterialToDocumentMapping,
    MaterialToDocumentCompositeKey,
)


class MaterialToDocumentMappingRepo:
    def __init__(self, session: Session):
        self.session = session

    def save(self, mapping: MaterialToDocumentMapping) -> MaterialToDocumentMapping:
        self.session.add(mapping)
        return mapping

    def find_by_id(self, id: str) -> Optional[MaterialToDocumentMapping]:
        stmt = select(MaterialToDocumentMapping).where(
            MaterialToDocumentMapping.id.documentMetadata.id == id
        )
        result = self.session.execute(stmt).scalars().first()
        return result

    def delete_by_id(self, id: MaterialToDocumentCompositeKey) -> None:
        mapping = (
            self.session.query(MaterialToDocumentMapping)
            .filter(MaterialToDocumentMapping.id == id)
            .first()
        )
        if mapping:
            self.session.delete(mapping)
            self.session.commit()

    def find_all_by_material_node(self, id: str) -> List[MaterialToDocumentMapping]:
        stmt = select(MaterialToDocumentMapping).where(
            MaterialToDocumentMapping.id.materialNode.id == id
        )
        result = self.session.execute(stmt).scalars().all()
        return result
