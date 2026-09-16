from __future__ import annotations

import ipaddress
import json
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import requests

API_BASE = "https://api.weixin.qq.com/cgi-bin"
CONFIG_PATHS = [
    Path("md2wechat.json"),
    Path.home() / ".config" / "echo-md2wechat" / "config.json",
    Path.home() / ".echo-md2wechat.json",
]


class WeChatError(Exception):
    pass


class MissingCredentials(Exception):
    pass


def load_config() -> dict:
    cfg: dict = {}
    for path in CONFIG_PATHS:
        if path.is_file():
            try:
                cfg.update(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
            break
    appid = os.environ.get("WECHAT_APPID") or cfg.get("appid")
    secret = os.environ.get("WECHAT_SECRET") or cfg.get("secret")
    proxy = os.environ.get("WECHAT_PROXY_URL") or cfg.get("proxy_url")
    return {"appid": appid, "secret": secret, "proxy_url": proxy}


def _proxies(proxy_url: str | None) -> dict | None:
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _check_resp(data: dict, context: str) -> None:
    if data.get("errcode") not in (0, None):
        raise WeChatError(f"{context} 失败: errcode={data.get('errcode')} errmsg={data.get('errmsg')}")


def get_access_token(appid: str, secret: str, proxy_url: str | None = None) -> str:
    if not appid or not secret:
        raise MissingCredentials("缺少 WECHAT_APPID / WECHAT_SECRET")
    resp = requests.get(
        f"{API_BASE}/token",
        params={"grant_type": "client_credential", "appid": appid, "secret": secret},
        proxies=_proxies(proxy_url),
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        _check_resp(data, "获取 access_token")
        raise WeChatError(f"获取 access_token 失败: {data}")
    return data["access_token"]


def _guard_remote(url: str) -> None:
    host = urlparse(url).hostname or ""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise WeChatError(f"无法解析图片域名: {host}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise WeChatError(f"拒绝下载内网/本地地址图片: {host}")


def _load_image_bytes(src: str, base_dir: Path) -> tuple[bytes, str]:
    if src.startswith("http://") or src.startswith("https://"):
        _guard_remote(src)
        resp = requests.get(src, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        name = Path(urlparse(src).path).name or "image.jpg"
        return resp.content, name
    path = (base_dir / src).expanduser().resolve() if not Path(src).is_absolute() else Path(src)
    if not path.is_file():
        raise WeChatError(f"找不到本地图片: {src}")
    return path.read_bytes(), path.name


def _ext_name(name: str) -> str:
    if "." in name:
        return name
    return name + ".jpg"


def upload_content_image(token: str, src: str, base_dir: Path, proxy_url: str | None = None) -> str:
    data, name = _load_image_bytes(src, base_dir)
    resp = requests.post(
        f"{API_BASE}/media/uploadimg",
        params={"access_token": token},
        files={"media": (_ext_name(name), data)},
        proxies=_proxies(proxy_url),
        timeout=60,
    )
    j = resp.json()
    if "url" not in j:
        _check_resp(j, "上传正文图片")
        raise WeChatError(f"上传正文图片失败: {j}")
    return j["url"]


def upload_permanent_image(token: str, src: str, base_dir: Path, proxy_url: str | None = None) -> dict:
    data, name = _load_image_bytes(src, base_dir)
    resp = requests.post(
        f"{API_BASE}/material/add_material",
        params={"access_token": token, "type": "image"},
        files={"media": (_ext_name(name), data)},
        proxies=_proxies(proxy_url),
        timeout=60,
    )
    j = resp.json()
    if "media_id" not in j:
        _check_resp(j, "上传封面素材")
        raise WeChatError(f"上传封面素材失败: {j}")
    return j


def build_article(title: str, content_html: str, thumb_media_id: str, author: str = "", digest: str = "", source_url: str = "") -> dict:
    return {
        "title": title[:64],
        "author": author[:8] if author else "",
        "digest": digest[:120],
        "content": content_html,
        "thumb_media_id": thumb_media_id,
        "content_source_url": source_url,
        "show_cover_pic": 1 if thumb_media_id else 0,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }


def create_draft(token: str, article: dict, proxy_url: str | None = None) -> str:
    resp = requests.post(
        f"{API_BASE}/draft/add",
        params={"access_token": token},
        data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
        proxies=_proxies(proxy_url),
        timeout=60,
    )
    j = resp.json()
    if "media_id" not in j:
        _check_resp(j, "创建草稿")
        raise WeChatError(f"创建草稿失败: {j}")
    return j["media_id"]
