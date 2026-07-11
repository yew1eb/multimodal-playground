#!/usr/bin/env python3
"""A tiny mock Gravitino server for local script testing.

This is NOT a real Gravitino server. It only implements the minimal REST endpoints
required by `bootstrap_gravitino.py` so that the bootstrap logic can be exercised
without a full Gravitino deployment.
"""
from __future__ import annotations

import json
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer


class Store:
    metalakes: dict[str, dict] = {}
    catalogs: dict[str, dict] = defaultdict(dict)
    schemas: dict[str, dict] = defaultdict(dict)
    filesets: dict[str, dict] = defaultdict(dict)


def _path_parts(path: str) -> list[str]:
    return [p for p in path.split("/") if p]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # noqa: ANN002
        print(f"[mock] {fmt % args}")

    def _send_json(self, status: int, body: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/vnd.gravitino.v1+json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self) -> None:  # noqa: N802
        parts = _path_parts(self.path)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "metalakes":
            name = parts[2]
            if name in Store.metalakes:
                self._send_json(200, {"code": 0, "metalake": Store.metalakes[name]})
            else:
                self._send_json(404, {"code": 404, "message": "not found"})
            return

        if len(parts) == 5 and parts[3] == "catalogs":
            metalake, catalog = parts[2], parts[4]
            if catalog in Store.catalogs[metalake]:
                self._send_json(200, {"code": 0, "catalog": Store.catalogs[metalake][catalog]})
            else:
                self._send_json(404, {"code": 404, "message": "not found"})
            return

        if len(parts) == 7 and parts[3] == "catalogs" and parts[5] == "schemas":
            metalake, catalog, schema = parts[2], parts[4], parts[6]
            if schema in Store.schemas[f"{metalake}.{catalog}"]:
                self._send_json(200, {"code": 0, "schema": Store.schemas[f"{metalake}.{catalog}"][schema]})
            else:
                self._send_json(404, {"code": 404, "message": "not found"})
            return

        if len(parts) == 9 and parts[3] == "catalogs" and parts[5] == "schemas" and parts[7] == "filesets":
            metalake, catalog, schema, fileset = parts[2], parts[4], parts[6], parts[8]
            key = f"{metalake}.{catalog}.{schema}"
            if fileset in Store.filesets[key]:
                self._send_json(200, {"code": 0, "fileset": Store.filesets[key][fileset]})
            else:
                self._send_json(404, {"code": 404, "message": "not found"})
            return

        self._send_json(404, {"code": 404, "message": "unsupported GET"})

    def do_POST(self) -> None:  # noqa: N802
        parts = _path_parts(self.path)
        body = self._read_body()

        if len(parts) == 2 and parts[0] == "api" and parts[1] == "metalakes":
            name = body["name"]
            Store.metalakes[name] = {"name": name, "comment": body.get("comment", "")}
            self._send_json(201, {"code": 0, "metalake": Store.metalakes[name]})
            return

        if len(parts) == 4 and parts[3] == "catalogs":
            metalake = parts[2]
            name = body["name"]
            Store.catalogs[metalake][name] = {
                "name": name,
                "type": body.get("type"),
                "provider": body.get("provider"),
                "comment": body.get("comment", ""),
                "properties": body.get("properties", {}),
            }
            self._send_json(201, {"code": 0, "catalog": Store.catalogs[metalake][name]})
            return

        if len(parts) == 6 and parts[3] == "catalogs" and parts[5] == "schemas":
            metalake, catalog = parts[2], parts[4]
            name = body["name"]
            key = f"{metalake}.{catalog}"
            Store.schemas[key][name] = {
                "name": name,
                "comment": body.get("comment", ""),
                "properties": body.get("properties", {}),
            }
            self._send_json(201, {"code": 0, "schema": Store.schemas[key][name]})
            return

        if len(parts) == 8 and parts[3] == "catalogs" and parts[5] == "schemas" and parts[7] == "filesets":
            metalake, catalog, schema = parts[2], parts[4], parts[6]
            name = body["name"]
            key = f"{metalake}.{catalog}.{schema}"
            Store.filesets[key][name] = {
                "name": name,
                "comment": body.get("comment", ""),
                "type": body.get("type"),
                "properties": body.get("properties", {}),
            }
            self._send_json(201, {"code": 0, "fileset": Store.filesets[key][name]})
            return

        self._send_json(404, {"code": 404, "message": "unsupported POST"})


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8090), Handler)
    print("[mock] Starting mock Gravitino server on http://127.0.0.1:8090")
    print("[mock] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[mock] Stopping")


if __name__ == "__main__":
    main()
