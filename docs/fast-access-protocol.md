# Fast-access protocol v1

Read compact activity across authorized workspaces, then keep a small local summary
cache up to date. Notifications say **something changed**; a completed read says
**which state can be committed**. Neither operation marks a person's messages read.

This is an interoperable HTTP contract with a Multica adapter. It is not a claim
that every Multica deployment implements these endpoints. The runnable
[reference client](../examples/fast-access-client/) uses synthetic HTTP/SSE fixtures;
production interoperability and performance must be checked against your deployment.
It is a read-only example, not a complete bot, mailbox, authentication service,
business database or MCP server. Existing mailbox examples remain illustrative.

## Requests and envelope

Use the service's existing authentication and authorization. A local network or
trusted host does not grant additional visibility. An adapter must retain the
actual principal, originating task and home workspace context; never substitute
its host account. Keep credentials outside tool arguments, logs and cache files.

`POST /api/fast-access/v1/read` starts a full **current-state baseline**:

```json
{
  "scope": {"mode": "all_visible"},
  "include": ["chats", "issues", "run_changes", "active_runs"],
  "limit": 100,
  "max_bytes": 50000
}
```

Explicit scope: `{"mode":"workspace_ids","workspace_ids":["<workspace-id>"]}`.
All four includes are the default. Inaccessible explicitly requested scopes fail
as a whole; an empty result must not disguise a permission failure.

An optional initial `since` (RFC3339 timestamp) reads a retained activity window,
**not** a complete cache baseline. It cannot recover changes from before journal
installation. A window crossing an access change or deletion can require a reset.
The reference mirror always starts without `since`.

Continue a page, or start the next delta from a completed checkpoint, with:

```json
{"cursor":"<opaque-handle>","limit":100,"max_bytes":50000}
```

Do not combine cursor with since, scope or include. Handles bind the identity,
scope, filters, permission revision and fixed batch watermarks. Never parse or
construct handles. A page handle and a completed checkpoint are different roles.

`GET /api/fast-access/v1/runs?active=true` uses the same envelope and authorization.
Initial query scope is `scope=all_visible` or `workspace_ids=<comma-separated-ids>`;
continuations use cursor only (plus optional limit/max_bytes). It is an active-run
view, not a substitute for a full mirror read.

| Response field | Meaning |
| --- | --- |
| `schema_version` | String `"1"`; reject unsupported versions |
| `mode` | `durable_delta`; see compatibility below |
| `as_of` | Fixed observation timestamp for every page in this batch |
| `coverage_from`, `retention_floor` | Earliest available journal window, bounded by installation and retention |
| `scope_revision` | Opaque permission version; compare only for equality |
| `changes` | Issue/chat summaries and individual run transitions; may be empty on an incomplete page |
| `active_runs` | Current active attempts and separately typed automation executions; prioritized in pagination |
| `active_runs_complete` | All active entries for this batch have been delivered |
| `complete` | Entire batch has been delivered, not merely this HTTP response |
| `next_cursor` | Opaque next-page handle when incomplete; otherwise null |
| `checkpoint` | Null until complete; completed durable position for subsequent reads and SSE |

Default limit is 100, maximum 200 items per response. Default/maximum max_bytes is
50000 **uncompressed UTF-8 JSON bytes**, including envelope and escaping. All pages
count as requests. A multi-page batch is not a single 50 KB response. A batch fixes
both its watermarks and materialized current values; newer commits belong to the
next read. Empty filtered pages still require following next_cursor. Only the final
completed checkpoint advances the mirror. No global ordering across workspaces is
promised; committed sequence order is per workspace.

## Summary fields

Common fields: `workspace_id`, optional presentation `workspace_name`, `kind`, `id`,
`revision` (decimal string), `changed_at` (RFC3339), `op` (`upsert` or `delete`),
`content_truncated`. Durable changes may also carry stable `event_id`.
The object key is `(workspace_id, kind, id)`; revisions compare numerically **only
within that object**, never lexically or using floating-point numbers.

