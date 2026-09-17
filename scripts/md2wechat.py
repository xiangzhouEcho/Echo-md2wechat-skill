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

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import renderer
import themes
import wechat_api


def copy_html_to_clipboard(html: str) -> bool:
    if sys.platform != "darwin":
        return False
    tmp = Path(tempfile.gettempdir()) / "echo_md2wechat_clip.html"
    try:
        tmp.write_text(html, encoding="utf-8")
    except OSError:
        return False
    posix = str(tmp).replace('"', '\\"')
    script = f'set the clipboard to (read (POSIX file "{posix}") as «class HTML»)'
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def _standalone(html: str, title: str) -> str:
    return (
        f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        f"<title>{title}</title></head><body>{html}</body></html>"
    )


def do_render(md_path: Path, args) -> dict:
    text = md_path.read_text(encoding="utf-8")
    result = renderer.render_markdown(
        text,
        font_size=args.font_size,
        citations=not args.no_citations,
        force_theme=args.theme,
    )
    if args.author:
        result["author"] = args.author
    if args.cover:
        result["cover"] = args.cover
    if not args.no_embed_images and not args.draft:
        embedded_html, n, missing = renderer.embed_local_images(result["html"], md_path.parent)
        result["html"] = embedded_html
        if n:
            print(f"✓ 已内嵌 {n} 张本地图片为 base64（粘贴时微信会自动上传）")
        for m in missing:
            print(f"! 找不到本地图片，已跳过: {m}", file=sys.stderr)
    out_path = Path(args.out) if args.out else md_path.with_suffix(".wechat.html")
    out_path.write_text(_standalone(result["html"], result["title"]), encoding="utf-8")
    result["out_path"] = out_path
    print(f"✓ 已渲染: {result['title']}  ->  {out_path}  (主题: {result['theme']})")
    if not args.no_copy and copy_html_to_clipboard(result["html"]):
        print("✓ 富文本已复制到剪贴板，可直接粘贴进公众号编辑器")
    elif not args.no_copy:
        print("· 剪贴板复制不可用（非 macOS 或失败），请打开 HTML 后全选复制")
    if args.open:
        subprocess.run(["open", str(out_path)], check=False)
    return result


def do_draft(result: dict, md_path: Path, args) -> None:
    cfg = wechat_api.load_config()
    if not cfg["appid"] or not cfg["secret"]:
        print(
            "✗ 未配置公众号凭据，无法建草稿。\n"
            "  设置环境变量 WECHAT_APPID / WECHAT_SECRET，或写入 ~/.config/echo-md2wechat/config.json\n"
            "  并确保服务器公网 IP 已加入公众号后台 IP 白名单。",
            file=sys.stderr,
        )
        raise SystemExit(2)
    base_dir = md_path.parent
    proxy = cfg["proxy_url"]
    token = wechat_api.get_access_token(cfg["appid"], cfg["secret"], proxy)
    html = result["html"]
    srcs = [s for s in renderer.iter_images(html) if not s.startswith("https://mmbiz")]
    mapping: dict[str, str] = {}
    for src in srcs:
        try:
            url = wechat_api.upload_content_image(token, src, base_dir, proxy)
            mapping[src] = url
            print(f"  · 正文图已上传: {src[:50]}")
        except wechat_api.WeChatError as exc:
            print(f"  ! 跳过图片 {src[:50]}: {exc}", file=sys.stderr)
    if mapping:
        html = renderer.replace_image_src(html, mapping)
    cover = result.get("cover") or (srcs[0] if srcs else "")
    if not cover:
        print("✗ 无封面图：草稿需要封面。用 --cover 指定，或在 frontmatter 写 cover:，或让正文含至少一张图。", file=sys.stderr)
        raise SystemExit(2)
    thumb = wechat_api.upload_permanent_image(token, cover, base_dir, proxy)
    article = wechat_api.build_article(
        title=result["title"],
        content_html=html,
        thumb_media_id=thumb["media_id"],
        author=result.get("author", ""),
        digest=result.get("digest", ""),
        source_url=result.get("source_url", ""),
    )
    draft_id = wechat_api.create_draft(token, article, proxy)
    print(f"✓ 草稿已创建 media_id={draft_id}")
    print("  到 mp.weixin.qq.com 后台「草稿箱」检查并手动群发。")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="md2wechat.py",
        description="把 Markdown 文件渲染成微信公众号内联样式 HTML，复制到剪贴板可直接粘贴；配置凭据后可一键建草稿。",
    )
    ap.add_argument("file", help="Markdown 文件路径")
    ap.add_argument("--theme", choices=themes.theme_names(), help=f"主题 (默认 {themes.DEFAULT_THEME})")
    ap.add_argument("--font-size", type=int, default=16, help="正文字号 px (默认 16)")
    ap.add_argument("--no-citations", action="store_true", help="不把外链转成底部参考")
    ap.add_argument("--out", help="输出 HTML 路径 (默认与输入同名 .wechat.html)")
    ap.add_argument("--no-copy", action="store_true", help="不复制到剪贴板")
    ap.add_argument("--no-embed-images", action="store_true", help="不把本地图片内嵌为 base64")
    ap.add_argument("--open", action="store_true", help="渲染后用浏览器打开")
    ap.add_argument("--draft", action="store_true", help="调用官方 API 创建草稿 (需凭据)")
    ap.add_argument("--cover", help="封面图路径或 URL (建草稿用)")
    ap.add_argument("--author", help="作者名")
    args = ap.parse_args(argv)

    md_path = Path(args.file).expanduser()
    if not md_path.is_file():
        ap.error(f"找不到文件: {md_path}")

    result = do_render(md_path, args)
    if args.draft:
        do_draft(result, md_path, args)


if __name__ == "__main__":
    main()
