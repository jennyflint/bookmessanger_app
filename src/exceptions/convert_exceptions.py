class ConvertPdfError(Exception):
    def __init__(self, message: str = "Convert to PDF format failed"):
        self.message = message
        super().__init__(self.message)


class ConvertFormatNotImplementedError(Exception):
    def __init__(self, message: str = "Convert format not implemented"):
        self.message = message
        super().__init__(self.message)
