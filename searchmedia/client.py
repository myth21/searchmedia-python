from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HttpResponse:
    # None means no response: wrong host, connection refused, or timeout.
    status_code: int | None
    body: str

    @classmethod
    def none(cls) -> "HttpResponse":
        return cls(None, "")

    def is_ok(self) -> bool:
        return self.status_code == 200


class HttpClient:
    def __init__(self, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise ValueError(f"Timeout must be greater than zero, got {timeout_seconds}.")

        self._timeout_seconds = timeout_seconds

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        request = Request(url, headers=headers or {}, method="GET")

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return HttpResponse(response.status, response.read().decode("utf-8", "replace"))
        except HTTPError as error:
            # Don't pass error responses to the mapper.
            return HttpResponse(error.code, "")
        except (URLError, TimeoutError, OSError):
            return HttpResponse.none()
