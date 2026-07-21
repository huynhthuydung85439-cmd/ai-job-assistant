"""Validate the CloudBase runtime without importing optional RAG packages."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

FORBIDDEN_IMPORTS = (
    "chromadb",
    "langchain_chroma",
    "langchain_huggingface",
    "onnxruntime",
    "sentence_transformers",
    "torch",
    "transformers",
    "triton",
)

FORBIDDEN_DISTRIBUTIONS = {
    "chromadb",
    "langchain-chroma",
    "langchain-huggingface",
    "onnxruntime",
    "sentence-transformers",
    "torch",
    "transformers",
    "triton",
}

ORDINARY_FEATURE_MODULES = (
    "app.api.v1.endpoints.chat",
    "app.routers.auth",
    "app.routers.history",
    "app.routers.resume",
    "app.services.auth",
    "app.services.chat",
    "app.services.pdf_parser",
    "app.services.resume_analyzer",
)

ALEMBIC_RUNTIME_PATHS = (
    "alembic.ini",
    "migrations/env.py",
    "migrations/script.py.mako",
    "migrations/versions",
)


def normalized_distribution_name(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def find_forbidden_distributions() -> list[str]:
    installed = {
        normalized_distribution_name(distribution.metadata["Name"])
        for distribution in metadata.distributions()
        if distribution.metadata["Name"]
    }
    return sorted(
        name
        for name in installed
        if name in FORBIDDEN_DISTRIBUTIONS or name.startswith("nvidia-") or "cuda" in name
    )


def find_imported_rag_modules() -> list[str]:
    return sorted(
        module_name
        for module_name in sys.modules
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_IMPORTS
        )
    )


def find_missing_alembic_runtime_paths(root: Path | None = None) -> list[str]:
    runtime_root = root or Path.cwd()
    return [path for path in ALEMBIC_RUNTIME_PATHS if not (runtime_root / path).exists()]


def collect_route_paths(routes: list[Any], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    for route in routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            include_context = getattr(route, "include_context", None)
            route_prefix = getattr(include_context, "prefix", "")
            paths.update(collect_route_paths(original_router.routes, f"{prefix}{route_prefix}"))
            continue

        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            route_prefix = getattr(route, "prefix", "")
            paths.update(collect_route_paths(nested_routes, f"{prefix}{route_prefix}"))
            continue

        route_path = getattr(route, "path", None)
        if isinstance(route_path, str):
            paths.add(f"{prefix}{route_path}")
    return paths


async def call_asgi(application: Any, method: str, path: str) -> tuple[int, dict[str, Any]]:
    response_start: dict[str, Any] = {}
    response_body = bytearray()
    request_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            response_start.update(message)
        elif message["type"] == "http.response.body":
            response_body.extend(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"cloud-runtime-check")],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }
    await application(scope, receive, send)
    return int(response_start["status"]), json.loads(response_body)


async def validate(require_absent: bool) -> dict[str, Any]:
    missing_alembic_paths = find_missing_alembic_runtime_paths()
    if missing_alembic_paths:
        raise AssertionError(
            "Cloud image is missing Alembic runtime paths: " + ", ".join(missing_alembic_paths)
        )

    main_module = importlib.import_module("app.main")
    application = main_module.app

    for module_name in ORDINARY_FEATURE_MODULES:
        importlib.import_module(module_name)

    route_paths = collect_route_paths(application.routes)
    health_path = "/api/v1/health"
    if health_path not in route_paths:
        raise AssertionError(
            f"Health route is not registered: {health_path}; routes={sorted(route_paths)}"
        )

    status_code, response = await call_asgi(
        application,
        "POST",
        "/api/v1/knowledge/warmup",
    )
    if status_code != 503 or response.get("code") != "rag_disabled":
        raise AssertionError(
            "Disabled RAG endpoint must return 503/rag_disabled, "
            f"got {status_code}/{response.get('code')}"
        )

    imported_rag_modules = find_imported_rag_modules()
    if imported_rag_modules:
        raise AssertionError(
            "Cloud startup imported optional RAG modules: " + ", ".join(imported_rag_modules)
        )

    forbidden_distributions = find_forbidden_distributions() if require_absent else []
    if forbidden_distributions:
        raise AssertionError(
            "Cloud image contains forbidden distributions: " + ", ".join(forbidden_distributions)
        )

    return {
        "app_import": "ok",
        "health_route": health_path,
        "rag_disabled_response": f"{status_code}/{response['code']}",
        "ordinary_feature_imports": "ok",
        "forbidden_rag_imports": imported_rag_modules,
        "forbidden_distributions": forbidden_distributions,
        "alembic_runtime_paths": "ok",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-absent",
        action="store_true",
        help="Also fail if optional RAG/CUDA packages are installed.",
    )
    arguments = parser.parse_args()
    print(json.dumps(asyncio.run(validate(arguments.require_absent)), indent=2))


if __name__ == "__main__":
    main()
