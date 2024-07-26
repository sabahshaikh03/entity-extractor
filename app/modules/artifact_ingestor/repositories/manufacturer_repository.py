from sqlalchemy.ext.declarative import declarative_base
from app.modules.artifact_ingestor.models.manufacturer import Manufacturer
from sqlalchemy.orm import Session


Base = declarative_base()


class ManufacturerRepo:
    def __init__(self, session : Session):
        self.session = session
        
    def save(self, manufacturer : Manufacturer) -> Manufacturer:
        self.session.add(manufacturer)
        return manufacturer

    def find_by_name(self, name):
        return self.session.query(Manufacturer).filter(Manufacturer.name == name).all()

    def find_by_name_substring(self, name):
        return (
            self.session.query(Manufacturer)
            .filter(Manufacturer.name.like(f"%{name}%"))
            .all()
        )
        
