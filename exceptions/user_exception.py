class UserInactiveError(Exception):
    def __init__(self, message: str = "This Account is deactivated."):
        super().__init__(message)
