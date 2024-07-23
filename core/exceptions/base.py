class APIError(Exception):
    """Base class for API exceptions"""

    pass


class StealEnergyError(APIError):
    """Raised when failed to steal energy"""

    pass
