# Benchmark: why four agent repos spread, and what we borrowed

Snapshot taken 2026-10-11 from the GitHub API and each README. Star counts move; treat them as orders of
magnitude. "Not found" means we looked and could not verify it.

## The four repos

| | [chekusu/yobiru](https://github.com/chekusu/yobiru) | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) | [obra/superpowers](https://github.com/obra/superpowers) | [anthropics/skills](https://github.com/anthropics/skills) |
|---|---|---|---|---|
| What it is | agents talk and wake each other over Tailscale | content-creation skills for Claude Code / Codex | coding-agent methodology as skills | official Agent Skills examples |
| Stars (approx.) | ~45 (one day old) | ~26.5k | ~297k | ~180k |
| License | MIT | MIT | MIT | Apache 2.0 for most skills (per README) |

## Nine dimensions

| Dimension | yobiru | baoyu-skills | superpowers | anthropics/skills | **virtual-bot-connect now** |
|---|---|---|---|---|---|
| Header image / GIF | AI-generated concept image, captioned "not real screenshots" | none | none | none | banner from the author's comic mascot + animated flow GIF captioned "illustration" |
| First-screen value | "**Let your agents talk to each other.**" + one paragraph | one line: skills to work faster with AI agents | "a complete software development methodology for your coding agents" | "Skills are folders of instructions…" | tagline + one-sentence value + four-piece table |
| Give-to-your-agent one-liner | plugin install, then say "Set up Yobiru on this machine." | "Ask the Agent: Please install Skills from github.com/JimLiu/baoyu-skills" | "Fetch and follow instructions from &lt;raw URL&gt;/INSTALL.md" | `/plugin marketplace add anthropics/skills` | "Fetch and follow …/AGENTS.md" prompt, copy-paste block |
| Demo | concept image + three-agent scenario table | large screenshot galleries | text smoke test ("Let's make a react todo list") | example prompt | animated flow GIF + real example folder |
| Badges | none | none | none | one (skills.sh) | license, type, local agents, pocket bots, stars |
| Star curve | no | yes, star-history at the bottom | no | no | yes, star-history at the bottom |
| Bilingual README | EN / 简体中文 / 日本語 with a switcher | EN / 中文 with a switcher on line 3 | EN only | EN only | EN / 简体中文 with a switcher under the banner |
| AGENTS.md / llms.txt | none at root (has SPEC.md, plugin dirs) | CLAUDE.md + plugin dirs | AGENTS.md, GEMINI.md, ~10 per-harness plugin dirs | `.claude-plugin/`, SKILL.md under folders | AGENTS.md (setup playbook) + llms.txt |
| Launch social post | not found | not found (author is @dotey on X) | [launch blog post](https://blog.fsck.com/2025/10/09/superpowers/), same day as the repo | [Anthropic engineering post](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | drafts for X and Xiaohongshu, awaiting the owner's approval |

## What we borrowed, and from where

| Technique | Source | Where it shows up here |
|---|---|---|
| "Fetch and follow &lt;raw URL&gt;" one-liner that works in any agent | superpowers (OpenCode install) | README "Give this to your agent" → AGENTS.md |
| Ask-the-agent install as a quoted sentence | baoyu-skills ("Option 3: Ask the Agent") | same block, phrased as a prompt |
| Install, then one natural-language sentence that triggers setup | yobiru ("Set up Yobiru on this machine.") | the prompt asks the agent to interview the user first |
| Concept visual with an explicit "not a real screenshot" caption | yobiru | demo GIF caption |
| Honest per-integration status, including "not verified" | yobiru | "Works with" table |
| Every supported tool named above the fold | superpowers (per-harness table of contents) | badges + "Works with" table |
| "Try it in X / Y / Z" split by surface | anthropics/skills | "Works with" split by pocket bot / local agent |
| Language switcher near the top | baoyu-skills, yobiru | under the banner in both READMEs |
| Star-history chart as the last section | baoyu-skills | bottom of both READMEs |
| Scenario table (who contributes what) | yobiru | four-piece table |
| Launch post on day one, linked from the repo | superpowers | social drafts prepared alongside the release |

## What we chose not to copy

- **Plugin marketplaces** (superpowers, anthropics/skills, baoyu-skills): this repo ships no runnable package yet,
  so a plugin command would over-promise. Revisit once a minimal bridge is published (see Roadmap).
- **Big screenshot galleries** (baoyu-skills): we have no product UI to show; a fake gallery would mislead.

## Method, for reuse

1. Pick 3–4 repos: one direct peer, one viral in the same audience, one mega-viral, one official.
2. Pull metadata with `gh api repos/OWNER/REPO` and the raw README.
3. Fill the nine-dimension table, quoting the exact first-screen line and install sentence.
4. For each technique you adopt, write down the source repo and where it lands in yours.
5. Note what you deliberately did not copy, and why.
