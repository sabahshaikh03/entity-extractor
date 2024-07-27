from logging import Logger
from sqlalchemy.orm import Session
from global_constants import GlobalConstants
from common.models.vector import Vector
import uuid

global_constants = GlobalConstants

class VectorRepository:

    def __init__(self, logger: Logger, session: Session):
        self.logger = logger
        self.session = session

    # Stores embeddings, text chunks and artifact metadata into vector store
    def create_vector_embeddings(self, artifact, text_chunks, embedding_vectors):
        # TODO: if exists, delete and insert vectors
        try:
            vector_records = []
            for page_number, (text_chunk, embedding) in enumerate(zip(text_chunks, embedding_vectors)):
                vector = Vector(
                    id=str(uuid.uuid4()).replace('-', ''),
                    genre='PFAS',  # todo: remove hardcoding
                    realm=artifact.realm,  # todo: remove hardcoding
                    tenant_id='1',  # todo: remove hardcoding
                    # metadata2=text_chunk.metadata,
                    embedding=embedding,
                    enabled=1,
                    text=text_chunk.page_content,
                    file_id=artifact.id,
                    source=artifact.source_name,
                    page_number=page_number,
                    file_name=artifact.name,
                    source_link=artifact.source_link,
                    data_format=artifact.data_format,
                    status=artifact.status,
                    category=artifact.category_id,
                    type=artifact.type_id,
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
            print("Added to vectors table!")
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.exception(f"PGVECTOR-UTIL : Error: {e}")

    def retrieve_relevant_documents(self, artifact_id, query_embedding):
        try:
            docs = self.session.query(Vector.text).filter(Vector.file_id == artifact_id).order_by(Vector.embedding.l2_distance(query_embedding)).limit(5).all()
            doc_contents = [doc.text for doc in docs]
            if not doc_contents:
                self.logger.warning(f"PGVECTOR-UTIL : Embeddings not found for artifact id {artifact_id}")
                return None
            self.logger.info(f"PGVECTOR-UTIL : Embeddings for artifact id {artifact_id} retrieved successfully")
            return doc_contents
        except Exception as e:
            self.logger.exception(f"PGVECTOR-UTIL : Error: {e}")
            return None

