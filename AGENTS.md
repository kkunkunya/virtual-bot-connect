# AGENTS.md

This file is for AI agents. There are two jobs you may have been given:

- **A. A user asked you to connect their local agents to their personal-assistant bot.** Follow the playbook below.
- **B. You are editing this repository.** Skip to [Maintaining this repo](#maintaining-this-repo).

---

## A. Setup playbook

virtual-bot-connect is a recipe, not an installer. You will build the smallest bridge that fits the user's tools,
using four pieces: **mailbox, wake-up, permissions, audit trail**. Read
[docs/primitives.md](docs/primitives.md) before proposing anything.

### Ground rules (do not break these)

1. **Never print, echo, paste, log or commit a secret** (tokens, webhook URLs and keys, passwords, SSH keys).
   Pass secrets through protected files (`0700` dir, `0600` file) or stdin, never as command-line arguments.
   If you need a secret, tell the user where to put it; do not ask them to paste it into chat.
2. **Propose before you change.** Show the plan and the list of files/settings you will touch; wait for a yes.
3. **Drafts first for outward actions.** Do not post publicly, message third parties or buy anything.
4. **Say what you verified and what you did not.** Keep *delivered*, *woken* and *done* apart; write "unknown"
   when unsure.

### Step 1 — Interview the user (ask, don't guess)

- Which pocket assistant bot? (Grok Bot, Dots, Muse, Cue, other.) More than one?
- Which local setup? (Claude Code, Codex, OpenCode, Pi, Multica, other.) One agent or several?
- Is there already a shared place both could use (a ticket system with CLI/API, a folder reachable from both,
  a Tailscale network)?
- Which projects must never be reachable from the bot side?

### Step 2 — Check what the bot can actually do

Run through the questions in [docs/adding-a-new-bot.md](docs/adding-a-new-bot.md#a-bot-on-a-new-platform)
with the user. The answers decide the paths:

| If the bot has… | Then the mailbox can be… | And it can be woken by… |
|---|---|---|
| its own computer with a shell | a CLI-driven ledger (e.g. Multica) or a folder mailbox | webhook routine, else schedule |
| only HTTP tools / connectors | an API-driven ledger | webhook routine, else schedule |
| neither | not connectable yet — tell the user and stop | — |

### Step 3 — Propose the smallest setup

Default choices, simplest first:

- **User already runs Multica** → follow [examples/kun-mac-multica-grok](examples/kun-mac-multica-grok/)
  (bot key + `multica` CLI on the bot side, `@agent` wakes local agents, optional webhook for waking the bot).
- **Single local agent (Claude Code / Codex / OpenCode / Pi)** → a folder mailbox (`inbox/`, `outbox/`, one JSON
  file per message, formats in [examples/kun-mac-multica-grok/mailbox/](examples/kun-mac-multica-grok/mailbox/))
  plus a watcher that starts the agent in its non-interactive mode. This path is documented but not yet verified
  by the maintainers — say so to the user, and keep the agent's own permission prompts on.
- **Both sides can run Yobiru on one tailnet** → consider [Yobiru](https://github.com/chekusu/yobiru) as the
  transport and apply the permission and audit rules from this repo on top.

Write the plan as: pieces → concrete choice → files/settings touched → how each path will be tested.

### Step 4 — Build, one path at a time

For each path: set it up, run **one real round trip**, record the evidence (ids, timestamps, HTTP status,
sha256), then move on. Use the standing-instruction template in
[examples/kun-mac-multica-grok/standing-instructions.md](examples/kun-mac-multica-grok/standing-instructions.md)
for the bot, adapted to the user's routing table.

### Step 5 — Hand over

Tell the user: what works (with evidence), what was not tested, where the keys live and how to revoke each one,
and what they need to do next (if anything).

---

## Maintaining this repo

Project facts that are stable and specific to this repository:

- It ships **documentation, a message spec and sanitized examples**. Bridge scripts and Multica server changes are
  not published here yet. Existing mailbox example fields are illustrative. The versioned
  [fast-access contract](docs/fast-access-protocol.md) has a runnable synthetic client under
  `examples/fast-access-client/`; real endpoint compatibility must be verified per deployment.
- The general recipe lives in `README*`, `docs/` and this file. Anything tied to one real setup lives under
  `examples/<setup>/`. The author's setup is [examples/kun-mac-multica-grok](examples/kun-mac-multica-grok/).
- **Public repo:** only placeholders such as `<bot-host>`, `<webhook-key>`. Never commit tokens, keys, passwords,
  real webhook URLs, Tailscale node names or IPs, emails, internal host or service names — in text, images or
  GIFs (check image metadata and visible text too). Scan the full Git history before pushing
  ([CONTRIBUTING.md](CONTRIBUTING.md)).
- Keep both READMEs in step: a change to one is a change to the other.
- When adding a bot or agent, record exactly what was verified and add a row to "Works with".
- Glossary: [CONTEXT.md](CONTEXT.md) · docs index: [docs/README.md](docs/README.md) · decisions:
  [docs/adr/](docs/adr/) · evidence pointers: [docs/evidence/INDEX.md](docs/evidence/INDEX.md) ·
  benchmark of README techniques: [research/benchmark.md](research/benchmark.md).
- Work tracking for this project lives in the maintainer's Multica workspace; the ledger is Multica, bots are its
  clients.
