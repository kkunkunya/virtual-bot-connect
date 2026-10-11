# Fast-access read-only cache example

A Python 3.9+ standard-library client for the [v1 protocol](../../docs/fast-access-protocol.md).
No pip install, account, database server or credential is needed for the fixture.
It demonstrates a disposable SQLite summary mirror, not a full business client.

## Run from a clean checkout

From the repository root:

```sh
python3 examples/fast-access-client/fixture.py
python3 -m unittest discover -s examples/fast-access-client -p 'test_*.py' -v
```

The demo starts a loopback HTTP/SSE server, performs a baseline, receives duplicate
notifications, reads one delta and prints the updated summary. It stops its server
and deletes its temporary database before exiting. Expected final lines:

```text
Read requests: 2
Human unread unchanged: True
```

Tests also cover a dropped connection, incomplete/empty pages, newer active snapshots,
repeated event IDs and revision ordering above the safe floating-point integer range,
delete tombstones, scope_reset, denied access, unknown schema/mode, seven-day expiry,
and two child processes that deliberately exit immediately before/after SQLite commit.
Assertions compare stored state, checkpoint and summary contents, not just event counts.

## Optional real endpoint

Use a deployment that advertises durable fast-access v1. Configure the actual
existing principal and authorization context; this client never mints or refreshes
credentials. Keep the token in a protected file (0600 under a 0700 directory),
provisioned outside chat and shell history. Environment variables carry configuration
and the file path, not a literal secret. `config.example.sh` contains placeholders
only; replace them locally. Do not commit that local file.

```sh
# Set the environment using your local configuration manager, then:
python3 examples/fast-access-client/client.py sync
python3 examples/fast-access-client/client.py cache
python3 examples/fast-access-client/client.py watch
```

`sync` reads one complete logical batch (possibly multiple HTTP pages) and exits.
The next sync reads incrementally from the saved checkpoint. `watch` runs in the
foreground; Ctrl-C stops it. It coalesces SSE notifications, revalidates periodically,
and reconnects with jittered backoff. `cache` uses no network or token, and always
marks its result unverified/overdue when appropriate. It never marks chats read.
All three commands print no credential; sync/cache print summaries, which can still
be private. Protect or avoid redirecting those outputs.

| Environment | Value |
| --- | --- |
| FAST_ACCESS_SERVER | HTTPS base URL, e.g. `https://service.example.invalid` |
| FAST_ACCESS_PRINCIPAL | Actual stable authenticated principal ID; not a display name or token |
| FAST_ACCESS_SCOPE | JSON scope; defaults to `{"mode":"all_visible"}` |
| FAST_ACCESS_TOKEN_FILE | Protected file containing the existing token only |
| FAST_ACCESS_CACHE | Dedicated private directory; defaults to `~/.cache/fast-access-example` |
| FAST_ACCESS_WORKSPACE | Optional existing home workspace header context |
| FAST_ACCESS_TASK | Optional existing originating task header context |
| FAST_ACCESS_ACTOR | Optional existing actor-source header context |

Use only the context your existing authorized client uses, never invent a broader
identity. Cache filenames hash server/principal/scope/include/context; change the
principal when changing identities. This partition is not a replacement for server
authorization. HTTPS is required for real endpoints and redirects are refused.
Only the fixture constructor permits loopback HTTP.

## Recovery rules

- Gather bounded pages before committing. One transaction updates dedup records,
  summaries, current active list and the completed read checkpoint. Partial batches
  are not visible. Before-commit crashes replay; after-commit crashes resume.
- SSE checkpoint IDs never become applied read positions. Reconnect from the
  committed read checkpoint. A notification batch triggers one compact read, not a
  full object request for every event. The batch has a local 20 MB/1000-page cap;
  exceeding it fails explicitly and leaves the previous checkpoint unchanged.
- Clear on scope_reset, reset_required or denied access, before rebuilding. The
  current server uses scope_reset for deletion; an empty rebuilt snapshot removes
  the deleted rows. Generic tombstones are supported too, retaining revision only.
- Return `stale_reason`, `cache_age` in seconds and `last_sync_at`. More than 60
  seconds without sync is overdue. Offline visibility is never freshly authorized;
  after seven days the old cache is cleared and a current baseline is required.
- The cache only stores summaries. The `active_runs` list is authoritative for
  which runs remain active; `summaries` can also retain historical terminal runs.
  New active snapshots overlay transitions after the whole batch is collected.
- One writer per cache is recommended. An optimistic checkpoint check prevents a
  slower writer from overwriting a newer completed batch. Do not mount this SQLite
  file on a network filesystem. Local copied data cannot be remotely recalled.

No real endpoint is required or exercised by the fixture commands. Successful mocks
do not prove a particular deployment supports the protocol, its latency target, or
all production permission paths. The example intentionally omits writes, credential
renewal, MCP serving, background supervision and full transcript storage.

## Check the installed MCP contract

On a POSIX host with Python 3.9+ and a Multica release providing the local MCP
adapter, use its existing runtime identity:

```sh
python3 examples/fast-access-client/verify_mcp_contract.py -- multica mcp serve
```

This starts the command in the foreground and sends only initialize,
notifications/initialized and tools/list. It never sends tools/call or mutates a
business object. Success reports nine matching tools. A missing tool, unexpected
argument, changed required field or checked schema bound exits with status 1.
The check covers the documented argument table, strictness, limit ranges, chat
mode enum, offset minimum and nested scope field names. Pagination semantics,
fixed payload budgets and authorization still require integration verification.

For an offline recheck, capture discovery with `--save-schema <local-schema.json>`
and later use `--schema <local-schema.json>` instead of the command. Review any
capture before sharing it; do not commit deployment-specific discovery output.
An offline pass checks that capture only. Neither mode runs the cache fixture or
proves real endpoint access. No additional credentials or public schema fixture
are needed.
