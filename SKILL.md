---
name: echo-md2wechat-skill
description: Use when publishing a Markdown file to a WeChat Official Account (微信公众号) — converting Markdown into the inline-CSS HTML the WeChat editor requires, copying it to the clipboard for pasting, or creating a draft via the official API. Renders locally with no paid conversion service. Also triggers on Chinese phrasings such as markdown 转公众号, md 转微信, 发布到公众号, 公众号排版, 微信公众号草稿, markdown 排版微信, 一键排版.
---

# Echo md2wechat Skill — Markdown 发布到微信公众号

## Overview

把一个 Markdown 文件排版成微信公众号可用的**内联样式 HTML**，复制到剪贴板直接粘进编辑器；配置了公众号凭据时还能一键上传图片并建草稿。

**Core principle:** 本地渲染，不依赖任何付费转换服务。微信编辑器会剥离 `<style>` 和 class，所以所有样式必须内联到每个元素的 `style=""` 上——本 skill 用 markdown + Pygments 内联高亮 + premailer 内联 CSS 完成这件事。

## When to Use

- 有一个 `.md` 文件，想排版好发到公众号
- 想要「复制即粘贴」的富文本，直接贴进 mp 编辑器
- 配了 AppID/AppSecret，想自动传图 + 建草稿
- 需要把 Markdown 里的外链转成底部「参考链接」（微信外链不可点）

**Not for:**
- 自动**群发/发布**给粉丝 —— 只建草稿，群发需你在后台手动确认（安全考虑）
- 阅读数/评论等数据 —— 不涉及
- 依赖付费第三方排版 API —— 本 skill 完全本地渲染

## Quick Start

**执行位置（重要）**：在**你的 Markdown 文件所在目录**运行，并用**绝对路径**调用脚本——这样输入文件用相对名即可正确解析，脚本依赖也能就位。不要 `cd` 进 skill 目录（那会让 `article.md` 相对到 skill 目录而找不到）。本机脚本绝对路径为 `~/.claude/skills/echo-md2wechat-skill/scripts/md2wechat.py`。依赖由 uv 按脚本内联声明自动安装，无需手动 pip。

```bash
SKILL=~/.claude/skills/echo-md2wechat-skill/scripts/md2wechat.py

# 渲染并复制到剪贴板（默认，免凭据）——然后去公众号编辑器 Cmd+V
uv run "$SKILL" article.md

# 选主题 + 浏览器预览
uv run "$SKILL" article.md --theme elegant --open

# 一键建草稿（需 AppID/AppSecret + IP 白名单）
uv run "$SKILL" article.md --draft --cover cover.png
```

输入文件与 `--cover`、`--out` 都相对于你当前所在目录（即 md 文件目录），不是 skill 目录。

## Options

| 选项 | 说明 | 默认 |
|------|------|------|
| `--theme` | `default` / `elegant` / `minimal`（CLI 覆盖 frontmatter） | `default` |
| `--font-size` | 正文字号 px | 16 |
| `--no-citations` | 不把外链转成底部参考 | 默认转 |
| `--out` | 输出 HTML 路径 | 同名 `.wechat.html` |
| `--open` | 渲染后浏览器打开 | 关 |
| `--no-copy` | 不复制到剪贴板 | 默认复制(macOS) |
| `--draft` | 调官方 API 建草稿（需凭据） | 关 |
| `--cover` | 封面图路径或 URL（建草稿用） | frontmatter `cover:` |
| `--author` | 作者名 | frontmatter `author:` |

## Frontmatter

Markdown 顶部可选 YAML：`title`、`author`、`digest`（摘要，缺省取首段）、`cover`、`theme`、`source_url`。

## Two Modes

1. **渲染 + 剪贴板（默认，免凭据）**：md → 内联 HTML 文件，macOS 上以富文本写入剪贴板，直接粘进编辑器。任何人立即可用。
2. **草稿 API（需凭据）**：加 `--draft`。读 `WECHAT_APPID`/`WECHAT_SECRET`（环境变量或 `~/.config/echo-md2wechat/config.json`）→ 获取 token → 正文图走 `media/uploadimg`（不占素材配额）、封面走 `material/add_material` 取 `thumb_media_id` → `draft/add` 建草稿。**只建草稿，不群发**；服务器公网 IP 需在公众号后台 IP 白名单内。

## WeChat Quirks Handled

- 全部样式内联，无 `<style>`/`class`（微信会剥离）
- 每个 `<p>` 显式加 `color`，防止被编辑器重置为黑色
- 外链（非 mp.weixin.qq.com）转成 `文字[N]` + 底部「参考链接」
- 代码块 Pygments 内联高亮；行内代码、表格、引用均内联样式

## Common Mistakes

| 症状 | 处理 |
|------|------|
| 粘进编辑器只有纯文本/标签 | 用默认剪贴板复制（富文本）；或 `--open` 后在浏览器全选复制 |
| `--theme` 不生效 | frontmatter 里也写了 `theme:`；CLI 已覆盖 frontmatter，确认用的是新版 |
| 建草稿报 `ip not in whitelist` | 把当前公网 IP 加入后台白名单，或配 `WECHAT_PROXY_URL` 固定出口 |
| 建草稿报无封面 | `--cover` 指定、frontmatter 写 `cover:`，或正文至少含一张图 |
| 建草稿报 45004 | 摘要(digest)过长，已自动截断至 120 字，仍报则检查标题 |

## Verify

```bash
uv run ~/.claude/skills/echo-md2wechat-skill/scripts/selftest.py   # 离线自检，零网络
```
