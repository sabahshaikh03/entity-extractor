from enum import Enum

class BlobStorageTypes(str, Enum):
    CUSTOMER = "CUSTOMER"
    GLOBAL = "GLOBAL"
    KEYWORD_ANALYSIS = "KEYWORD_ANALYSIS"


