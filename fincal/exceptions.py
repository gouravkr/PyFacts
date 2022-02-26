class DateNotFoundError(Exception):
    """Exception to be raised when date is not found"""

    def __init__(self, message, date):
        message = f"{message}: {date}"
        super().__init__(message)
