from sqlalchemy import create_engine, String, Column, Integer, Text, JSON, BigInteger, Boolean
import uuid
from common.mysql_declarative_base import Base
from pgvector.sqlalchemy import Vector


class Vector(Base):
    __tablename__ = 'vectors'
    id = Column(String(64), primary_key=True, default=str(uuid.uuid4()).replace('-', ''))
    embedding = Column(Vector(3072), nullable=False)
    enabled = Column(Integer)
    genre = Column(String)
    question = Column(String)
    sql = Column(Text)
    text = Column(Text)
    realm = Column(String, nullable=False)
    tenant_id = Column(String)
    file_id = Column('fileId', String)
    source = Column(String)
    page_number = Column(Integer)
    file_name = Column('fileName', String)
    source_link = Column('sourceLink', String)
    data_format = Column('dataFormat', String)
    status = Column(String)
    category = Column(String)
    type = Column(String)
    trust_factor = Column('trustFactor', String)
    region = Column(String)
    country = Column(String)
    state = Column(String)
    city = Column(String)
    domain = Column(String)
    sub_domain = Column('subDomain', String)
