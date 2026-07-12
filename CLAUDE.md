# media-briefing-bot

Daily Vietnamese-language news digest for journalism/media-industry topics (AI in newsrooms, press freedom, journalism tools). Sources in `config/sources.yaml`. Repo: https://github.com/hangkrypton/media-briefing-bot (must stay **public** — see below).

## Architecture: split local + cloud

The pipeline is split across two runtimes because the Claude Code cloud sandbox (CCR) has two hard limits discovered by trial and error:

1. **Network egress is blocked for nearly all external domains** — even via the WebFetch tool, even Wikipedia as a control. Only `github.com` worked. No self-serve setting was found anywhere in claude.ai to allow-list domains; treat as a hard platform limit, not a misconfiguration.
2. **The GitHub connection available to CCR routines is read-only** — cloning/pulling a public repo works, but `git push` and GitHub MCP write tools (`push_files`, `create_or_update_file`) all return `403 Resource not accessible by integration`. No GitHub App with write scope was ever found installed for this account, despite reconnecting/revoking the OAuth connection multiple times.

Consequence: the repo must stay **public** (cloud can only read it, and only if public), and the split is:

- **Local (`scripts/run_daily.sh`, via macOS launchd, `~/Library/LaunchAgents/com.hangkrypton.media-briefing-bot.plist`, 20:30 Asia/Saigon daily)**: runs `python -m scripts.main` — fetches RSS/Atom feeds, dedupes against `state/seen.json`, writes `new_items.json`, commits + pushes both files. This is the only part of the system that touches the open internet or writes to git.
- **Cloud routine ("Media Briefing Bot - Daily", claude.ai routines, cron `0 14 * * *` UTC = 21:00 Asia/Saigon, 30 min after the local job to give it time to push)**: reads `new_items.json` from the repo (no fetching, no git writes), searches Gmail for 3 newsletter sources via the Gmail MCP connector, writes the Vietnamese 3-section summary ("Tin mới" / "Phân tích chuyên sâu" / "Công cụ mới"), sends it via Outlook (`outlook_send_mail`, real send — not draft) to `hangthu@vnexpress.net`, and saves a copy to OneDrive (`Media Briefing/YYYY-MM-DD.md`) via the Microsoft 365 connector. Managed at https://claude.ai/code/routines — edit the routine's prompt there (or via the `/schedule` skill), not in this repo.

Any future change that needs to fetch external content or commit to git from the cloud side will hit the same wall — do that work in `scripts/run_daily.sh` instead and have the cloud routine only read + use MCP connectors.

## Local environment gotchas

- System Python is 3.9.6 (`/usr/bin/python3`) — **no `X | None` union type syntax**; add `from __future__ import annotations` at the top of any new module using it (already done in `scripts/discover_feed.py`).
- `git` on this machine uses `credential.helper=osxkeychain` with a cached PAT — non-interactive `git push` from launchd works as-is. If pushes start failing with an auth prompt, the PAT likely expired (fine-grained tokens were created with a short expiry) and needs regenerating at github.com/settings/tokens.
- Test the local job manually before trusting the schedule: `./scripts/run_daily.sh`. Logs from the automated launchd run go to `~/Library/Logs/media-briefing-bot.log` / `.err.log`.

## Known gaps

- 4 of 19 RSS sources have no auto-discoverable feed (Superhuman AI, OpenAI Blog, Anthropic News, Joe Amditis/jamditis.com) — `discover_feed.py` logs "Không tìm được feed" for these; add an explicit `feed_url:` in `sources.yaml` if they matter.
