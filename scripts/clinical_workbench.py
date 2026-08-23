#!/usr/bin/env python3
"""Serve the local, in-memory clinical calculator case workbench."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sys
from typing import Any
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clinical_calculators.workbench import calculate_selected, recommend_for_case  # noqa: E402


WEB_ROOT = ROOT / "workbench_web"
MAX_BODY_BYTES = 1_000_000


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "ClinicalWorkbench/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        # Do not place case URLs or payload-adjacent details in access logs.
        return

    def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _static_target(self) -> Path | None:
        clean_path = self.path.split("?", 1)[0]
        if clean_path in {"", "/"}:
            target = WEB_ROOT / "index.html"
        elif clean_path.startswith("/assets/"):
            target = ROOT / clean_path.lstrip("/")
        else:
            target = WEB_ROOT / clean_path.lstrip("/")
        try:
            target.resolve().relative_to(ROOT.resolve())
        except ValueError:
            return None
        return target if target.is_file() else None

    def _serve_static(self, *, include_body: bool) -> None:
        target = self._static_target()
        if target is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type,
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("无效的请求长度") from exc
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError("请求为空或超过 1 MB")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError("请求必须是有效 JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("请求 JSON 必须是对象")
        return payload

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/api/recommend":
                response = recommend_for_case(
                    str(payload.get("query", "")),
                    str(payload.get("case_text", "")),
                    supplied_values=payload.get("values") or {},
                    limit=payload.get("limit", 6),
                )
            elif self.path == "/api/calculate":
                inputs = payload.get("calculator_inputs")
                if not isinstance(inputs, dict):
                    raise ValueError("calculator_inputs 必须是对象")
                response = calculate_selected(
                    inputs,
                    session_id=str(payload.get("session_id", "")),
                )
            else:
                self._json({"error": "接口不存在"}, HTTPStatus.NOT_FOUND)
                return
            self._json(response)
        except ValueError as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self._json({"error": "服务内部错误，病例数据未保存"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._json({"status": "ok", "storage": "memory_only"})
            return
        self._serve_static(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._serve_static(include_body=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="open the workbench in the default browser")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), WorkbenchHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Clinical Calculator Workbench: {url}")
    print("Case data is processed in memory and is not written to disk.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
