import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from client import Cache, Failure, RETENTION, consume, sse, sync
from fixture import NOW, PRINCIPAL, SCOPE, SERVER, Script, item, page, serve


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = NOW
        self.cache = Cache(self.tmp.name, SERVER, PRINCIPAL, SCOPE, clock=lambda: self.now)

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def baseline(self):
        return sync(self.cache, Script([page(changes=[item()])]))

    def test_http_sync_sse_duplicates_and_disconnect_gap(self):
        frames = (b': keepalive\n\n' + b'event: change\ndata: {"event_id":"event-2"}\n\n' * 8
                  + b'event: checkpoint\nid: notification-only\ndata: {}\n\n')
        script = Script([page(changes=[item()]), page("read-2", [item("2", event_id="event-2")]),
                         page("read-3", [item("3", title="Changed while disconnected")])], frames)
        with serve(script) as transport:
            sync(self.cache, transport)
            consume(self.cache, transport, transport.events("read-1"))
            self.assertEqual(self.cache.state()["checkpoint"], "read-2")
            self.assertEqual(len([r for r in script.requests if "event_path" not in r]), 2)
            sync(self.cache, transport)
        self.assertEqual(script.requests[-1]["cursor"], "read-2")
        self.assertEqual(self.cache.view()["summaries"][0]["title"], "Changed while disconnected")
        self.assertEqual(self.cache.view()["summaries"][0]["unread_count"], 3)

    def test_pages_empty_page_and_active_overlay(self):
        run = item("20", "run", status="running", phase="executing")
        script = Script([
            page(None, [], [run], complete=False, next_cursor="page-2"),
            page(None, [], [], complete=False, next_cursor="page-3"),
            page("read-20", [item("19", "run", status="queued", event_id="run-19")])])
        result = sync(self.cache, script)
        self.assertEqual(result["summaries"][0]["status"], "running")
        self.assertEqual(result["active_runs"][0]["status"], "running")
        self.assertEqual(script.requests[1], {"cursor": "page-2", "limit": 100, "max_bytes": 50000})
        sync(self.cache, Script([page("read-21", [item("21", "run", status="completed")])]))
        self.assertEqual(self.cache.view()["active_runs"], [])

    def test_equal_revision_active_overlay_preserves_current_details(self):
        result = sync(self.cache, Script([page(changes=[item("20", "run", status="running")],
                         active=[item("20", "run", status="running", started_at="2030-01-01T00:00:00Z")])]))
        self.assertEqual(result["summaries"][0]["started_at"], "2030-01-01T00:00:00Z")

    def test_incomplete_batch_never_commits(self):
        self.baseline()
        script = Script([page(None, [item("2")], complete=False, next_cursor="page-2"),
                         Failure("offline")])
        with self.assertRaises(Failure):
            sync(self.cache, script)
        self.assertEqual(self.cache.state()["checkpoint"], "read-1")
        self.assertEqual(self.cache.view()["summaries"][0]["revision"], "1")
        self.assertEqual(self.cache.view()["stale_reason"], "offline")

    def test_replayed_events_large_revision_and_tombstones(self):
        revision = "9007199254740993"
        entry = item(revision, event_id="event-large")
        sync(self.cache, Script([page(changes=[entry, entry, item("3")])]))
        self.assertEqual(self.cache.view()["summaries"][0]["revision"], revision)
        self.assertEqual(self.cache.db.execute("SELECT count(*) FROM seen").fetchone()[0], 1)
        sync(self.cache, Script([page("deleted", [item("9007199254740994", op="delete"), entry])]))
        self.assertEqual(self.cache.view()["summaries"], [])

    def test_scope_reset_clears_before_failed_rebuild(self):
        self.baseline()
        with self.assertRaises(Failure):
            sync(self.cache, Script([Failure("scope_reset", 409), Failure("offline")]))
        self.assertEqual(self.cache.view()["summaries"], [])
        self.assertIsNone(self.cache.state().get("checkpoint"))

    def test_scope_reset_rebuild_and_delete_fallback(self):
        self.baseline()
        script = Script([Failure("scope_reset", 409), page("new-permission", scope_revision="permission-2")])
        sync(self.cache, script)
        self.assertIn("scope", script.requests[1])
        self.assertEqual(self.cache.view()["summaries"], [])
        self.assertEqual(self.cache.state()["scope_revision"], "permission-2")

    def test_stream_reset_rebuild(self):
        self.baseline()
        consume(self.cache, Script([page("new", scope_revision="permission-2")]),
                [{"event": "scope_reset", "data": {}, "id": None}])
        self.assertEqual(self.cache.view()["summaries"], [])

    def test_server_expiry_and_local_seven_day_expiry(self):
        self.baseline()
        script = Script([Failure("reset_required", 410), page("rebuilt")])
        sync(self.cache, script)
        self.assertIn("scope", script.requests[-1])
        self.now += RETENTION + 1
        self.assertEqual(self.cache.view()["stale_reason"], "retention_expired")
        self.assertEqual(self.cache.view()["summaries"], [])
        # A rebuild must never send the expired position or a historic since.
        from datetime import datetime, timezone
        script = Script([page("fresh", as_of=datetime.fromtimestamp(self.now, timezone.utc).isoformat())])
        sync(self.cache, script)
        self.assertNotIn("cursor", script.requests[0])
        self.assertNotIn("since", script.requests[0])

    def test_isolation_permissions_and_stale_metadata(self):
        result = self.baseline()
        self.assertIsNone(result["stale_reason"])
        self.assertEqual(self.cache.view()["stale_reason"], "offline_unverified")
        self.now += 61
        self.assertEqual(self.cache.view()["stale_reason"], "sync_overdue")
        self.assertEqual(self.cache.view()["cache_age"], 61)
        self.assertIsNotNone(result["last_sync_at"])
        for server, principal, scope, context in [
                (SERVER + "/other", PRINCIPAL, SCOPE, None),
                (SERVER, "another-principal", SCOPE, None),
                (SERVER, PRINCIPAL, {"mode": "workspace_ids", "workspace_ids": ["example"]}, None),
                (SERVER, PRINCIPAL, SCOPE, {"X-Task-ID": "another-task"})]:
            other = Cache(self.tmp.name, server, principal, scope, context)
            self.assertNotEqual(other.path, self.cache.path)
            self.assertEqual(other.view()["summaries"], [])
            other.close()
        self.assertEqual(self.cache.path.stat().st_mode & 0o777, 0o600)

    def test_auth_failure_and_unknown_protocol_fail_closed(self):
        for failure in (Failure("scope_denied", 403), Failure("http_error", 401)):
            self.baseline()
            with self.assertRaises(Failure):
                sync(self.cache, Script([failure]))
            self.assertEqual(self.cache.view()["summaries"], [])
        for altered in ({"schema_version": "2"}, {"mode": "timestamp_snapshot"}):
            self.baseline()
            with self.assertRaises(Failure):
                sync(self.cache, Script([page(**altered)]))
            self.assertEqual(self.cache.view()["summaries"], [])

    def test_crash_before_and_after_commit_real_process(self):
        self.baseline()
        command = '''
import sys
from client import Cache, sync
from fixture import NOW, SERVER, PRINCIPAL, SCOPE, Script, item, page
cache = Cache(sys.argv[1], SERVER, PRINCIPAL, SCOPE, clock=lambda: NOW)
sync(cache, Script([page("read-2", [item("2", event_id="event-2")])]), crash=sys.argv[2])
'''
        for point, exit_code, expected in [("before_commit", 81, "read-1"),
                                           ("after_commit", 82, "read-2")]:
            proc = subprocess.run([sys.executable, "-c", command, self.tmp.name, point],
                                  cwd=Path(__file__).parent, capture_output=True)
            self.assertEqual(proc.returncode, exit_code, proc.stderr)
            self.assertEqual(self.cache.state()["checkpoint"], expected)
            self.assertEqual(self.cache.view()["summaries"][0]["revision"], expected[-1])
        script = Script([page("read-3", [item("2", event_id="event-2")])])
        sync(self.cache, script)
        self.assertEqual(script.requests[0]["cursor"], "read-2")
        self.assertEqual(len(self.cache.view()["summaries"]), 1)
        self.assertEqual(self.cache.db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_sse_incomplete_frame_and_multiline(self):
        self.assertEqual(list(sse(io.BytesIO(b'event: checkpoint\nid: lost\ndata: {}'))), [])
        frames = list(sse(io.BytesIO(b'event: change\r\ndata: {\r\ndata: "x":1}\r\n\r\n')))
        self.assertEqual(frames[0]["data"], {"x": 1})

    def test_unknown_fields_not_cached_and_429_preserves_checkpoint(self):
        sync(self.cache, Script([page(changes=[item(future_detail="omit this")])]))
        self.assertNotIn("future_detail", self.cache.view()["summaries"][0])
        with serve(Script([Failure("rate_limited", 429, 12)])) as transport:
            with self.assertRaises(Failure) as caught:
                sync(self.cache, transport)
        self.assertEqual(caught.exception.retry_after, 12)
        self.assertEqual(self.cache.state()["checkpoint"], "read-1")
        self.assertEqual(self.cache.view()["stale_reason"], "rate_limited")

    def test_retry_after_and_reset_http(self):
        self.baseline()
        with serve(Script([Failure("scope_reset", 409), page("rebuilt")])) as transport:
            sync(self.cache, transport)
        self.assertEqual(self.cache.state()["checkpoint"], "rebuilt")


if __name__ == "__main__":
    unittest.main()
