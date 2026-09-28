from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse

from searchmedia import service as search_service
from searchmedia.client import HttpClient
from searchmedia.config import Config, config_from_env
from searchmedia.envelope import error_body, meta_body, pagination
from searchmedia.query import InvalidSearchQuery, read_query
from searchmedia.throttle import RequestThrottle, RequestTooSoon

AVAILABLE_SERVICE_NAMES = ("klipy", "google", "giphy")
ITEMS_LIMIT = 30
SERVICE_NAMES_PATH = "/api/v1/searchmedia/service-names"
SEARCH_PATH = "/api/v1/searchmedia"
JSON_MEDIA_TYPE = "application/json; charset=UTF-8"
SERVICE_TIMEOUT_SECONDS = 5.0

app = FastAPI(
    title="Search Media API",
    docs_url="/api/searchmedia/v1/swagger/",
    redoc_url=None,
    openapi_url="/openapi.json",
    redirect_slashes=False,
)

# Kept on app.state rather than in module globals, so a test can replace them (app.state.config = ...) without monkeypatching the module.
app.state.config = config_from_env()
app.state.client = HttpClient(SERVICE_TIMEOUT_SECONDS)
app.state.throttle = RequestThrottle()


def get_config(request: Request) -> Config:
    return request.app.state.config


def get_client(request: Request) -> HttpClient:
    return request.app.state.client


def get_throttle(request: Request) -> RequestThrottle:
    return request.app.state.throttle


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.get(SERVICE_NAMES_PATH)
def service_names(request: Request) -> JSONResponse:
    body = meta_body(200, request_id=request.state.request_id)
    body["data"] = list(AVAILABLE_SERVICE_NAMES)

    return JSONResponse(body, media_type=JSON_MEDIA_TYPE)


@app.get(SEARCH_PATH)
def search(
    request: Request,
    # Some parameters only describe the query string for OpenAPI. 
    # The real parsing is done by read_query(), which keeps the API's own validation and its handling of repeated keys.
    text: Annotated[
        str | None,
        Query(description="Search text. Give the key once: `?text=a&text=b` is answered with 400."),
    ] = None,
    service: Annotated[
        list[str] | None,
        Query(
            description="Search service names to query, one per repetition of the key: "
            "`service=klipy&service=giphy`. Absent means every service."
        ),
    ] = None,
    limit: Annotated[
        str | None, Query(description="Number of items to retrieve per page.")
    ] = None,
    offset: Annotated[str | None, Query(description="Offset for pagination.")] = None,
    config: Config = Depends(get_config),
    client: HttpClient = Depends(get_client),
    throttle: RequestThrottle = Depends(get_throttle),
) -> JSONResponse:
    try:
        throttle.throttle_by_ip(_client_ip(request))
    except RequestTooSoon:
        return _error(request, 429, "Too Many Requests", config, help_url=config.documentation_url)

    try:
        query = read_query(request.query_params, AVAILABLE_SERVICE_NAMES, ITEMS_LIMIT)
    except InvalidSearchQuery as invalid:
        return _error(request, 400, str(invalid), config)

    items, meta = search_service.search(client, config, query, AVAILABLE_SERVICE_NAMES)

    body = meta_body(
        200,
        request_id=request.state.request_id,
        meta=meta,
        pagination=pagination(limit=query.limit, offset=query.offset, items_count=len(items)),
    )
    body["data"] = items

    return JSONResponse(body, media_type=JSON_MEDIA_TYPE)


def _error(
    request: Request, code: int, message: str, config: Config, *, help_url: str | None = None
) -> JSONResponse:
    body = error_body(
        code,
        request_id=request.state.request_id,
        message=message,
        help_url=help_url if help_url is not None else config.specification_url,
    )

    return JSONResponse(body, status_code=code, media_type=JSON_MEDIA_TYPE)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""