| kind | Summary fields |
| --- | --- |
| `chat` | title, preview, last_active_at, unread_count (the authenticated viewer's count) |
| `issue` | identifier, title, status, new_comment_count (including new replies under old roots), changed_fields if known |
| `run` | agent_id, authorized source_type/source_id, title, status, phase, started_at/finished_at if available, optional error_class |
| `autopilot_run` | Separately typed automation execution with status/phase and authorized source fields |

Titles: at most 80 Unicode code points/240 UTF-8 bytes. Previews: 160/480. Missing
optional fields are not proof of absence of activity. Individual historical run
transitions can omit start/finish timestamps; the current active snapshot supplies
current details. Prompts, full messages, configuration, results, token streams and
credentials are outside this projection. Fetch permitted detail separately, bounded
by object/thread/page. Never expand one whole transcript per notification.

Active attempts: queued, dispatched, running, waiting_local_directory, plus deferred
attempts with a wakeup. Phase is queued, executing (dispatched/running), or waiting.
Include chat-only attempts even when no issue exists. Automation execution is not
an agent attempt. Do not collapse all runs for one issue into one record.

## SSE and recovery

Subscribe to `GET /api/fast-access/v1/events?cursor=<completed-read-checkpoint>`.
On reconnect, `Last-Event-ID` takes precedence if supplied. Page handles cannot
subscribe. Example frames (all IDs are placeholders):

```text
event: change
data: {"event_id":"<event>","workspace_id":"<workspace>","entity_kind":"run","entity_id":"<run>","revision":"42","op":"upsert","changed_at":"2030-01-01T00:00:00Z"}

event: checkpoint
id: <notification-checkpoint>
data: {}

```

Change frames do not individually carry an SSE id in this adapter. After all
notifications in a segment, the checkpoint frame carries its opaque id. A disconnect
before it replays the segment with the same event IDs. Empty filtered segments may
still advance the notification checkpoint. Delivery is **at least once**.

An SSE id records notification delivery, **not applied data**. Coalesce changes and
call read from your **committed read checkpoint**. Apply revisions idempotently and
deduplicate event IDs in the same transaction as summaries and checkpoint. Finish
all read pages before committing. Process transition records before overlaying the
current active snapshots, which can have later revisions. Replace the active-run
list on each complete batch, including an empty list.

The example reconnects from its committed read checkpoint and intentionally does
not persist SSE ids. This may replay notifications but cannot skip unapplied reads.
It reads once per notification checkpoint, and periodically on keepalive, rather
than once per event. It also reads before each subscription to cover disconnected
periods; replay covers the read/subscribe gap. Use exponential backoff with jitter
and honor Retry-After. A periodic read is still required if the reminder path fails.

Control frames:

| Event | Client action |
| --- | --- |
| `scope_reset` | Immediately discard affected summaries, active list, dedup state and positions; rebuild current baseline |
| `reset_required` | Discard expired positions and cached state; rebuild without since |
| `read_required` | Compact read from committed read checkpoint, then reconnect; reset if instructed |
| comment keepalive | No entity change; permit periodic revalidation |

The service revalidates every page and replay. A stream revalidates during polling
and before delivery, and closes on reset. Slow consumers disconnect and recover
through reads. Persistent journal correctness must not depend on an in-memory
notification buffer, a single API process, Redis or a websocket being available.

## Permissions, deletion and cache boundaries

Member access and linked-project access are distinct. Validate both agent and
source visibility for runs; do not reveal hidden source IDs or titles. New grants,
revocations, sharing changes and expired grants can invalidate a scope. The current
Multica adapter uses a conservative global permission revision, so an unrelated
change may cause extra rebuilds.

Generic adapters may send tombstones to a known authorized audience. The current
adapter uses **scope_reset for deletion**, without publishing deleted/hidden IDs.
Clients must support that fallback; a rebuilt full snapshot replaces missing rows.
The example additionally accepts a revision-only tombstone and prevents older
upserts from resurrecting it. It does not claim that the current server emits such
tombstones.

Partition cache files by normalized server URL, actual principal, canonical scope,
filters and any task/workspace identity context. A locally supplied principal label
is not authentication; use the real identity and change it when switching accounts.
Never put credentials in that key. One principal's cache must not be reused by a
new principal or broader host identity.

SQLite holds only summaries, dedup records and a read checkpoint. Its writes are
local only. Commit all batch updates and checkpoint in one local transaction.
Before-commit crash: old state/old checkpoint survive. After-commit crash: new
state/new checkpoint survive. Replayed events have no additional effect. The cache
is disposable, never the source of business truth or a store for full sensitive
content. Local access permissions reduce exposure but cannot recall copied data.

Offline results must expose `last_sync_at`, `cache_age` (seconds since successful
sync), and `stale_reason`. More than 60 seconds without sync is overdue; even a
recent offline read is unverified. Clock skew makes age approximate. On observed
revocation or failed authentication/authorization, clear summaries before trying
again. Offline clients cannot know about revocation that happened after disconnection;
sensitive details always require online authorization. Beyond seven days rebuild
current state, never claim that expired history was recovered.

## Errors and resource limits

Errors have a stable `code` and human `message`. Do not log raw bodies, authorization
headers, handles or endpoint URLs containing private data.

| HTTP / code | Meaning and action |
| --- | --- |
| 400 `invalid_request` | Invalid scope, parameters or handle role; correct the request |
| 401 | Existing authentication failed; clear protected cache and stop |
| 403 `scope_denied` | Unauthorized scope/identity; clear cache and stop |
| 409 `scope_reset` | Permissions/deletion invalidated the scope; clear and rebuild |
| 410 `reset_required` | Unknown, expired or wrong-identity handle, unavailable history, or expired batch; rebuild |
| 422 `byte_budget_too_small` | One next item cannot fit; increase budget within the limit |
| 422 `snapshot_too_large` | Current-state projection too large; narrow scope |
| 429 `rate_limited` / `stream_limit` | Back off according to Retry-After header with jitter |
| 5xx / network failure | Keep only clearly marked stale summaries; retry reads with backoff |

Adapter defaults: 60 reads/minute, burst 10 per principal **per API process**;
deployment-wide read quotas require a shared limiter. Two simultaneous streams per
principal are shared across API processes. Keepalive is 30 seconds, event buffering
is bounded to 1 MB, and blocked stream writes time out after five seconds.
Page materializations expire after five minutes; completed checkpoints and journal
replay are valid for at most seven days. Current materializations cap at 10000
objects and return an explicit error beyond that. Limits are not throughput promises.

## MCP adapter tool surface

MCP is a thin adapter over the same authorization, read protocol and business APIs,
not a second database. This table specifies the intended v1 surface; discover the
actual installed adapter with `tools/list`. Availability must be verified per release.
The reference Python example does **not** implement these tools.

| Tool | Inputs | Bounded return / behavior |
| --- | --- | --- |
| `changes_read` | scope; since or cursor; limit, max_bytes | Read envelope, including completion metadata |
| `runs_list` | scope, active, cursor, limit, max_bytes | Active runs with the same envelope |
| `issue_get` | workspace_id, id | One issue summary; detail explicit |
| `comments_list` | workspace_id, issue_id, thread/window, limit | Compact directory; old root with new replies remains discoverable |
| `chats_list` | workspace_id, filters, cursor, limit | Directory with unread and last activity |
| `chat_history` | workspace_id, chat_id, cursor, limit | One bounded page; no read-cursor mutation |
| `comment_create` | workspace_id, issue_id, content, optional parent_id | Created id/status/canonical URL where supported |
| `chat_send` | workspace_id, chat_id, content, mode | Created id/status/canonical URL where supported |
| `attachment_download` | attachment_id | Authorized file with size/hash verification |

Read tools declare readOnlyHint; annotations are not a security boundary. Credentials
belong in the adapter's protected transport configuration. Writes retain existing
server validation and quotas. Without server idempotency support, do not retry a
timeout blindly: report ambiguous_write, query the outcome, then resolve it. A
stdio adapter and a future Streamable HTTP adapter are distinct from this application's
SSE event stream. Application SSE is not an MCP transport.

## Compatibility and validation

Accept additive optional fields for known schema versions; reject unknown major
schemas and unknown operations. Keep revision strings lossless. The earlier
`timestamp_snapshot` mode can display current summaries but cannot support reliable
history, deletion recovery or durable cursor replay. Its snapshot receipt is not a
read cursor. The example refuses it explicitly rather than inventing continuity.

Enable a durable client only after its server has the persistent journal and read
endpoints. A server rollback or journal reinstall can invalidate handles; rebuild
against a supported durable version. The example has no token renewal, scheduler,
write API, encryption-at-rest service, UI or server deployment logic.

Run [the fixture commands](../examples/fast-access-client/README.md) from a clean
checkout to exercise sync, empty pagination, disconnected catch-up, duplicate
notifications/events, large revisions, real process crashes, reset/deletion,
retention expiry, isolation and unchanged unread counts. Production claims require
separate authorized live verification, including access revocation and final cache
comparison against the authorized current state. Mock timings are not production
latency evidence.
