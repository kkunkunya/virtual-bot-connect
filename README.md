<p align="center">
  <b>English</b> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-2dd4bf"></a>
  <img alt="Recipe, not a package" src="https://img.shields.io/badge/type-recipe%20%2B%20spec-a78bfa">
  <img alt="Verified combination: Grok Bot + Multica" src="https://img.shields.io/badge/verified-Grok%20Bot%20%2B%20Multica-2dd4bf">
  <a href="https://github.com/kkunkunya/virtual-bot-connect/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/kkunkunya/virtual-bot-connect?style=social"></a>
</p>

# virtual-bot-connect · Kun's offices

**I want a butler to coordinate my AI offices, so I can spend my attention on decisions.**

When each computer has its own agents, a task board and remote access still leave me following every thread.
My starting point is that human attention and the brain's I/O have a limit. I think someone who programs and
runs several projects needs a general manager to follow up, gather results and report back.

This repository shares my solution: a private network and a butler, one office per device, and project memory
I want to keep when the tools change. It contains the reasoning, a message spec and sanitized examples.
Start with the office model; adapt the wiring only after deciding how work should be managed.

## 1. A private network and a personal butler

Grok Bot provides a virtual computer. I connect it and my devices through Tailscale as a private network,
borrowing from Guo Yu's [Yobiru](https://github.com/chekusu/yobiru). The bot is the butler I talk to on my phone;
it contacts the offices and brings back a summary.

Grok Bot + Multica is the only combination verified here. Muse, Dots or Cue might take the butler role later,
but those integrations are **untested** and their capabilities need checking first.

## 2. One device is one office

Each device is an **office**, and the agents working there are its **employees**. Multica is the work hub and
ledger in the verified example: it assigns work and keeps tasks, conversations and results. The butler
coordinates the offices, follows up and reports to me as the owner.

I give goals and make the decisions that need me; I do not want to supervise every device and thread.
In my view, a board, more agents or a remote app still leave that coordination work with the owner.
The general-manager role is how I am trying to handle it.

```mermaid
flowchart TD
  Owner["Owner: goals and decisions"] <-->|"requests / summaries"| Butler["Butler / general manager: Grok Bot"]
  Butler <-->|"work / results"| Hub["Work hub and ledger: Multica"]
  Hub <--> Office["Verified office: local device and agents"]
  Butler -.-> More["Other device offices: model to extend"]
  Office --> Memory["Project memory: decisions and experience"]
  Memory -.-> Drive["Google Drive backups: in progress"]
```

The dotted paths show the intended extension and backup work, not additional verified deployments.
Details: [the office model](docs/office-model.md).

## 3. Memory is the moat I want to keep

After a task, an employee should leave useful decisions and experience in the project's memory, so the next
employee can continue. For me, the accumulated work in tarot, toB, self-media and school is the asset I want to
keep across devices and assistants.

