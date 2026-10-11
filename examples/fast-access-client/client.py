#!/usr/bin/env python3
"""Read-only fast-access example. Python 3.9+, standard library only."""
import argparse
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import random
import sqlite3
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

RETENTION = 7 * 24 * 3600
INCLUDE = ["chats", "issues", "run_changes", "active_runs"]
SUMMARY_FIELDS = set("event_id workspace_id workspace_name kind id revision changed_at op title "
                     "preview content_truncated identifier status new_comment_count changed_fields "
                     "last_active_at unread_count agent_id source_type source_id phase started_at "
                     "finished_at error_class".split())


def summary(item):
    # Forward-compatible additions are ignored, never blindly persisted as sensitive detail.
    return {key: value for key, value in item.items() if key in SUMMARY_FIELDS}


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


class Failure(Exception):
    def __init__(self, code, status=0, retry_after=0):
        super().__init__(code)  # Never include a URL, response body or credential.
        self.code, self.status, self.retry_after = code, status, retry_after


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Failure("redirect_refused")


class HTTP:
    def __init__(self, server, headers=None, fixture=False):
        parts = urlsplit(server)
        if parts.username or parts.password or parts.query or parts.fragment:
            raise Failure("invalid_server")
        if parts.scheme != "https" and not (fixture and parts.hostname == "127.0.0.1"):
            raise Failure("https_required")
        self.server = server.rstrip("/")
        self.headers = headers or {}
        self.opener = build_opener(NoRedirect())

    def open(self, path, payload=None, extra=None):
        headers = {**self.headers, **(extra or {})}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.server + path, data=None if payload is None else encode(payload).encode(),
                      headers=headers)
        try:
            return self.opener.open(req, timeout=40)
        except HTTPError as error:
            try:
                code = json.loads(error.read(4096)).get("code", "http_error")
            except (ValueError, AttributeError):
                code = "http_error"
            # Only propagate known codes, never arbitrary server text.
            known = {"scope_reset", "reset_required", "scope_denied", "rate_limited",
                     "stream_limit", "invalid_request", "byte_budget_too_small",
                     "snapshot_too_large"}
            try:
                retry = max(0, min(300, int(error.headers.get("Retry-After", "0"))))
            except ValueError:
                retry = 0
            raise Failure(code if code in known else "http_error", error.code, retry) from None
        except (URLError, OSError):
            raise Failure("offline") from None

    def read(self, payload):
        try:
            with self.open("/api/fast-access/v1/read", payload) as response:
                raw = response.read(50001)
        except (OSError, HTTPException):
            raise Failure("offline") from None
        if len(raw) > 50000:
            raise Failure("response_too_large")
        try:
            return json.loads(raw)
        except ValueError:
            raise Failure("invalid_response") from None

    def events(self, checkpoint, last_id=None):
        headers = {"Accept": "text/event-stream"}
        if last_id:
            headers["Last-Event-ID"] = last_id
        with self.open("/api/fast-access/v1/events?" + urlencode({"cursor": checkpoint}),
                       extra=headers) as response:
            if response.headers.get_content_type() != "text/event-stream":
                raise Failure("invalid_stream")
            yield from sse(response)


def sse(stream):
    """Bounded UTF-8 SSE parser; keepalives also let the reader revalidate."""
    event, event_id, data, size = "message", None, [], 0
    while True:
        raw = stream.readline(65537)
        if not raw:
            return  # An incomplete final frame must not advance any cursor.
        size += len(raw)
        if len(raw) > 65536 or size > 1024 * 1024:
            raise Failure("stream_too_large")
        try:
            line = raw.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            raise Failure("invalid_stream") from None
        if line.startswith(":"):
            yield {"event": "keepalive", "id": None, "data": {}}
            size = 0
        elif not line:
            if data:
                try:
                    value = json.loads("\n".join(data))
                except ValueError:
                    raise Failure("invalid_stream") from None
                yield {"event": event, "id": event_id, "data": value}
            event, event_id, data, size = "message", None, [], 0
        else:
            field, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if field == "event":
                event = value
            elif field == "id" and "\0" not in value:
                event_id = value
            elif field == "data":
                data.append(value)


