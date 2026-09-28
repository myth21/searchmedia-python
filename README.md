# Search Media API

A media search service in Python (FastAPI + Uvicorn). It searches GIFs and images in Klipy, Giphy and Google Custom Search at once and answers with a single JSON envelope.

## Endpoints

| Route | What it does |
|---|---|
| `GET /api/v1/searchmedia` | Search. At most one request per 5 seconds from one IP |
| `GET /api/v1/searchmedia/service-names` | List of available services |
| `GET /api/searchmedia/v1/swagger/` | Swagger UI |
| `GET /openapi.json` | OpenAPI specification |

Search parameters:

| Parameter | Required | Description |
|---|---|---|
| `text` | yes | Search text, 1 to 32 characters. Given once |
| `service` | no | Service: `klipy`, `google` or `giphy`. Can be repeated: `service=klipy&service=giphy`. If absent, every service is queried |
| `limit` | no | How many items to return, 1 to 30. Defaults to 30 |
| `offset` | no | Pagination offset. Defaults to 0 |

Invalid parameters return `400`, too frequent requests return `429`. If one of the services fails, results from the others still come back.

Example:

```bash
curl 'http://127.0.0.1:8082/api/v1/searchmedia?text=cats&service=giphy&limit=5'
```

## Structure

```
.
├── Dockerfile
├── compose.yaml
├── .env.example                   template for .env
├── requirements-searchmedia.txt   dependencies
├── searchmedia/
│   ├── __main__.py    entry point: python -m searchmedia
│   ├── server.py      FastAPI app and routes
│   ├── config.py      settings from environment variables
│   ├── query.py       query string parsing and validation
│   ├── service.py     calls the services and builds the result
│   ├── plan.py        how the requested limit is split between services
│   ├── klipy.py, giphy.py, google.py   service requests and response mapping
│   ├── mapping.py     shared mapping helpers
│   ├── client.py      HTTP client for external APIs
│   ├── envelope.py    JSON response envelope
│   └── throttle.py    per-IP rate limiting
└── tests/             unit tests and their fixtures
```

## Configuration

All settings come from environment variables prefixed with `SEARCHMEDIA_`.

| Variable | Default | Description |
|---|---|---|
| `SEARCHMEDIA_HOST` | `0.0.0.0` | Address the server listens on |
| `SEARCHMEDIA_PORT` | `80` | Port |
| `SEARCHMEDIA_RELOAD` | `false` | Restart on code changes. Development only |
| `SEARCHMEDIA_GIPHY_KEY` | - | Giphy key |
| `SEARCHMEDIA_KLIPY_KEY` | - | Klipy key |
| `SEARCHMEDIA_GOOGLE_KEY` | - | Google Custom Search key |
| `SEARCHMEDIA_GOOGLE_CX` | - | Google search engine ID (cx) |
| `SEARCHMEDIA_SPECIFICATION_URL` | `/api/searchmedia/v1/swagger/` | Specification link in error bodies |
| `SEARCHMEDIA_DOCUMENTATION_URL` | `/api/searchmedia/v1/doc/` | Documentation link in `429` error bodies |
| `SEARCHMEDIA_HOST_PORT` | `8082` | Port on your machine. Read only by `compose.yaml`, not by the app |

The app starts even without keys. A service without a key just answers with an error and is marked as unavailable.

## Running in Docker

Copy `.env.example` to `.env` and fill in the keys (`.env` is in `.gitignore`):

```bash
cp .env.example .env
```

Build the image and start the service:

```bash
docker compose up -d --build
```

The API is available at `http://127.0.0.1:8082`, Swagger at `http://127.0.0.1:8082/api/searchmedia/v1/swagger/`.

The port on your machine is set by `SEARCHMEDIA_HOST_PORT` in `.env` (8082 if not set; the examples in this README use it). Inside the container the app always listens on 80. The service is reachable only from this machine; to open it to the network, remove `127.0.0.1:` from `ports` in `compose.yaml`.

Logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

For development, mount the code into the container and turn on reload, so changes are picked up without rebuilding:

```bash
docker compose run --rm --service-ports -e SEARCHMEDIA_RELOAD=true -v "$PWD":/var/www searchmedia
```

## Running locally

Requires Python 3.10 or newer (Docker uses 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-searchmedia.txt
```

```bash
set -a; source .env; set +a
SEARCHMEDIA_PORT=8000 SEARCHMEDIA_RELOAD=true python -m searchmedia
```

The first line loads the keys from `.env` into the environment. Without them the app still starts, but every service answers as unavailable.

Run it as a module, `python -m searchmedia`, from the repository root. Running `python searchmedia/__main__.py` breaks the package imports.

## Tests

The tests use the standard `unittest`, so no test framework needs to be installed, but the app's own dependencies do. They make no network requests: external API responses come from fixtures.

Locally, from the repository root, with the virtual environment from "Running locally" activated:

```bash
python -m unittest discover -s tests
```

In Docker (the image does not contain the tests, so the code is mounted):

```bash
docker compose run --rm -v "$PWD":/var/www searchmedia python -m unittest discover -s tests
```

A single file or a single test:

```bash
python -m unittest tests.test_query
```

```bash
python -m unittest tests.test_query.TextTest.test_missing_text_is_invalid
```

Fixtures are split by purpose:

- `tests/fixtures/recorded/` - real service responses. The mapping tests (`test_*_mapper.py`) check that the mappers handle them correctly.
- `tests/fixtures/edge-cases/` - hand-built responses with missing and `null` fields. Used by `test_*_defaults.py` and `test_service.py`.

## Known limitations

- Services are called one after another, not in parallel, with a 5 second timeout each. One request can hang for up to 15 seconds.
- Rate limit counters live in process memory. With several workers or replicas the "one request per 5 seconds" limit no longer holds.
