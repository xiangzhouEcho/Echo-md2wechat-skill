# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "markdown",
#   "pygments",
#   "premailer",
#   "requests",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import renderer
import themes
import wechat_api

FIXTURE = """---
title: 单元测试标题
author: Echo
theme: default
cover: cover.png
---

# 一级标题

一段带 **粗体**、*斜体*、`行内代码`，一个[外链](https://example.com/a)与一个[另一外链](https://foo.bar/x)，还有一个[公众号链接](https://mp.weixin.qq.com/s/xyz)。

## 二级标题

- 项目一
- 项目二

> 引用文字

```python
def f(x):
    return x + 1
```

![图](pics/demo.png)

| A | B |
|---|---|
| 1 | 2 |
"""


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def main():
    r = renderer.render_markdown(FIXTURE)
    h = r["html"]
    check(r["title"] == "单元测试标题", "frontmatter 标题解析")
    check(r["author"] == "Echo", "frontmatter 作者解析")
    check(r["cover"] == "cover.png", "frontmatter 封面解析")
    check(r["theme"] == "default", "frontmatter 主题解析")
    check(r["digest"], "自动摘要非空")
    check("<style" not in h, "无 <style> 标签(微信会剥离)")
    check("class=" not in h, "无 class 属性(微信会剥离)")
    check(h.strip().startswith("<section style="), "根节点带内联样式")
    check("<p style=" in h, "段落带内联样式")
    check('style="color:' in h.replace("'", '"') or "style='color:" in h, "代码高亮为内联样式")
    check("<th style=" in h, "表头带内联样式")
    check("<blockquote style=" in h, "引用带内联样式")
    check("[1]" in h and "[2]" in h and "参考链接" in h, "外链转底部参考编号")
    check("mp.weixin.qq.com" in h, "公众号链接保留为可点 <a>")
    check("foo.bar" not in h.split("参考链接")[0], "外链在正文中已去可点性")

    imgs = renderer.iter_images(h)
    check("pics/demo.png" in imgs, "图片引用可枚举")
    mapped = renderer.replace_image_src(h, {"pics/demo.png": "https://mmbiz.qpic.cn/x.png"})
    check("https://mmbiz.qpic.cn/x.png" in mapped, "图片 src 可替换")

    check(set(themes.theme_names()) >= {"default", "elegant", "minimal"}, "内置至少三种主题")
    for name in themes.theme_names():
        css = themes.build_css(name, 16)
        check(".md2wx p" in css and "color:" in css.lower(), f"主题 {name} CSS 含段落颜色")

    art = wechat_api.build_article("t" * 100, "<section>x</section>", "MID", author="超长作者名一二三四五六七八九", digest="d" * 200, source_url="https://s")
    check(len(art["title"]) <= 64 and len(art["author"]) <= 8 and len(art["digest"]) <= 120, "草稿字段长度截断")
    check(art["thumb_media_id"] == "MID" and art["show_cover_pic"] == 1, "封面 media_id 映射")

    cfg = wechat_api.load_config()
    check(set(cfg.keys()) == {"appid", "secret", "proxy_url"}, "配置加载返回预期字段")

    import tempfile
    tmpd = Path(tempfile.mkdtemp(prefix="wxembed_"))
    (tmpd / "pics").mkdir()
    png = bytes.fromhex("89504e470d0a1a0a0000000d494844520000000100000001080600000037") + b"\x00" * 20
    (tmpd / "pics" / "demo.png").write_bytes(png)
    emb, n, missing = renderer.embed_local_images(r["html"], tmpd)
    check(n == 1 and "data:image/png;base64," in emb, "本地图片内嵌为 base64 data URI")
    check("pics/demo.png" not in emb, "内嵌后不再有本地相对路径")

    no_cite = renderer.render_markdown(FIXTURE, citations=False)["html"]
    check("参考链接" not in no_cite, "--no-citations 关闭底部参考")

    print("\nselftest: ALL PASS")


if __name__ == "__main__":
    main()
