# Contributing

Notes from connecting other bots and platforms are very welcome.

- Add a page under `docs/` for a new bot or local agent (copy the shape of
  `examples/kun-mac-multica-grok/grok.md`) and a row in the "Works with" table of both READMEs.
- A whole setup of your own is welcome too: add it as `examples/<your-setup>/` with a short README.
- Examples use placeholders like `<bot-host>`, `<webhook-key>`. **Never** include real tokens, keys, webhook
  URLs, tailnet/node names, IPs, host-key fingerprints, email addresses or internal hostnames.
- Say what you actually tested and what you didn't.
- Images and GIFs count: no real hostnames, IPs, emails or tokens visible in screenshots, and strip metadata.
- Run a secret scan over the full history before opening a PR, e.g. `gitleaks git .`.
