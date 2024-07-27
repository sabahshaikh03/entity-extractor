"""
This file contains the JSON schemas expected from the LLM for both, material composition analysis and material PFAS
analysis.
Pydantic helps in serializing structures defined in classes and makes it handy to convert them to an
OpenAI function call.
"""

from pydantic.v1 import BaseModel, Field


# ChemicalInfo and MaterialComposition classes are used for defining material composition schema
class ChemicalInfo(BaseModel):
    name: str = Field(description="Name of the chemical")
    cas_no: str = Field(description="CAS number of the chemical")
    source: str = Field(description="URL Source for this piece of information")


class MaterialComposition(BaseModel):
    product_name: str = Field(description="Name of the product specified")
    chemicals: list[ChemicalInfo] = Field(
        description="List of chemicals present in the product."
    )
    confidence: int = Field(description="Confidence score of the result")


# MaterialInfo class is used for defining material's PFAS analysis schema.
class MaterialInfo(BaseModel):
    analyzed_material: str = Field(description="Name of the material that was analyzed")
    composition: str = Field(description="Chemical composition of the material")
    analysis_method: str = Field(description="Method used for PFAS analysis")
    decision: str = Field(
        description="Decision of whether the material is PFAS compliant or not: PFAS (Yes/No)"
    )
    confidence: float = Field(description="Confidence score of response.")
    primary_reason: str = Field(description="Primary reasoning of response content.")
    secondary_reason: str = Field(
        description="Secondary reasoning of response content."
    )
    evidence: list[str] = Field(description="Evidence supporting the response given.")
    health_problems: list[str] = Field(
        description="List of health problems that could potentially be attached to the product."
    )
    confidence_level: str = Field(
        description="Confidence level of the response: low, medium, high"
    )
    recommendation: str = Field(
        description="Recommendation of what to do with the material with regards to its PFAS compliance."
    )
    suggestion: str = Field(
        description="Suggestion of what to do with the material with regards to its PFAS compliance."
    )
    limitations_and_uncertainties: str = Field(
        description="Limitations and uncertainties based on the data"
    )
