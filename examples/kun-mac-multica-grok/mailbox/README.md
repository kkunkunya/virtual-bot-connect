# Execution mailbox

For jobs that must run on the bot's computer and report back with files. Everything else (reading tickets,
chatting, commenting) goes through the CLI directly.

```mermaid
sequenceDiagram
  participant M as Multica ticket
  participant Br as Mac bridge
  participant B as Bot computer
  Br->>B: write task.json into /workspace/mailbox/inbox (over SSH)
  Br->>B: POST the bot's wake webhook (task id only)
  B->>B: read inbox, run job in /workspace/jobs/TASK_ID/
  B->>B: write task_result.json into outbox (files listed with size + sha256)
  Br->>B: fetch result and each listed file
  Br->>Br: verify size + sha256
  Br->>M: comment with result, attach verified files, name any that failed
```

- One JSON file per message. [`task.json`](task.json) goes to the bot, [`task_result.json`](task_result.json)
  comes back.
- `to` addresses one bot when several share a computer; without it, the first bot to read takes it.
- Only task ids the bridge issued are accepted, each reported once.
- Result files must live under `/workspace/jobs/<task-id>/` (anything else is rejected, so a token file can't be
  sent by mistake). Defaults: 25 MB per file, 10 files per result.
- The wake webhook carries only the task id. If waking fails, delivery still stands; the scheduled check picks
  it up.
- With no open tasks the bridge connects only every 15 minutes, to cut SSH noise.
