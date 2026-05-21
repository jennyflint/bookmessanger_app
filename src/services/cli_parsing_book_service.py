class CliParsingBookService:
    @staticmethod
    def default_command_parsing_book(
        path_to_book: str, path_to_save: str
    ) -> dict[str, str | bool | int]:
        return {
            "file": path_to_book,
            "log_mode": False,
            "save": path_to_save,
            "short": True,
        }
