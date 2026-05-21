import os
import re
from urllib.parse import urlparse

from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


# Paths that are eligible for the workspace-scoped CORS allowlist. These
# are the routes a different-origin frontend needs in order to mint the
# workspace session cookie and load workspace artifacts via fetch():
#   - POST/DELETE /api/auth/workspace-session
#   - GET /api/conversations/{conversation_id}/workspace/...
_WORKSPACE_SESSION_PATH = "/api/auth/workspace-session"
_WORKSPACE_STATIC_RE = re.compile(r"^/api/conversations/[^/]+/workspace(/|$)")


def _is_workspace_scoped_path(path: str) -> bool:
    if path == _WORKSPACE_SESSION_PATH:
        return True
    return bool(_WORKSPACE_STATIC_RE.match(path))


class LocalhostCORSMiddleware(CORSMiddleware):
    """Custom CORS middleware that allows any request from localhost/127.0.0.1 domains.

    Also allows the DOCKER_HOST_ADDR IP, while using standard CORS rules for
    other origins.
    """

    def __init__(self, app: ASGIApp, allow_origins: list[str]) -> None:
        super().__init__(
            app,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def is_allowed_origin(self, origin: str) -> bool:
        if origin and not self.allow_origins and not self.allow_origin_regex:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ""

            # Allow any localhost/127.0.0.1 origin regardless of port
            if hostname in ["localhost", "127.0.0.1"]:
                return True

            # Also allow DOCKER_HOST_ADDR if set (for remote browser access)
            docker_host_addr = os.environ.get("DOCKER_HOST_ADDR")
            if docker_host_addr and hostname == docker_host_addr:
                return True

        # For missing origin or other origins, use the parent class's logic
        result: bool = super().is_allowed_origin(origin)
        return result


class WorkspaceScopedCORSMiddleware:
    """Path-scoped CORS dispatcher.

    Wraps two ``LocalhostCORSMiddleware`` instances and routes each request
    to one of them based on the URL path:

    * Requests targeting the workspace-session auth endpoint and the
      workspace static-file router are handled by a middleware whose
      allowlist is the union of ``allow_origins`` and
      ``allow_workspace_origins``. This lets a different-origin frontend
      mint the cookie and fetch workspace artifacts.
    * All other requests are handled by a middleware configured with only
      ``allow_origins`` — origins listed exclusively in
      ``allow_workspace_origins`` are NOT granted CORS access to the rest
      of the API.

    Each wrapped middleware delegates to the same downstream ``app``, so
    the actual request handling is unchanged; only the CORS headers and
    preflight handling differ between the two scopes.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        allow_origins: list[str],
        allow_workspace_origins: list[str],
    ) -> None:
        # Preserve order/uniqueness so the OpenAPI/debug output is stable.
        combined: list[str] = list(allow_origins)
        for origin in allow_workspace_origins:
            if origin not in combined:
                combined.append(origin)

        self._default_cors = LocalhostCORSMiddleware(
            app, allow_origins=list(allow_origins)
        )
        self._workspace_cors = LocalhostCORSMiddleware(app, allow_origins=combined)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") == "http" and _is_workspace_scoped_path(
            scope.get("path", "")
        ):
            await self._workspace_cors(scope, receive, send)
            return
        await self._default_cors(scope, receive, send)
