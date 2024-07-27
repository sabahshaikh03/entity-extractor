from enum import Enum

class NodeUseType(str, Enum):
    UNKNOWN = 'UNKNOWN'
    DIRECT = 'DIRECT'
    INDIRECT = 'INDIRECT'
    PACKAGING = 'PACKAGING'