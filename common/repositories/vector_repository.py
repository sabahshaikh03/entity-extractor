# TODO: utility to access pgvector vector db data
from logging import Logger
from sqlalchemy.orm import Session
from global_constants import GlobalConstants

from common.models.vector import Vector

global_constants = GlobalConstants


class VectorRepository:

    def __init__(self, logger: Logger, session: Session):
        self.session = session
        self.logger = logger

    # Stores embeddings, text chunks and artifact metadata into vector store
    def create_vector_embeddings(self, artifact, text_chunks, embedding_vectors):
        # TODO: if exists, delete and insert vectors
        try:
            vector_records = []
            for page_number, (text_chunk, embedding) in enumerate(zip(text_chunks, embedding_vectors)):
                vector = Vector(genre='PFAS',  # todo: remove hardcoding
                                realm='dummy-realm',  # todo: remove hardcoding
                                tenant_id='1',  # todo: remove hardcoding
                                metadata2=text_chunk.metadata,
                                embedding=embedding,
                                enabled=global_constants.enabled_flag,
                                text=text_chunk.page_content,
                                file_id=artifact.id,
                                source=artifact.source,
                                page_number=page_number,
                                file_name=artifact.file_name,
                                source_link=artifact.sourceLink,
                                data_format=artifact.dataFormat,
                                status=artifact.status,
                                category=artifact.category,
                                type=artifact.type,
                                trust_factor=artifact.trust_factor,
                                region=artifact.region,
                                country=artifact.country,
                                state=artifact.state,
                                city=artifact.city,
                                domain=artifact.domain,
                                sub_domain=artifact.sub_domain
                                )
                vector_records.append(vector)

            self.session.add_all(vector_records)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.exception(f"PGVECTOR-UTIL : Error: {e}")

    def retrieve_embeddings(self, artifact_id, query_embeddings):
        try:
            docs = self.session.query(Vector.text).filter(artifact_id).order_by(Vector.embedding.l2_distance(query_embeddings)).all()

            doc_contents = [doc.text for doc in docs]

            if doc_contents is None or len(doc_contents) == 0:
                self.logger.warning(f"PGVECTOR-UTIL : Embeddings not found for artifact id  {artifact_id}")
                return None
            self.logger.info(f"PGVECTOR-UTIL : Embeddings for artifact id {artifact_id} retrieved successfully")
            return doc_contents
        except Exception as e:
            self.logger.exception(f"PGVECTOR-UTIL : Error: {e}")
            return None
