import typer

from src.cli.download_avatars_cli import download_avatars, download_multiple_avatars


app = typer.Typer(help="App cli commands")


@app.callback()
def main() -> None:
    pass


app.command(name="download_avatars")(download_avatars)
app.command(name="download_multiple_avatars")(download_multiple_avatars)

if __name__ == "__main__":
    app()
