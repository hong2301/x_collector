"""正文解析：emoji 保留、话题标签、提及、外链。"""

import html
import re

from lxml import html as lh

# 正文里的 emoji 是 <img alt="😀">，替换成文本节点再交给 lxml
_IMG_TAG = re.compile(r"<img\b[^>]*>")
_ALT = re.compile(r'alt="([^"]*)"')
_HREF = re.compile(r'<a[^>]+href="(https?://[^"]+)"')


def _img_to_span(match):
    """把 emoji <img> 替换为 <span>alt 文本</span>，并转义防破坏结构。"""
    alt_match = _ALT.search(match.group(0))
    alt = alt_match.group(1) if alt_match else ""
    return f"<span>{html.escape(alt)}</span>"


def flatten(inner_html):
    """把正文 inner_html 拍平成纯文本（保留 emoji）。"""
    if not inner_html:
        return ""
    fixed = _IMG_TAG.sub(_img_to_span, inner_html)
    try:
        doc = lh.fromstring(fixed)
        return "".join(doc.xpath("//text()"))
    except Exception:
        return re.sub(r"<[^>]+>", "", fixed)


def parse_body(inner_html):
    """正文 → {text, hashtags, mentions, links}。

    links 是正文中全部外链原始地址（空格分隔），不含话题/提及的相对路径。
    """
    text = flatten(inner_html)
    hashtags = re.findall(r"#\w+", text)
    mentions = re.findall(r"@\w+", text)
    links = _HREF.findall(inner_html or "")
    return {
        "text": text,
        "hashtags": " ".join(hashtags),
        "mentions": " ".join(mentions),
        "links": " ".join(links),
    }