class Cache:
    def __init__(self, directory, server, principal, scope, context=None, clock=time.time):
        # The caller supplies the actual principal; this key is isolation, not authentication.
        scope = dict(scope)
        if "workspace_ids" in scope:
            scope["workspace_ids"] = sorted(set(scope["workspace_ids"]))
        self.scope, self.clock = scope, clock
        key = encode([server.rstrip("/"), principal, scope, INCLUDE, context or {}])
        root = Path(directory).expanduser()
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        root.chmod(0o700)
        self.path = root / (hashlib.sha256(key.encode()).hexdigest() + ".sqlite3")
        self.db = sqlite3.connect(self.path, timeout=5)
        self.path.chmod(0o600)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT);
            INSERT OR IGNORE INTO state VALUES(1, '{}');
            CREATE TABLE IF NOT EXISTS objects (
                key TEXT PRIMARY KEY, revision TEXT NOT NULL, body TEXT);
            CREATE TABLE IF NOT EXISTS active (key TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY, applied_at REAL NOT NULL);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def state(self):
        return json.loads(self.db.execute("SELECT value FROM state WHERE id=1").fetchone()[0])

    def put_state(self, value):
        self.db.execute("UPDATE state SET value=? WHERE id=1", (encode(value),))

    def invalidate(self, reason):
        with self.db:
            for table in ("objects", "active", "seen"):
                self.db.execute("DELETE FROM " + table)
            self.put_state({"stale_reason": reason})

    def stale(self, reason):
        with self.db:
            state = self.state()
            state["stale_reason"] = reason
            self.put_state(state)

    def view(self, online=False):
        state = self.state()
        now = self.clock()
        if state.get("as_of") and now - timestamp(state["as_of"]) >= RETENTION:
            self.invalidate("retention_expired")
            state = self.state()
        last = state.get("last_sync_at")
        age = max(0, now - timestamp(last)) if last else None
        reason = state.get("stale_reason")
        if not reason and (age is None or age > 60):
            reason = "never_synced" if age is None else "sync_overdue"
        if not reason and not online:
            reason = "offline_unverified"
        return {"summaries": [json.loads(row[0]) for row in self.db.execute(
                    "SELECT body FROM objects WHERE body IS NOT NULL ORDER BY key")],
                "active_runs": [json.loads(row[0]) for row in self.db.execute(
                    "SELECT body FROM active ORDER BY key")],
                "last_sync_at": last, "cache_age": age, "stale_reason": reason}

    @staticmethod
    def key(item):
        return encode([item["workspace_id"], item["kind"], item["id"]])

    def apply(self, item, current=False):
        revision = item["revision"]
        if not isinstance(revision, str) or not revision.isascii() or not revision.isdecimal():
            raise Failure("invalid_revision")
        if item["op"] not in ("upsert", "delete"):
            raise Failure("unknown_operation")
        key = self.key(item)
        event = item.get("event_id")
        if event:
            if self.db.execute("SELECT 1 FROM seen WHERE id=?", (event,)).fetchone():
                return
            self.db.execute("INSERT INTO seen VALUES(?,?)", (event, self.clock()))
        previous = self.db.execute("SELECT revision FROM objects WHERE key=?", (key,)).fetchone()
        if previous and (int(revision) < int(previous[0]) or
                         (int(revision) == int(previous[0]) and not current)):
            return
        # Keep a revision-only tombstone so a late upsert cannot resurrect a delete.
        body = encode(summary(item)) if item["op"] == "upsert" else None
        self.db.execute("INSERT OR REPLACE INTO objects VALUES(?,?,?)", (key, revision, body))

    def commit_batch(self, pages, baseline, expected, crash=None):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.state().get("checkpoint") != expected:
                raise Failure("concurrent_sync")
            if baseline:
                for table in ("objects", "seen"):
                    self.db.execute("DELETE FROM " + table)
            # All transitions first; current active snapshots may have higher revisions.
            for page in pages:
                for item in page["changes"]:
                    self.apply(item)
            self.db.execute("DELETE FROM active")
            for page in pages:
                for item in page["active_runs"]:
                    self.apply(item, current=True)
                    self.db.execute("INSERT OR REPLACE INTO active VALUES(?,?)",
                                    (self.key(item), encode(summary(item))))
            final = pages[-1]
            self.put_state({"checkpoint": final["checkpoint"],
                            "scope_revision": final["scope_revision"], "as_of": final["as_of"],
                            "last_sync_at": datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(),
                            "stale_reason": None})
            self.db.execute("DELETE FROM seen WHERE applied_at<?", (self.clock() - RETENTION,))
            if crash == "before_commit":
                os._exit(81)  # Fixture only; SQLite rolls back the open transaction.
        if crash == "after_commit":
            os._exit(82)


