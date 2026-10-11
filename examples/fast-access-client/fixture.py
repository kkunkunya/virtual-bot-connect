#!/usr/bin/env python3
"""Synthetic HTTP/SSE fixture. No account, network service or credential required."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import tempfile
from threading import Thread
from datetime import datetime, timezone

from client import Cache, HTTP, consume, encode, sync

NOW = 1_800_000_000
SERVER = "https://service.example.invalid"
PRINCIPAL = "fixture-principal"
SCOPE = {"mode": "all_visible"}


def item(revision="1", kind="chat", ident="00000000-0000-4000-8000-000000000002", **extra):
    return {"workspace_id": "00000000-0000-4000-8000-000000000001", "workspace_name": "Example",
            "kind": kind, "id": ident, "revision": revision, "op": "upsert",
            "changed_at": datetime.fromtimestamp(NOW, timezone.utc).isoformat(),
            "title": "Example summary", "content_truncated": False,
            **({"unread_count": 3} if kind == "chat" else {}), **extra}


def page(checkpoint="read-1", changes=None, active=None, **extra):
    return {"schema_version": "1", "mode": "durable_delta",
            "as_of": datetime.fromtimestamp(NOW, timezone.utc).isoformat(),
            "coverage_from": datetime.fromtimestamp(NOW - 86400, timezone.utc).isoformat(),
            "retention_floor": datetime.fromtimestamp(NOW - 86400, timezone.utc).isoformat(),
            "scope_revision": "permission-1", "changes": [] if changes is None else changes,
            "active_runs": [] if active is None else active, "active_runs_complete": True,
            "complete": True, "next_cursor": None, "checkpoint": checkpoint, **extra}


class Script:
    def __init__(self, replies, frames=b""):
        self.replies, self.frames, self.requests = list(replies), frames, []

    def read(self, body):
        self.requests.append(body)
        response = self.replies.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@contextmanager
def serve(script):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            if self.path != "/api/fast-access/v1/read":
                self.send_error(404)
                return
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            try:
                value = script.read(body)
                status, data = 200, encode(value).encode()
            except Exception as error:
                status, data = getattr(error, "status", 500), encode({"code": str(error)}).encode()
                retry_after = getattr(error, "retry_after", 0)
            self.send_response(status)
            if status == 429:
                self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            script.requests.append({"event_path": self.path,
                                    "last_event_id": self.headers.get("Last-Event-ID")})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(script.frames)))
            self.end_headers()
            self.wfile.write(script.frames)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield HTTP("http://127.0.0.1:" + str(server.server_port), fixture=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def demo():
    frames = (b'event: change\ndata: {"event_id":"fixture-event"}\n\n' * 2
              + b'event: checkpoint\nid: stream-2\ndata: {}\n\n')
    script = Script([page(changes=[item()]),
                     page("read-2", [item("2", title="Updated summary", event_id="fixture-event")])],
                    frames)
    with tempfile.TemporaryDirectory() as directory, serve(script) as transport:
        cache = Cache(directory, SERVER, PRINCIPAL, SCOPE, clock=lambda: NOW)
        first = sync(cache, transport)
        print("Initial sync:", encode(first))
        consume(cache, transport, transport.events(cache.state()["checkpoint"]))
        print("After duplicate notifications:", encode(cache.view(online=True)))
        print("Read requests:", len([r for r in script.requests if "event_path" not in r]))
        print("Human unread unchanged:", cache.view()["summaries"][0]["unread_count"] == 3)
        cache.close()


if __name__ == "__main__":
    demo()
