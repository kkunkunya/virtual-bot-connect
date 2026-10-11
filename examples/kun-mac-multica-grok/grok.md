# Grok Bot

Notes from connecting real Grok Bots. Host names, addresses and keys are placeholders.

## Platform facts that shape the design

- All Grok Bots on one account **share one cloud computer**: files, logins and CLI credentials are shared.
- Routines (scheduled / webhook-triggered tasks), descriptions and memory are **per bot**. Connectors and saved
  skills are per account.
- The computer is **paused when idle** (we saw it drop off after ~15 minutes). `/workspace` persists; apt
  packages and `/etc/hosts` edits may be lost on reset, so a watchdog restores them.
- What we got: Debian, 8 cores, ~15 GiB RAM, with `sudo` and a TUN device. DNS went through a fake-IP proxy.

## Mac → bot computer (remote host)

- Both machines join your Tailscale network. Give the bot computer a node name (`<bot-host>` below).
- If Tailscale on the Mac runs in **userspace mode** (no admin rights), you cannot `ssh user@100.x.y.z`
  directly. Use a `ProxyCommand` through `tailscale nc` — see [examples/ssh/ssh_config.example](ssh/ssh_config.example).
- Run a normal `sshd` on the bot computer on a high port, public-key only. Pin the host key in `known_hosts`.
- Traffic may go through a DERP relay (~200 ms for us). `ControlMaster` makes repeated commands fast.

## Things on the bot computer

| Path | What |
|---|---|
| `/workspace/remote/ensure-remote.sh` | watchdog: restart Tailscale if offline > 15 s, restore `/etc/hosts` ([sketch](ssh/ensure-remote.sh)) |
| `/workspace/mailbox/{inbox,outbox}` | execution mailbox ([formats](mailbox/)) |
| `/workspace/mailbox/standing-instructions.md` | long-lived instructions ([example](standing-instructions.md)) |
| `/workspace/jobs/<task-id>/` | working folder per job; the only place result files may come from |
| `/workspace/remote/credentials/` | protected credentials (`0700` dir, `0600` files), loaded by the shell profile |
| `/workspace/remote/CREDENTIALS.md` | registry: what credential, why, how to revoke — no values |

A routine runs twice an hour (watchdog + check mailbox + check pending events). Webhook wake-ups make it
react immediately; the schedule is the backstop.

## Reconnecting after a pause

- A wake-up webhook (or any message to the bot) resumes the computer; the routine runs the watchdog first,
  then Tailscale comes back.
- From the Mac side, retry at the routine's scheduled windows, at most twice. If both fail, ask the owner to send
  the bot any message.
- Once connected, cancel the remaining retries and *continue the actual work* — "connected" is not the goal.

## Pitfalls we hit

- **Tailscale SSH "check" mode** blocks on an interactive approval → use plain `sshd` and turn off `--ssh`.
- **Fake-IP DNS proxy** made Tailscale's control-plane long-poll hang and the node looked offline → pin the
  control-plane host names to real IPs in `/etc/hosts` (the watchdog re-applies this).
- **macOS background services can't read external drives.** If `~/.ssh/config` includes a file on an external
  disk, the bridge service fails → give the bridge its own ssh config under the home folder.
- **`ProxyCommand` doesn't expand `%d`** here → use absolute paths.

## Credentials on the bot computer

- Put only what the work needs (e.g. Multica bot key, a GitHub token). Transfer over SSH stdin, never as
  arguments, never printed. Verify login from a new process and record it in the registry.
- Whole-machine reset is a separate test from "new shell still logged in". Report which one you did.

## Tried and dropped

- Bots without `sudo`/TUN can't join a tailnet as a host (we dropped one such bot platform).
- API-proxy hacks, email "doorbells", a self-hosted MCP server and a third-party relay server all worked in
  principle but were too long a chain or too much upkeep.
