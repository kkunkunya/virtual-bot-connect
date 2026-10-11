# Contributing

Notes from connecting other bots and platforms are very welcome.

- Add a page under `docs/` for a new platform (copy the shape of `docs/grok.md`) and a row in the README.
- Examples use placeholders like `<bot-host>`, `<webhook-key>`. **Never** include real tokens, keys, webhook
  URLs, tailnet/node names, IPs, host-key fingerprints, email addresses or internal hostnames.
- Say what you actually tested and what you didn't.
- Run a secret scan before opening a PR, e.g. `gitleaks git .`.
