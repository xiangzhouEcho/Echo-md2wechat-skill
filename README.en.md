# Echo md2wechat Skill · Publish Markdown to WeChat Official Accounts

![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-6B5B95?style=flat-square)

> 🌏 **中文版：[README.md](./README.md)**

A skill for Claude Code / Codex and similar agents that turns a Markdown file into the **inline-CSS HTML the WeChat Official Account editor requires**, copies it to the clipboard for pasting, and — when credentials are configured — uploads images and creates a draft via the official API.

The core idea: **local rendering, no paid formatting service**. The WeChat editor strips `<style>` and classes, so every style must be inlined onto each element — this skill does that with `markdown` + Pygments inline highlighting + `premailer` CSS inlining, entirely locally.

- **Zero-credential use**: `md → inline HTML`, copied to the clipboard as rich text on macOS, paste straight into the editor
- **Three themes**: `default` (blue) / `elegant` (green, refined) / `minimal` (black & white)
- **WeChat quirks handled**: all styles inlined, explicit `color` on every `<p>`, external links turned into bottom citations, inline-highlighted code, styled tables/blockquotes
- **Optional draft API**: with `AppID/AppSecret`, body images go through `uploadimg` (no material quota), the cover through permanent material, and `draft/add` creates a draft (draft only, never mass-sends)

## 30-Second Start

Dependencies are declared inline (PEP 723) and installed automatically by [uv](https://github.com/astral-sh/uv) — no manual `pip install`.

Run from **the directory where your Markdown lives**, invoking the script by **absolute path** (do not `cd` into the skill dir, or the input filename resolves to the wrong place):

```bash
SKILL=~/.claude/skills/echo-md2wechat-skill/scripts/md2wechat.py

# Render + copy to clipboard (default, no credentials) → paste with Cmd+V in the editor
uv run "$SKILL" article.md

# Pick a theme and preview in the browser
uv run "$SKILL" article.md --theme elegant --open

# One-shot draft (requires credentials)
uv run "$SKILL" article.md --draft --cover cover.png
```

Inside an agent, just say "format this markdown and publish it to my WeChat account" with the file — the skill triggers automatically.

## Options

| Option | Meaning | Default |
|--------|---------|---------|
| `--theme` | `default` / `elegant` / `minimal` (CLI overrides frontmatter) | `default` |
| `--font-size` | Body font size in px | 16 |
| `--no-citations` | Don't convert external links to bottom references | on |
| `--out` | Output HTML path | `<name>.wechat.html` |
| `--open` | Open in browser after rendering | off |
| `--no-copy` | Don't copy to clipboard | copy on (macOS) |
| `--draft` | Create a draft via the official API | off |
| `--cover` | Cover image path or URL | frontmatter `cover:` |
| `--author` | Author name | frontmatter `author:` |

## Frontmatter (optional)

```yaml
---
title: Article title
author: Your name
digest: One-line summary (defaults to the first paragraph)
cover: cover.png
theme: elegant
source_url: https://original-link
---
```

## Two Modes

1. **Render + clipboard (default, no credentials, no IP whitelist)**: produces an inline-CSS HTML file and puts rich text on the clipboard, ready to paste into the mp editor. Usable by anyone immediately.
2. **Draft API (needs credentials)**: add `--draft`. Reads `WECHAT_APPID`/`WECHAT_SECRET` (env vars or `~/.config/echo-md2wechat/config.json`), gets an access_token, uploads body images (`media/uploadimg`, no material quota) and the cover (`material/add_material` → `thumb_media_id`), and calls `draft/add`. **Draft only — you confirm the mass-send yourself in the backend.** The server's public IP must be in the account's IP whitelist; for a dynamic IP, set `WECHAT_PROXY_URL` for a fixed egress.

## Credentials

Environment variables:

```bash
export WECHAT_APPID=wx...
export WECHAT_SECRET=...
export WECHAT_PROXY_URL=http://...   # optional, fixed egress IP
```

Or `~/.config/echo-md2wechat/config.json`:

```json
{ "appid": "wx...", "secret": "...", "proxy_url": "" }
```

## Dependencies

- [uv](https://github.com/astral-sh/uv) (runs the scripts, auto-installs deps)
- Python deps (handled by uv): `markdown`, `pygments`, `premailer`, `requests`, `beautifulsoup4`, `lxml`

## Self-Test

```bash
uv run scripts/selftest.py   # offline, no network
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Only plain text/tags after pasting | Use the default rich-text clipboard copy; or `--open` then select-all copy in the browser |
| `--theme` has no effect | CLI overrides frontmatter `theme:`; check the command and version |
| Draft error `ip not in whitelist` | Add your public IP to the backend whitelist, or set `WECHAT_PROXY_URL` |
| Draft error: no cover | Use `--cover`, set frontmatter `cover:`, or include an image in the body |

## Echo WeChat Skill Family

Three skills form a pipeline: **search → download → format & publish**.

- [Echo-wechat-search-skill](https://github.com/xiangzhouEcho/Echo-wechat-search-skill) — search Official-Account articles by keyword, pipe straight to download
- [Echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill) — download articles without a certificate (single/album/batch; md/html/pdf + images/video/audio)
- [Echo-md2wechat-skill](https://github.com/xiangzhouEcho/Echo-md2wechat-skill) — format & publish Markdown to WeChat (inline CSS + clipboard + draft API) · this repo

## License

MIT © xiangzhouEcho
