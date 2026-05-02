class AuthError(Exception):
    def __init__(self, message: str = "Authorization error"):
        self.message = message
        super().__init__(self.message)


class EmailAuthError(AuthError):
    def __init__(self, message: str = "Email is required from Google Auth"):
        super().__init__(message)
