"""How the requested limit is split between services."""

from collections.abc import Mapping, Sequence


class ServiceLimitPlan:
    def __init__(self, limits: Mapping[str, int]) -> None:
        self._limits = dict(limits)

    @classmethod
    def for_request(
        cls,
        available_service_names: Sequence[str],
        requested_service_names: Sequence[str] | None,
        limit: int,
    ) -> "ServiceLimitPlan":
        if requested_service_names is None:
            names = list(available_service_names)
        else:
            names = []
            for name in available_service_names:
                if name in requested_service_names:
                    names.append(name)

        if not names:
            return cls({})

        per_service, remainder = divmod(limit, len(names))

        limits = {}
        for index, name in enumerate(names):
            limits[name] = per_service + (1 if index < remainder else 0)

        return cls(limits)

    def limit_for(self, service_name: str) -> int:
        return self._limits.get(service_name, 0)