**Automatic Google Drive backups are in progress:** the intended schedule is Grok Bot every **2 days** and
Multica every **7 days**. Those schedules and recovery have not been accepted as working here. Keeping the
whole setup running after changing an office or a general manager is the goal; it is not a verified recovery
claim. See [memory and backup status](docs/office-model.md#memory-and-backup-status).

## The wiring underneath the offices

The butler and employees need a mailbox, a wake-up, permissions and an audit trail. These are the connecting
pieces under the office model, with the verified and untested paths separated below.

<p align="center">
  <img src="assets/banner.png" alt="virtual-bot-connect: a mailbox, a wake-up, permissions and an audit trail between the AI assistant in your pocket and the agents on your own machine" width="100%">
  <br><sub>Concept illustration of the connecting pieces; not a deployment screenshot.</sub>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="Animated illustration: a request from the phone lands in the mailbox, wakes a local agent, the result returns with a sha256 receipt and every step is logged" width="88%">
  <br><sub><i>Animated illustration of the flow, not a screen recording.</i></sub>
</p>

## The four pieces

| | Piece | What it does | Rule of thumb |
|---|---|---|---|
| 📮 | **Mailbox / bridge** | One place both sides can write to and read from: a ticket system, a shared folder, a queue. | Messages carry **pointers, not payloads**. Files travel as `{url, size, sha256}` and are checked before use. |
| 🔔 | **Wake-up** | A new message wakes the receiver at once (webhook, `@mention`, file watcher) instead of everyone polling. | **The receiver decides who may wake it**: event types, hourly cap, quiet hours. Polling stays as the backstop. |
| 🔐 | **Permissions** | Each bot gets its own revocable key; outward actions need your explicit yes. | **Drafts first** for anything public, paid or sent to third parties. Keys go in protected files, never in chat or argv. |
| 🧾 | **Audit trail** | Every request, wake-up, result and file is recorded with who did it ("via &lt;bot&gt;"). | Keep **delivered ≠ woken ≠ done** apart. Write "unknown" rather than guess. |

Full write-up with options for each piece: [docs/primitives.md](docs/primitives.md).

## How the connecting pieces fit together

This is a generic flow. Only Grok Bot + Multica is verified; the webhook return path remains in live testing
and the other integrations are untested.

```mermaid
flowchart LR
  You["📱 You"] <-->|chat| Bot["Pocket assistant bot<br/>Grok Bot · Dots · Muse · Cue"]
  Bot -->|"📮 drop a task<br/>(own key, shown 'via bot')"| Box[("Mailbox / bridge<br/>tickets · folder · queue")]
  Box -->|"🔔 wake-up<br/>@mention · watcher"| Agents["Local agents<br/>Claude Code · Codex · OpenCode · Pi · Multica"]
  Agents -->|"result + files<br/>{url, size, sha256}"| Box
  Box -->|"🔔 wake-up<br/>webhook, summary only"| Bot
  Box --- Log["🧾 Audit trail<br/>who · what · delivered / woken / done"]
  Rules["🔐 Permissions<br/>per-bot keys · wake rules · drafts first"] -.-> Box
```

## What is verified, in testing or untested

The recipe is generic; one combination has been run on a real account so far. Status is stated honestly.

| Side | Tool | What it needs to provide | Status |
|---|---|---|---|
| Pocket bot | **Grok Bot** | own cloud computer with shell, webhook-triggered routines | ✅ bot → Multica via CLI and Mac → bot over SSH verified · 🚧 live acceptance of the webhook wake-up in progress · [example](examples/kun-mac-multica-grok/) |
| Pocket bot | Dots (OpenAI) · Muse (Meta) · Cue (Manus) | a way to write to the mailbox (shell, HTTP, or tool call) and a way to be woken (webhook or schedule) | 🧪 untested · [checklist](docs/adding-a-new-bot.md) |
| Local agents | **Multica** | tickets/chats as the mailbox, `@agent` as the wake-up | ✅ verified (same example) |
| Local agents | Claude Code · Codex · OpenCode · Pi | a non-interactive mode a watcher can start (`claude -p`, `codex exec`, `opencode run`, …) | 🧪 pattern documented, not yet verified |

Got another combination working? A pull request with a page under `docs/` and one row here is the best
contribution. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Verified office example: a Mac, Multica and Grok Bot

[`examples/kun-mac-multica-grok/`](examples/kun-mac-multica-grok/) is the author's own working setup, sanitized:

- **Mailbox:** Multica tickets and chats; a Mac-side bridge for long jobs that must run on the bot's computer.
- **Wake-up:** `@mention` wakes home agents; Multica POSTs a summary to the Grok Bot's routine webhook (built server-side; live acceptance in progress).
- **Permissions:** a bot key with "via &lt;bot&gt;" marking, receiver-owned wake rules (6/hour, quiet 23:00–08:00).
- **Audit trail:** everything lives in Multica; result files arrive with size + sha256.
- **Remote host:** agents on the Mac SSH into the bot's cloud computer over Tailscale.

## Compact activity reads

The [fast-access v1 protocol](docs/fast-access-protocol.md) and
[Python/SQLite example](examples/fast-access-client/) demonstrate compact reads,
SSE notifications and crash-safe summary caching. Run the synthetic demo without
credentials or dependencies; real deployment compatibility remains to be verified.

## Lessons from daily use

- **Split the roles:** the pocket bot is the butler (routes, follows up, accepts and merges by your rules); the
  agent platform assigns work and keeps the record. People are pulled in only for risky steps.
- **Push setup traps:** the `Authorization` header value includes the scheme, `Bearer <token>`; quiet hours follow the owner's time
  zone; an hourly cap that is too low holds back real events.
- **Wake-up limits that behave:** blocked wakes return a clear error, people are never rate-limited, wakes for the
  same task are merged, and stopping a task stops its related runs.
- **Key rotation:** check who uses a key before deleting it; a dead key marks the client offline, reassigns its
  work and notifies you.
- **Patrol and memory:** check what is duplicated or stuck, and leave decisions and experience in project memory.
  Automatic Google Drive backups are in progress: Grok Bot every 2 days, Multica every 7 days; recovery is unverified.
- **Results with images ship as one phone-friendly page.**

Details: [docs/lessons-learned.md](docs/lessons-learned.md)

## FAQ

**Is this an app I install?**
No. It is a recipe, a message spec and worked examples. Your agent reads them and builds the small glue your setup
needs. The bridge scripts and Multica server changes from the example are not published yet (see Roadmap).

**How is this different from [Yobiru](https://github.com/chekusu/yobiru)?**
Yobiru is a working transport: agents on a Tailscale network send each other messages, files and wake-ups. This
repo explains my office model: a butler coordinates device offices, Multica keeps the work record, and
project memory is intended to survive tool changes. The connecting pieces include permissions and drafts-first rules. Our wake-up design borrows from Yobiru.
Yobiru is a candidate mailbox transport; its integration with this setup is untested.

**Do I need Multica?**
No. Multica is the ledger in the example because it already has tickets, chats, `@mention` wake-ups and an audit
log. A shared folder plus a watcher, or a reachable queue, is a possible alternative; those integrations are untested here.

**Do I need Tailscale?**
Tailscale connects the devices and the bot computer in my office setup. A different private network may fit
your environment. A mailbox or webhook alone can be designed without that network; that does not reproduce
the full office setup, and alternative deployments are untested here.

**Is it safe to give a bot a key to my agents?**
Give each bot its own key that you can revoke in one click, show its writes as "via &lt;bot&gt;" so they never
count as your own approval, keep outward actions as drafts, and keep sensitive projects off the bot side
entirely. Details in [docs/primitives.md](docs/primitives.md#-permissions).

**My bot has no shell. Can it still join?**
Maybe. It needs some way to write into the mailbox (an HTTP tool, an email, a connector) and some way to be
woken. Run the [new-bot checklist](docs/adding-a-new-bot.md) first; it tells you which paths are possible.

## Roadmap

- [x] Working example: Mac + Multica + Grok Bot (direct CLI, remote host, execution mailbox)
- [x] Vendor-neutral write-up of the four pieces
- [ ] Automatic Google Drive backups: Grok Bot every 2 days, Multica every 7 days (in progress; recovery unverified)
- [ ] Live acceptance of the Multica → Grok Bot wake webhook
- [ ] Minimal folder-mailbox + watcher that wakes Claude Code / Codex / OpenCode, with a real round trip
- [ ] Verified pages for Dots, Muse and Cue
- [ ] Publish the Mac bridge script (sanitized)
- [ ] Yobiru as a drop-in mailbox transport

## Adapting the model to your own setup (optional)

After reading the office model, you can ask an agent to assess your environment. Other local-agent
integrations are untested; this prompt starts a plan, not a proven installation.

```text
Fetch and follow https://raw.githubusercontent.com/kkunkunya/virtual-bot-connect/main/AGENTS.md
and https://raw.githubusercontent.com/kkunkunya/virtual-bot-connect/main/docs/office-model.md
to plan a butler and device offices for my own setup. First ask me which bot I use and which local agent
setup I run, then propose the smallest setup before changing anything. Never print, paste or
commit any of my keys.
```

Your agent reads the playbook, interviews you, checks what your bot can actually do (shell? webhooks? schedule?),
and builds the smallest bridge that fits. Nothing here is a black-box installer: every step is a document you can
read first.

## Repository layout

```text
README.md · README.zh-CN.md   office model and verification status (English / 中文)
AGENTS.md                     office narrative, maintainer rules and optional setup playbook
llms.txt                      index for LLMs
docs/
  office-model.md             butler · device offices · memory and backup status
  primitives.md               mailbox · wake-up · permissions · audit trail, with options
  adding-a-new-bot.md         checklist for any new bot or platform
  lessons-learned.md          what daily use taught us (roles, push, limits, keys, patrol, memory, backups in progress)
examples/
  kun-mac-multica-grok/       the author's real setup: Multica + Grok Bot + Tailscale
research/
  benchmark.md                what we borrowed from Yobiru, baoyu-skills, Superpowers, anthropics/skills
  yobiru.md · yobiru.zh-CN.md notes on Yobiru's wake-up design
```

## Acknowledgements

- **[Yobiru](https://github.com/chekusu/yobiru)** by Guo Yu ([@turingou](https://x.com/turingou)) for the wake-up
  model: receiver-owned wake rules, small messages that point to content, sha256-checked files, and keeping
  *delivered / woken / done* apart. Notes: [research/yobiru.md](research/yobiru.md).
- README structure borrowed from [Superpowers](https://github.com/obra/superpowers) (the "fetch and follow"
  one-liner), [baoyu-skills](https://github.com/JimLiu/baoyu-skills) (ask-your-agent install, star history,
  language switcher), [Yobiru](https://github.com/chekusu/yobiru) (labelled concept visuals, honest status) and
  [anthropics/skills](https://github.com/anthropics/skills) ("works with" by surface). Full comparison:   [research/benchmark.md](research/benchmark.md).
- Thanks to [Multica](https://github.com/multica-ai/multica) and [Tailscale](https://tailscale.com).

Product names belong to their owners; listing them does not imply endorsement.

## Star history

<a href="https://star-history.com/#kkunkunya/virtual-bot-connect&Date">
  <img src="https://api.star-history.com/svg?repos=kkunkunya/virtual-bot-connect&type=Date" alt="Star history chart" width="600">
</a>

## License

[MIT](LICENSE)
