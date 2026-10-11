# Wake webhook examples

- [`wake-event.json`](wake-event.json) — body of one wake-up. Summary and pointers only; the bot fetches the
  full content with its own key. Attachments carry `size` + `sha256`.
- [`request.http`](request.http) — the HTTP request Multica makes.
- [`wake-rules.json`](wake-rules.json) — the receiver's rules, as returned by the API. Note the response never
  contains the webhook URL or key, only `webhook_configured`.

Field names follow the design used in this project and may differ in your Multica version.
