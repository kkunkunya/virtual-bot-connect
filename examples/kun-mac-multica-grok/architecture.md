# Architecture

## Roles in the office model

See [Kun's office model](../../docs/office-model.md). One device is one office, and the local agents are its
employees. Only the Grok Bot + Multica example is verified; webhook wake-up remains in live testing.
Dots, Muse, Cue and other local-agent integrations are untested.

- **Owner = goals and decisions.** The owner does not follow every device and thread.
- **Grok Bot = butler / general manager, with a cloud computer.** It coordinates the offices, follows up and
  reports. Other personal assistants are possible replacements to assess, not verified integrations.
- **Local device = office; local agents = employees.** They do work with that device's files and permitted access.
- **Multica = work hub and ledger.** It assigns work to employees and retains tasks, chats, state and audit.
- **Remote.** The bot's computer is in the cloud, not on your Mac. The Mac reaches it over Tailscale.

## Memory to retain across offices

Employees should leave useful decisions and experience in project memory. Tarot, toB, self-media and school
are project areas, not a list of separately verified offices. Automatic Google Drive backups are **in progress**:
Grok Bot every **2 days**, Multica every **7 days**. Recovery after changing devices or the general manager
is unverified; the backup schedule is not completed automation.

## Channels

| Channel | Direction | How | Notes |
|---|---|---|---|
| Direct CLI | Bot → Multica | `multica` CLI on the bot's computer, logged in with a bot key | read/search tickets and chats, comment, @ agents, update, upload files |
| Wake webhook | Multica → Bot | server POSTs the bot's routine webhook on subscribed events | summary only; the bot fetches details with the CLI |
| Remote host | Mac → Bot computer | `ssh <bot-host>` over Tailscale | sync a repo, run tests, fetch results |
| Execution mailbox | Multica → Bot computer → Multica | Mac bridge writes a task into the bot's inbox, bot replies with `task_result` | for long jobs; result files verified by size + sha256 |
| Polling | Bot → Multica | bot routine every 30 min | fallback only: picks up throttled, muted or failed wake-ups |

```mermaid
sequenceDiagram
  participant H as Home agent
  participant M as Multica
  participant B as Cloud bot
  H->>M: comment "@butler please check X" on ticket
  M->>M: check butler's wake rules (event type, hourly cap, quiet hours, who may wake it)
  alt allowed
    M->>B: POST webhook {event id, type, ticket, author, summary, link}
    B-->>M: HTTP 200 (delivered — not yet "running")
    B->>M: multica issue get / comment list (fetch full text)
    B->>M: multica issue comment add (reply, shown "via butler")
  else throttled / muted
    M->>M: keep in butler's pending list
    B->>M: next 30-min poll reads pending events
  end
```

## Ground rules

1. **Full rights, no tiers.** A bot added by an admin gets the admin's rights. Server-side permission checks still
   apply; there is no extra "confirm before delete" layer for bots.
2. **Drafts first for anything outward.** Public posts, messages to third parties, purchases: show a draft, wait
   for an explicit "send".
3. **Route by area, not by agent.** The bot only decides *which area* a request belongs to (coding, content,
   …). Which agent handles that area is a lookup table on the Multica side that you can change.
4. **Reply to whoever asked.** Messages carry `from_bot`; replies go back to the bot that started the thread.
5. **Keep sensitive projects off the cloud.** Decide up front which projects never go to bots.
6. **Credentials are registered, never written down.** Whatever credentials sit on the bot computer are listed
   (purpose + how to revoke, no values) in a registry file there. All bots on one account share that computer,
   so a key there *is* your identity — revoke it from the settings page if anything goes wrong.
7. **Report in detail.** Who, which ticket or chat, what was done, result and evidence, next step. Mark what was
   not read, not finished or still queued.
8. **Events wake, polling backs up** (borrowed from Yobiru): mentions both ways, webhook wake-ups, the receiver
   owns its wake rules, files as address + sha256.
