# Kun's office model

[中文](office-model.zh-CN.md) · [Overview](../README.md)

I have a limited amount of attention to spend on work. When agents are spread across devices, I want a
butler to coordinate the offices and bring me the decisions, rather than following each thread myself.
This is the reasoning behind virtual-bot-connect and the solution I am building around it.

## A private network and a butler

In the verified example, Grok Bot supplies a virtual computer, connected to the local device through
Tailscale. The bot is my personal butler and general manager: it takes a goal, contacts the relevant office,
follows up and gathers results. Guo Yu's [Yobiru](https://github.com/chekusu/yobiru) inspired the private-network
and wake-up design. It provides communication between agents; task management remains a separate concern.

## Devices, employees and the work hub

One device is one **office**. Its agents are the **employees**, with the files and permitted access they need
on that device. **Multica** is the work hub and ledger in this example; it assigns tasks and keeps the record.
The butler coordinates and reports. The owner gives goals and handles decisions that require a person.

For me, a board, additional agents and a remote app still leave the owner managing the work across threads.
That is why I want a general manager. This is my judgment about my workflow, not a claim that those tools
cannot coordinate work for anyone else.

An office is a device, not a project. Tarot, toB, self-media and school are project areas whose knowledge I
want to keep; listing them does not imply one verified device or integration for each area. The wider
multi-office arrangement is a model to extend from the verified local-device and cloud-computer example.

## Memory and backup status

After work, an employee should leave the useful decisions and experience in project memory. Those records
are the accumulated asset I want to carry into the next office or the next general manager. The audit trail
answers what happened; project memory preserves what the next employee needs to know.

| Item | Intended arrangement | Current status |
|---|---|---|
| Grok Bot memory backup | Automatic backup to Google Drive every **2 days** | **In progress**, not accepted as working |
| Multica memory backup | Automatic backup to Google Drive every **7 days** | **In progress**, not accepted as working |
| Changing offices or the general manager | Continue from retained project memory and backups | Design goal; end-to-end recovery unverified |

These are the current planned backup cadences, not completed automation. This repository provides no backup
installer and no proof of a successful restore. Earlier daily/private-repository export advice is replaced
by this status. Neither a task result nor a record in Multica proves that a Google Drive backup ran.

## Evidence boundary

- **Verified:** Grok Bot → Multica through the CLI, Multica agent wake-ups, local device → Grok Bot computer
  over Tailscale/SSH, and the execution-mailbox path described in the [sanitized example](../examples/kun-mac-multica-grok/).
- **In live testing:** Multica → Grok Bot webhook wake-up. Server implementation does not prove the bot woke
  or completed work; delivered, woken and done remain separate states.
- **Untested:** Dots, Muse, Cue, standalone Claude Code/Codex/OpenCode/Pi bridges, and Yobiru as a transport
  for this setup. A possible replacement is not a supported integration.
- **In progress:** the Google Drive backup schedules above. Recovery and portability remain goals.

## The connecting pieces

The [mailbox, wake-up, permissions and audit trail](primitives.md) connect the butler and employees. Network
reachability does not grant access to projects or credentials. Existing draft-first and permission rules
remain in place; retaining memory does not transfer approval or secrets to a new bot.

For a new environment, read the [capability checklist](adding-a-new-bot.md) before adapting the
[optional setup playbook](../AGENTS.md#a-setup-playbook). For the Yobiru comparison, see the
[versioned research notes](../research/yobiru.md).
