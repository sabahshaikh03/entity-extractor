from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import select, join
from typing import List
from app.modules.artifact_ingestor.models.global_node import GlobalNode
from app.modules.artifact_ingestor.models.manufacturer import Manufacturer
from app.modules.artifact_ingestor.models.document_metadata import DocumentMetadata
from app.modules.artifact_ingestor.dto.artifact_msds_material import (
    ArtifactMSDSMaterials,
)
from app.modules.artifact_ingestor.models.material_to_document_mapping import (
    MaterialToDocumentMapping,
)

Base = declarative_base()


class DocumentMetadataRepo:
    def __init__(self, session: Session):
        self.session = session
        
    def save(self,document_metadata : DocumentMetadata) -> DocumentMetadata:
        self.session.add(document_metadata)
        return document_metadata

    def find_by_name(self, name: str) -> List[DocumentMetadata]:
        return (
            self.session.query(DocumentMetadata)
            .filter(DocumentMetadata.name == name)
            .all()
        )

    def find_by_name_and_locator_and_document_type(
        self, name: str, blob_urls: str, document_type: str
    ) -> List[DocumentMetadata]:
        return (
            self.session.query(DocumentMetadata)
            .filter(
                DocumentMetadata.name == name,
                DocumentMetadata.locator == blob_urls,
                DocumentMetadata.document_type == document_type,
            )
            .all()
        )

    def get_all_msds_materials(self) -> List[ArtifactMSDSMaterials]:
        stmt = (
            select(
                GlobalNode.name,
                GlobalNode.pfas_status,
                GlobalNode.pfas_information_source,
                Manufacturer.name,
                DocumentMetadata.locator,
                DocumentMetadata.name,
                DocumentMetadata.document_type,
            )
            .select_from(
                join(
                    DocumentMetadata,
                    MaterialToDocumentMapping,
                    DocumentMetadata.id
                    == MaterialToDocumentMapping.document_metadata_id,
                ).join(
                    GlobalNode,
                    GlobalNode.id == MaterialToDocumentMapping.material_node_id,
                )
            )
            .distinct()
        )

        result = self.session.execute(stmt).fetchall()
        return [ArtifactMSDSMaterials(*row) for row in result]
