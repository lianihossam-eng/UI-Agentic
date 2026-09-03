"""Application adapter contract for external projects."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass(frozen=True)
class RouteTarget:
    route: str
    navigation_target: str
    code_digest: str


@dataclass(frozen=True)
class HttpAppAdapter:
    base_url: str
    project_digest: str
    routes: tuple[str, ...]

    def targets(self) -> dict[str, RouteTarget]:
        result: dict[str, RouteTarget] = {}
        base = self.base_url.rstrip("/") + "/"
        for route in self.routes:
            navigation_target = urljoin(base, route.lstrip("/"))
            route_digest = hashlib.sha256(
                f"{self.project_digest}\n{route}".encode("utf-8")
            ).hexdigest()[:12]
            result[route] = RouteTarget(route, navigation_target, route_digest)
        return result

    def navigation_targets(self) -> dict[str, str]:
        return {route: target.navigation_target for route, target in self.targets().items()}

    def code_digests(self) -> dict[str, str]:
        return {route: target.code_digest for route, target in self.targets().items()}
