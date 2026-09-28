"""Start with `python -m searchmedia`."""

import uvicorn

from searchmedia.config import config_from_env

# Keep this as an import string so Uvicorn can reload the app.
APP = "searchmedia.server:app"

# Watch only application code, not the virtual environment.
RELOAD_DIRS = ["searchmedia"]


def main() -> None:
    config = config_from_env()

    uvicorn.run(
        APP,
        host=config.host,
        port=config.port,
        reload=config.reload,
        reload_dirs=RELOAD_DIRS if config.reload else None,
    )


# Prevent the server from starting when this module is imported by the reloader.
if __name__ == "__main__":
    main()
