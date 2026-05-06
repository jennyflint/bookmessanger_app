from authlib.integrations.starlette_client import OAuth

from src.settings.settings import auth_settings


oauth = OAuth()

oauth.register(
    name="google",
    client_id=auth_settings.google_oauth_client_id,
    client_secret=auth_settings.google_oauth_client_secret,
    server_metadata_url=auth_settings.google_server_metadata_url,
    client_kwargs=auth_settings.google_client_kwargs,
)
