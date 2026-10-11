# Adding a new bot

## Another bot on the same platform (e.g. a second Grok Bot)

Bots on one account share the cloud computer, so the network and logins are already there. Still verify the
new bot's own identity and workspace before trusting it.

1. Create the bot and name it (e.g. "Personal errands").
2. In Multica, add it under *External bots* (or create a personal token) and keep the key for step 4.
3. Paste the [standing instructions](../examples/standing-instructions.md) into its description / routine.
   Tell it its own name; it must send `from_bot` so replies come back to it.
4. Hand over the key through a protected file or stdin. Run `multica auth status` from a new shell.
5. Give it a routine with a webhook trigger, register that webhook with Multica, set wake rules.
6. Round-trip test: @-mention it from a ticket, check it wakes, reads the ticket and replies "via <name>".

## A bot on a new platform

Answer these first; they decide which channels are possible.

| Question | Decides |
|---|---|
| Does it have its own computer? `sudo`? TUN device? | can it join Tailscale as a remote host |
| Does the computer pause when idle? After how long? | do you need a watchdog and queued mailbox |
| Can it run shell commands and install a CLI? | can it use the `multica` CLI directly (preferred) |
| Does it have scheduled tasks? Webhook triggers? | polling fallback / instant wake-ups |
| Do several bots share one computer? | blast radius of a key stored there |

Then write a page for it under `docs/` (copy the shape of [grok.md](grok.md)) and add it to the
channel table in the README.

## Acceptance checklist

- [ ] Login checked from a fresh process (and, separately, after a reset if you tested that).
- [ ] Credentials only in the protected directory, registered without values; not in descriptions, routines,
      comments, mailbox messages or logs.
- [ ] One real round trip per channel you enabled.
- [ ] Reports distinguish *delivered*, *woken*, *has result*; anything unclear is marked "unknown".
- [ ] You know how to stop it (revoke key) and have tried it once.
