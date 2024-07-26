from enum import Enum


class NodeUseSubType(str, Enum):
    NONE = "NONE"
    INDIRECT = "INDIRECT"
    PACKLAYER = "PACKLAYER"
