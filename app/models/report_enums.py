from enum import Enum


class QueueLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class VehicleAvailability(str, Enum):
    available = "available"
    limited = "limited"
    unavailable = "unavailable"
