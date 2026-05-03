class HtmlTagNotFoundError(Exception):
    def __init__(self, message: str = "HTML tag not found"):
        self.message = message
        super().__init__(self.message)
