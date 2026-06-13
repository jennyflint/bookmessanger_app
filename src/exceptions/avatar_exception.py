from pathlib import Path


class AvatarFolderNotFoundError(Exception):
    def __init__(self, folder_path: Path):
        super().__init__(f"Error: Folder '{folder_path}' does not exist.")
