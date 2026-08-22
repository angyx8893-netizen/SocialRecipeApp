from . import main_legacy as legacy
from .meta_facebook import META_GRAPH_VERSION, configured as meta_configured, patch_legacy

patch_legacy(legacy)

from .main_legacy import *  # noqa: F401,F403,E402
from .image_routes import register_image_routes  # noqa: E402

app.version = "3.5.0"

# Sostituisce il vecchio /health con una risposta che include lo stato Meta.
app.router.routes = [
    route for route in app.router.routes
    if not (getattr(route, "path", None) == "/health" and "GET" in (getattr(route, "methods", set()) or set()))
]


@app.get("/health")
def health_v35():
    data = legacy.health()
    data["version"] = "3.5.0"
    data["metaOembedConfigured"] = meta_configured()
    data["metaGraphVersion"] = META_GRAPH_VERSION
    return data


register_image_routes(
    app=app,
    ImportResponse=ImportResponse,
    openai_client=openai_client,
    require_key=require_key,
    model=OPENAI_MODEL,
    clean=clean,
)
