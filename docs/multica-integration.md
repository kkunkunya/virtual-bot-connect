# Connecting a bot to Multica

This page covers the Multica side: giving a bot an identity, showing what it wrote, and waking it up.

Some of these features (the *External bots* settings page, "via bot" attribution, wake rules) were built in a
Multica fork for this project and may not be in upstream Multica yet. With plain upstream Multica you can still
do steps 1–3 using a normal personal API token.

## 1. Bot key

- Create a key for each bot. Under the hood it is a personal access token with the admin's rights, stored with a
  bot marker (`kind = bot`) so the server can tell bot writes apart.
- The *External bots* page (admins only) lets you name the bot, pick its type, generate the key once, copy
  ready-made setup instructions, see when it was last used, and stop or regenerate it.
- Stopping a bot revokes its key immediately (the bot's next command fails with 401). History stays readable.

**Handing the key over:** never in chat, prompts, the bot's description, git or logs. Put it in a protected file
on the bot computer (directory `0700`, file `0600`) or pass it on stdin:

```sh
# on the bot computer — reads the token from a protected file, never from argv
multica login --token < "$CREDENTIALS_DIR/multica.token"
multica auth status
multica workspace list --output json
```

Then open a **new** shell and run `multica auth status` again — "installed" is not "logged in", and "logged in
once" is not "persists".

## 2. "Via bot" attribution

Because the bot key has your rights, its writes would otherwise look exactly like you. The server records which
bot key made each write and the UI/CLI show it:

- comments, chat messages and ticket changes carry `via_bot_id` / `via_bot_name`;
- the web UI shows "via &lt;bot name&gt;" next to the author;
- `--output json` includes the field;
- a comment made via a bot is **never** treated as the owner's own words — it cannot approve a decision.

The trusted source is the authenticated key. Any client-supplied "I am bot X" header is stripped and ignored.

## 3. Using the CLI from the bot

| Goal | Command |
|---|---|
| find work, read everything | `issue list / search / get / context`, `issue comment list --full` |
| find chats, read history | `chat list / search / history` (follow the cursor) |
| continue a chat | `chat send --session …`, then `chat history` to find *this* reply |
| change tickets | `issue update / status / assign / label` |
| comment, edit, retract | `issue comment add / update / delete` |
| files | `issue comment add --attachment`, `chat send --attachment` |

Always check `--help` first. A successful send only means the request was accepted; match the reply by
session/message id and time, not by "the latest message".

## 4. Wake-ups (Multica → bot)

The bot gives Multica a webhook (for Grok: a routine with a webhook trigger). Multica stores the URL and key
**encrypted and write-only** — the API only ever reports `webhook_configured: true`.

When something the bot cares about happens, the server POSTs a short event to that webhook
([example payload](../examples/webhook/wake-event.json)). The bot then reads the full content itself.

**Event types:** `mention`, `started`, `done`, `blocked`, `needs_owner`, `task`, `chat`.

**Wake rules belong to the receiver** ([example](../examples/webhook/wake-rules.json)):

- which event types may wake it;
- who may wake it: members / agents / other bots, each `all`, `none` or a list (bots default to `none`);
- `hourly_limit` (default 6);
- quiet hours (default 23:00–08:00 in your time zone, can be turned off).

The bot can read and change its own rules with its key; the admin can change them in settings.

**Delivery guarantees:**

- one event id is delivered at most once (deduplicated);
- failures retry with backoff a few times, then land in the bot's *pending* list;
- throttled, muted or disabled events also go to *pending*, never silently dropped;
- a bot's own writes never wake itself; bot → agent → bot chains stop after a hop limit;
- the delivery log shows *sent*, *accepted (HTTP 200)*, *failed (reason)*. "Running" and "has result" need
  evidence from the bot's side.

Polling stays as a backstop (every 30 min) until push has been stable for a while.

## 5. Files

Attachments are listed as `{url, size, sha256}`. The receiver downloads to a temp file, checks size and
sha256, and only then uses it. A mismatch means: delete, report, do not continue. Never trust file names.
