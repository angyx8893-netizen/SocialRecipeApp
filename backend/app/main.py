from .main_legacy import *  # noqa: F401,F403
from .image_routes import register_image_routes

app.version = "3.3.0"
register_image_routes(
    app=app,
    ImportResponse=ImportResponse,
    openai_client=openai_client,
    require_key=require_key,
    model=OPENAI_MODEL,
    clean=clean,
)
