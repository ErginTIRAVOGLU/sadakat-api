from enum import Enum


class CustomerRewardStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    EXPIRED = "EXPIRED"