def sync(cache, transport, crash=None):
    """One logical read batch (including pages); reset at most once per call."""
    for attempt in range(2):
        state = cache.state()
        if state.get("as_of") and cache.clock() - timestamp(state["as_of"]) >= RETENTION:
            cache.invalidate("retention_expired")
            state = cache.state()
        expected = state.get("checkpoint")
        baseline = not expected
        request = {"cursor": expected} if expected else {"scope": cache.scope, "include": INCLUDE}
        pages, cursors, total = [], set(), 0
        try:
            while True:
                page = transport.read({**request, "limit": 100, "max_bytes": 50000})
                if not isinstance(page, dict):
                    raise Failure("invalid_response")
                if page.get("schema_version") != "1" or page.get("mode") != "durable_delta":
                    raise Failure("unsupported_protocol")
                if type(page.get("complete")) is not bool:
                    raise Failure("invalid_response")
                if not isinstance(page.get("scope_revision"), str) or not page["scope_revision"]:
                    raise Failure("invalid_response")
                timestamp(page["as_of"])
                for field in ("changes", "active_runs"):
                    if not isinstance(page.get(field), list):
                        raise Failure("invalid_response")
                if pages and any(page[k] != pages[0][k] for k in ("scope_revision", "as_of")):
                    raise Failure("scope_reset", 409)
                if expected and page["scope_revision"] != state.get("scope_revision"):
                    raise Failure("scope_reset", 409)
                total += len(encode(page).encode())
                if len(pages) >= 1000 or total > 20_000_000:
                    raise Failure("batch_too_large")
                pages.append(page)
                if page["complete"]:
                    if (not isinstance(page.get("checkpoint"), str) or not page["checkpoint"]
                            or page.get("next_cursor") or page.get("active_runs_complete") is not True):
                        raise Failure("invalid_response")
                    break
                cursor = page.get("next_cursor")
                if not isinstance(cursor, str) or not cursor or cursor in cursors or page.get("checkpoint"):
                    raise Failure("invalid_response")
                cursors.add(cursor)
                request = {"cursor": cursor}
            cache.commit_batch(pages, baseline, expected, crash)
            return cache.view(online=True)
        except Failure as error:
            if error.code in ("scope_reset", "reset_required"):
                cache.invalidate(error.code)
                if attempt == 0:
                    continue
            elif error.status in (401, 403):
                cache.invalidate("access_denied")
            elif error.code in ("unsupported_protocol", "invalid_response", "invalid_revision",
                                "unknown_operation"):
                cache.invalidate(error.code)
            else:
                cache.stale(error.code)
            raise
        except (KeyError, TypeError, ValueError):
            cache.invalidate("invalid_response")
            raise Failure("invalid_response") from None
    raise Failure("reset_required")


def consume(cache, transport, frames, refresh_seconds=30):
    """Coalesce a whole SSE batch into one read; never store SSE IDs as read positions."""
    last_read = time.monotonic()
    for frame in frames:
        kind = frame["event"]
        if kind in ("scope_reset", "reset_required"):
            cache.invalidate(kind)
            sync(cache, transport)
            return
        if kind == "read_required":
            sync(cache, transport)
            return
        if kind == "checkpoint" or time.monotonic() - last_read >= refresh_seconds:
            sync(cache, transport)
            last_read = time.monotonic()
        # change events only notify. Even repeated event IDs cannot skip a read.


def watch(cache, transport):
    delay = 1
    while True:
        try:
            sync(cache, transport)  # Catch the baseline/subscribe gap and every reconnect.
            consume(cache, transport, transport.events(cache.state()["checkpoint"]))
            delay = 1
            cache.stale("disconnected")
        except Failure as error:
            if error.status in (401, 403):
                cache.invalidate("access_denied")
                raise
            if error.code in ("scope_reset", "reset_required"):
                cache.invalidate(error.code)
            else:
                cache.stale(error.code)
            if error.status and error.status < 500 and error.status != 429 and error.status not in (409, 410):
                raise
            delay = max(delay, error.retry_after)
        except (OSError, URLError, HTTPException):
            cache.stale("offline")
        time.sleep(delay + random.uniform(0, min(delay, 3)))
        delay = min(delay * 2, 60)


def configured():
    server = os.environ["FAST_ACCESS_SERVER"]
    principal = os.environ["FAST_ACCESS_PRINCIPAL"]
    scope = json.loads(os.environ.get("FAST_ACCESS_SCOPE", '{"mode":"all_visible"}'))
    context = {}
    for env, header in (("FAST_ACCESS_WORKSPACE", "X-Workspace-ID"),
                        ("FAST_ACCESS_TASK", "X-Task-ID"), ("FAST_ACCESS_ACTOR", "X-Actor-Source")):
        if os.environ.get(env):
            context[header] = os.environ[env]
    cache = Cache(os.environ.get("FAST_ACCESS_CACHE", "~/.cache/fast-access-example"),
                  server, principal, scope, context)
    return cache, server, context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sync", "watch", "cache"])
    args = parser.parse_args()
    # Sidecar journals also inherit private permissions.
    os.umask(0o077)
    cache = None
    try:
        cache, server, headers = configured()
        if args.command == "cache":
            print(encode(cache.view()))
            return 0
        # Existing identity only; this example never creates or refreshes credentials.
        token = Path(os.environ["FAST_ACCESS_TOKEN_FILE"]).expanduser().read_text().strip()
        if not token or "\n" in token or "\r" in token:
            raise Failure("invalid_credential_file")
        transport = HTTP(server, {**headers, "Authorization": "Bearer " + token})
        if args.command == "sync":
            print(encode(sync(cache, transport)))
        else:
            watch(cache, transport)
        return 0
    except KeyboardInterrupt:
        return 130
    except (Failure, KeyError, OSError, ValueError, sqlite3.Error):
        # Do not print arbitrary exceptions (they may contain endpoints or headers).
        print("fast-access failed; check configuration or cache stale_reason", file=sys.stderr)
        return 1
    finally:
        if cache:
            cache.close()


if __name__ == "__main__":
    sys.exit(main())
