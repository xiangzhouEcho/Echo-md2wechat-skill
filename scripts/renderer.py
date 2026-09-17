from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import markdown as mdlib
from bs4 import BeautifulSoup
from premailer import Premailer

import themes

_FRONTMATTER = re.compile(r"^﻿?---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_WEIXIN_HOSTS = ("mp.weixin.qq.com", "weixin.qq.com")


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        return {}, text
    meta = _parse_yaml_block(m.group(1))
    return meta, text[m.end():]


def _parse_yaml_block(block: str) -> dict:
    meta: dict = {}
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            meta[key] = val
    return meta


def _first_paragraph_text(soup: BeautifulSoup, limit: int = 100) -> str:
    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if txt:
            return txt[:limit]
    return ""


def _is_external(href: str) -> bool:
    if not href:
        return False
    parts = urlparse(href)
    if parts.scheme not in ("http", "https"):
        return False
    host = parts.netloc.lower()
    return not any(host == h or host.endswith("." + h) for h in _WEIXIN_HOSTS)


def _convert_links_to_citations(soup: BeautifulSoup) -> None:
    refs: list[str] = []
    seen: dict[str, int] = {}
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if not _is_external(href):
            continue
        if href in seen:
            idx = seen[href]
        else:
            idx = len(refs) + 1
            seen[href] = idx
            refs.append(href)
        text = a.get_text() or href
        sup = soup.new_tag("span")
        sup.string = f"{text}[{idx}]"
        a.replace_with(sup)
    if not refs:
        return
    container = soup.find(class_="md2wx") or soup
    block = soup.new_tag("section")
    block["class"] = "md2wx-refs"
    title = soup.new_tag("p")
    title["class"] = "md2wx-refs-title"
    title.string = "参考链接"
    block.append(title)
    for i, url in enumerate(refs, 1):
        line = soup.new_tag("p")
        line.string = f"[{i}] {url}"
        block.append(line)
    container.append(block)


def render_markdown(
    text: str,
    theme: str = themes.DEFAULT_THEME,
    font_size: int = 16,
    citations: bool = True,
    force_theme: str | None = None,
) -> dict:
    meta, body = split_frontmatter(text)
    theme = force_theme or meta.get("theme") or theme
    tconf = themes.get_theme(theme)
    md = mdlib.Markdown(
        extensions=["extra", "codehilite", "sane_lists", "admonition", "toc"],
        extension_configs={
            "codehilite": {
                "noclasses": True,
                "pygments_style": tconf["pygments_style"],
                "guess_lang": False,
            }
        },
    )
    inner = md.convert(body)
    wrapper = f'<section class="md2wx">{inner}</section>'
    css = themes.build_css(theme, font_size)
    full = f"<style>{css}</style>{wrapper}"
    soup = BeautifulSoup(full, "html.parser")
    if citations:
        _convert_links_to_citations(soup)
    prepared = str(soup)
    inlined = Premailer(
        prepared,
        remove_classes=True,
        keep_style_tags=False,
        disable_validation=True,
        cssutils_logging_level="CRITICAL",
    ).transform()
    inlined = _extract_section(inlined)
    result_soup = BeautifulSoup(inlined, "html.parser")
    title = meta.get("title") or _extract_title(result_soup, body)
    digest = meta.get("digest") or _first_paragraph_text(result_soup)
    return {
        "html": inlined,
        "title": title,
        "author": meta.get("author", ""),
        "digest": digest,
        "cover": meta.get("cover", ""),
        "source_url": meta.get("source_url", meta.get("source", "")),
        "theme": theme,
        "meta": meta,
    }


def _extract_section(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    sec = soup.find("section")
    return str(sec) if sec else html


def _extract_title(soup: BeautifulSoup, body: str) -> str:
    h1 = soup.find(["h1", "h2"])
    if h1:
        t = h1.get_text(strip=True)
        if t:
            return t
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "未命名文章"


def embed_local_images(html: str, base_dir: Path) -> tuple[str, int, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    embedded = 0
    missing: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith(("http://", "https://", "data:")):
            continue
        path = Path(src) if Path(src).is_absolute() else (base_dir / src)
        path = path.expanduser()
        if not path.is_file():
            missing.append(src)
            continue
        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        data = base64.b64encode(path.read_bytes()).decode()
        img["src"] = f"data:{mime};base64,{data}"
        embedded += 1
    return str(soup), embedded, missing


def iter_images(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [img.get("src", "") for img in soup.find_all("img") if img.get("src")]


def replace_image_src(html: str, mapping: dict[str, str]) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src in mapping:
            img["src"] = mapping[src]
    return str(soup)
