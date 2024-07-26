from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from common.mysql_declarative_base import Base


class Manufacturer(Base):
    __tablename__ = 'manufacturer'

    id = Column(String, primary_key=True) 
    name = Column(String(244), nullable=False)
    address = Column(String)
    postal_code = Column(String(100))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    region = Column(String(100))
    
    global_nodes = relationship("GlobalNode", back_populates="manufacturer")

    # __table_args__ = (
    #     Index('manufacturer_name_index', 'name'),
    #     UniqueConstraint('name', 'address', 'postal_code', 'city', 'state', 'country'),
    # )