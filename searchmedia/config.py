"""Settings from environment variables, all prefixed SEARCHMEDIA_."""

import os
from dataclasses import dataclass

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 80
# Disabled by default to avoid running the file watcher in production.
DEFAULT_RELOAD = False
# Goes into error.help.
DEFAULT_SPECIFICATION_URL = "/api/searchmedia/v1/swagger/"
# TODO: add rate-limit documentation.
DEFAULT_DOCUMENTATION_URL = "/api/searchmedia/v1/doc/"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    reload: bool
    specification_url: str
    documentation_url: str
    # Empty when not set. The app still starts; the service just answers with an error and shows up as unavailable.
    giphy_key: str
    klipy_key: str
    google_key: str
    google_cx: str


def config_from_env() -> Config:
    return Config(
        host=os.getenv("SEARCHMEDIA_HOST") or DEFAULT_HOST,
        port=int(os.getenv("SEARCHMEDIA_PORT") or DEFAULT_PORT),
        reload=_bool_from_env("SEARCHMEDIA_RELOAD", DEFAULT_RELOAD),
        specification_url=os.getenv("SEARCHMEDIA_SPECIFICATION_URL")
        or DEFAULT_SPECIFICATION_URL,
        documentation_url=os.getenv("SEARCHMEDIA_DOCUMENTATION_URL")
        or DEFAULT_DOCUMENTATION_URL,
        giphy_key=os.getenv("SEARCHMEDIA_GIPHY_KEY", ""),
        klipy_key=os.getenv("SEARCHMEDIA_KLIPY_KEY", ""),
        google_key=os.getenv("SEARCHMEDIA_GOOGLE_KEY", ""),
        google_cx=os.getenv("SEARCHMEDIA_GOOGLE_CX", ""),
    )


def _bool_from_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)

    if not raw:
        return default

    return raw.strip().lower() in _TRUTHY
