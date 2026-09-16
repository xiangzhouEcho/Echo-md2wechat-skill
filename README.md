# Echo md2wechat Skill · Markdown 一键排版发布到微信公众号

![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-6B5B95?style=flat-square)

> 🌏 **English version: [README.en.md](./README.en.md)**

一个适配 Claude Code / Codex 等 Agent 环境的技能，把 Markdown 文件排版成**微信公众号可用的内联样式 HTML**，复制到剪贴板即可粘进编辑器；配置公众号凭据后还能自动传图、一键建草稿。

核心是一句话：**本地渲染，不依赖任何付费排版服务**。微信编辑器会剥离 `<style>` 和 class，所以所有样式必须内联到每个元素上——本技能用 `markdown` + Pygments 内联高亮 + `premailer` 内联 CSS 全程本地完成。

- **免凭据即用**：`md → 内联 HTML`，macOS 上以富文本写入剪贴板，直接 Cmd+V 粘进编辑器
- **三套主题**：`default`（蓝）/ `elegant`（绿·雅致）/ `minimal`（黑白极简）
- **微信适配**：全样式内联、每个 `<p>` 显式着色、外链转底部「参考链接」、代码块内联高亮、表格/引用样式化
- **可选草稿 API**：配 `AppID/AppSecret` 后，正文图走 `uploadimg`（不占配额）、封面走永久素材、`draft/add` 建草稿（只建草稿不群发）

## 30 秒开始

依赖由 [uv](https://github.com/astral-sh/uv) 按脚本内联声明自动安装，无需手动 `pip install`。

```bash
# 渲染 + 复制到剪贴板（默认，免凭据）→ 打开公众号编辑器 Cmd+V
uv run scripts/md2wechat.py article.md

# 换主题并在浏览器预览
uv run scripts/md2wechat.py article.md --theme elegant --open

# 一键建草稿（需凭据）
uv run scripts/md2wechat.py article.md --draft --cover cover.png
```

在 Agent 里直接说「把这篇 markdown 排版发到公众号」并给出文件即可自动触发。

## 选项

| 选项 | 说明 | 默认 |
|------|------|------|
| `--theme` | `default` / `elegant` / `minimal`（CLI 覆盖 frontmatter） | `default` |
| `--font-size` | 正文字号 px | 16 |
| `--no-citations` | 不把外链转成底部参考 | 默认转 |
| `--out` | 输出 HTML 路径 | 同名 `.wechat.html` |
| `--open` | 渲染后浏览器打开 | 关 |
| `--no-copy` | 不复制到剪贴板 | 默认复制(macOS) |
| `--draft` | 调官方 API 建草稿 | 关 |
| `--cover` | 封面图路径或 URL | frontmatter `cover:` |
| `--author` | 作者名 | frontmatter `author:` |

## Frontmatter（可选）

```yaml
---
title: 文章标题
author: 你的名字
digest: 一句话摘要（缺省取正文首段）
cover: cover.png
theme: elegant
source_url: https://原文链接
---
```

## 两种发布方式

1. **渲染 + 剪贴板（默认，免凭据、免 IP 白名单）**：产出内联 HTML 文件并把富文本写入剪贴板，直接粘进 mp 编辑器。任何人立即可用。
2. **草稿 API（需凭据）**：加 `--draft`。读取 `WECHAT_APPID`/`WECHAT_SECRET`（环境变量或 `~/.config/echo-md2wechat/config.json`），获取 access_token，上传正文图（`media/uploadimg`，不占素材配额）与封面（`material/add_material` → `thumb_media_id`），调用 `draft/add` 建草稿。**只建草稿，群发由你在后台手动确认。** 服务器公网 IP 需在公众号后台 IP 白名单内；动态 IP 可配 `WECHAT_PROXY_URL` 走固定出口。

## 凭据配置

环境变量：

```bash
export WECHAT_APPID=wx...
export WECHAT_SECRET=...
export WECHAT_PROXY_URL=http://...   # 可选，固定出口 IP
```

或 `~/.config/echo-md2wechat/config.json`：

```json
{ "appid": "wx...", "secret": "...", "proxy_url": "" }
```

## 依赖

- [uv](https://github.com/astral-sh/uv)（运行脚本、自动装依赖）
- Python 依赖（uv 自动处理）：`markdown`、`pygments`、`premailer`、`requests`、`beautifulsoup4`、`lxml`

## 自检

```bash
uv run scripts/selftest.py   # 离线，零网络
```

## 常见问题

| 症状 | 处理 |
|------|------|
| 粘进编辑器只有纯文本/标签 | 用默认富文本剪贴板复制；或 `--open` 后在浏览器全选复制 |
| `--theme` 不生效 | CLI 已覆盖 frontmatter 的 `theme:`，确认命令与版本 |
| 草稿报 `ip not in whitelist` | 把公网 IP 加入后台白名单，或配 `WECHAT_PROXY_URL` |
| 草稿报无封面 | `--cover` 指定 / frontmatter 写 `cover:` / 正文含图 |

## License

MIT © xiangzhouEcho
