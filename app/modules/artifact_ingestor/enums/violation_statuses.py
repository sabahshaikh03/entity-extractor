from enum import Enum

class ViolationStatus(str, Enum):
    YES = "YES"
    NO = "NO"
    PENDING = "PENDING"

