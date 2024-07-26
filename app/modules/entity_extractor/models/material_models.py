from typing import List

from pydantic.v1 import BaseModel, Field

class Chemical(BaseModel):
    chemical_name: str = Field(description="Name of the chemical")
    tag: str = Field(description="Tag associated with the chemical")
    cas_no: str = Field(description="CAS Number of the chemical")
    composition: str = Field(description="Chemical composition of the chemical")
    ec_no: str = Field(description="EC Number of the chemical")


class Material(BaseModel):
    material_name: str = Field(description="Name of the material")
    material_no: str = Field(description="Number of the material")
    manufacturer_name: str = Field(description="Manufacturer's Name")
    manufacturer_address: str = Field(description="Manufacturer's Address")
    manufacturer_city: str = Field(description="Manufacturer's City")
    manufacturer_postal_code: str = Field(description="Manufacturer's Postal Code")
    manufacturer_country: str = Field(description="Manufacturer's Country")
    manufacturer_state: str = Field(description="Manufacturer's State")
    manufacturer_region: str = Field(description="Manufacturer's Region")
    cas_no: str = Field(description="CAS Number of the material")
    ec_no: str = Field(description="EC Number of the material")
    chemicals: List[Chemical] = Field(description="List of chemicals associated with the material")