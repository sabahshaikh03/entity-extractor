
from enum import Enum

class PfasInformationSource(str, Enum):
    MANUAL = "MANUAL"
    VAI = "VAI"
    OECD = "OECD"
    ECHA = "ECHA"
    NONE = "NONE"
    