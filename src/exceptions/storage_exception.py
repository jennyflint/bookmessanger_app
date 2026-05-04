class FileNotExistError(Exception):
    def __init__(self, file_path: str):
        super().__init__(f"Error: File '{file_path}' does not exist.")
