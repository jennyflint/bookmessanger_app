import time
from secrets import choice
from string import ascii_lowercase

import requests
import typer

from src.services.storage_avatar_service import StorageAvatarService


SIZE = 256
FILE_FORMAT = "png"


def download_avatars(count: int = 100, style: str = "adventurer") -> None:

    storage_service = StorageAvatarService()

    for _i in range(count):
        ts = int(time.time())
        random_char = "".join(choice(ascii_lowercase) for i in range(5))
        seed = f"{style}_{ts}_{random_char}"
        url = (
            f"https://api.dicebear.com/9.x/"
            f"{style}/{FILE_FORMAT}?seed={seed}&size={SIZE}"
        )

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            storage_service.save(f"{seed}.{FILE_FORMAT}", response.content, style)
            typer.echo(f"Downloaded {seed}.{FILE_FORMAT}")
        else:
            typer.echo(f"Error {seed}.{FILE_FORMAT}")
        time.sleep(0.3)


def download_multiple_avatars(count: int = 100) -> None:
    styles = (
        "adventurer",
        "avataaars",
        "big-ears",
        "big-smile",
        "bottts",
        "bottts-neutral",
        "croodles",
        "dylan",
        "lorelei",
        "micah",
        "miniavs",
        "notionists",
        "open-peeps",
        "personas",
        "pixel-art",
        "toon-head",
    )
    for style in styles:
        download_avatars(count, style)
