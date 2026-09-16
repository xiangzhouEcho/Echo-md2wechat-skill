from __future__ import annotations

_BASE = """
.md2wx {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: {font_size}px;
  color: {text};
  line-height: 1.75;
  letter-spacing: 0.02em;
  word-break: break-word;
  background: {bg};
  padding: 16px;
}}
.md2wx p {{
  color: {text};
  margin: 16px 0;
  line-height: 1.75;
}}
.md2wx h1, .md2wx h2, .md2wx h3, .md2wx h4 {{
  color: {heading};
  font-weight: 700;
  line-height: 1.4;
  margin: 28px 0 16px;
}}
.md2wx h1 {{ font-size: 1.5em; border-bottom: 2px solid {accent}; padding-bottom: 8px; }}
.md2wx h2 {{ font-size: 1.3em; border-left: 4px solid {accent}; padding-left: 12px; }}
.md2wx h3 {{ font-size: 1.15em; }}
.md2wx h4 {{ font-size: 1.05em; color: {text}; }}
.md2wx a {{ color: {accent}; text-decoration: none; font-weight: 600; }}
.md2wx strong {{ color: {heading}; font-weight: 700; }}
.md2wx em {{ color: {text}; font-style: italic; }}
.md2wx ul, .md2wx ol {{ color: {text}; margin: 16px 0; padding-left: 26px; }}
.md2wx li {{ color: {text}; margin: 8px 0; line-height: 1.75; }}
.md2wx blockquote {{
  color: {muted};
  border-left: 4px solid {accent};
  background: {quote_bg};
  margin: 16px 0;
  padding: 12px 16px;
  border-radius: 4px;
}}
.md2wx blockquote p {{ color: {muted}; margin: 6px 0; }}
.md2wx code {{
  color: {code_inline};
  background: {code_inline_bg};
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "SF Mono", Consolas, Menlo, monospace;
  font-size: 0.9em;
}}
.md2wx pre {{
  background: {code_bg};
  color: {code_fg};
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
  font-size: 0.88em;
  line-height: 1.6;
}}
.md2wx pre code {{ background: none; color: inherit; padding: 0; font-size: 1em; }}
.md2wx .codehilite {{ background: {code_bg}; border-radius: 8px; margin: 16px 0; }}
.md2wx .codehilite pre {{ margin: 0; }}
.md2wx img {{ max-width: 100%; height: auto; border-radius: 6px; display: block; margin: 16px auto; }}
.md2wx table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 0.92em; }}
.md2wx th {{ background: {accent}; color: #ffffff; padding: 8px 12px; border: 1px solid {border}; }}
.md2wx td {{ padding: 8px 12px; border: 1px solid {border}; color: {text}; }}
.md2wx hr {{ border: none; border-top: 1px solid {border}; margin: 28px 0; }}
.md2wx .footnotes {{ color: {muted}; font-size: 0.85em; margin-top: 32px; border-top: 1px solid {border}; padding-top: 12px; }}
.md2wx .footnotes p {{ color: {muted}; font-size: 1em; margin: 6px 0; }}
.md2wx .md2wx-refs {{ margin-top: 32px; border-top: 1px solid {border}; padding-top: 12px; }}
.md2wx .md2wx-refs .md2wx-refs-title {{ color: {heading}; font-weight: 700; font-size: 0.95em; margin: 0 0 8px; }}
.md2wx .md2wx-refs p {{ color: {muted}; font-size: 0.82em; margin: 4px 0; line-height: 1.5; }}
"""

THEMES = {
    "default": {
        "text": "#3f3f3f",
        "heading": "#1a1a1a",
        "muted": "#6a6a6a",
        "accent": "#3f7ef7",
        "bg": "#ffffff",
        "quote_bg": "#f6f8fb",
        "border": "#e4e4e4",
        "code_inline": "#c7254e",
        "code_inline_bg": "#f7f2f4",
        "code_bg": "#282c34",
        "code_fg": "#abb2bf",
        "pygments_style": "one-dark",
    },
    "elegant": {
        "text": "#4a4a48",
        "heading": "#2f3e46",
        "muted": "#6f7a72",
        "accent": "#3a8659",
        "bg": "#ffffff",
        "quote_bg": "#f2f7f3",
        "border": "#e2e8e2",
        "code_inline": "#a4503b",
        "code_inline_bg": "#f5efe9",
        "code_bg": "#2d3033",
        "code_fg": "#d0d0c8",
        "pygments_style": "friendly",
    },
    "minimal": {
        "text": "#333333",
        "heading": "#111111",
        "muted": "#777777",
        "accent": "#111111",
        "bg": "#ffffff",
        "quote_bg": "#f5f5f5",
        "border": "#dddddd",
        "code_inline": "#555555",
        "code_inline_bg": "#f0f0f0",
        "code_bg": "#f6f6f6",
        "code_fg": "#333333",
        "pygments_style": "default",
    },
}

DEFAULT_THEME = "default"


def theme_names() -> list[str]:
    return list(THEMES.keys())


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def build_css(name: str, font_size: int) -> str:
    t = get_theme(name)
    return _BASE.format(font_size=font_size, **{k: v for k, v in t.items() if k != "pygments_style"})
