from enum import Enum

class InformationSource(str, Enum):
    MANUAL = "MANUAL"
    VAI = "VAI"
    OECD = "OECD"
    ECHA = "ECHA"
    NONE = "NONE"
