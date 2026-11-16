"""落盘：每帖一个 JSON，文件名 = status id。"""

import json
import os
import re
import time

from . import config


def post_id_of(url):
    """从帖子链接提取 status id；提取不到返回空串。"""
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else ""


def build_record(**fields):
    """补齐派生字段，保证输出结构稳定。

    keyword 是 input.csv 的关键词列原值（复合标记，如 `E7|reply|0`），
    keywordText 是它的第一段（真正的词），keywordFlags 是其余段。
    """
    from .utils import keyword_flags, keyword_text

    keyword = fields.get("keyword", "")
    fields.setdefault("keywordText", keyword_text(keyword))
    fields.setdefault("keywordFlags", keyword_flags(keyword))
    fields["writeTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return fields


def write(record, posts_dir=None):
    """写入 data/posts/<id>.json，返回 (路径, 是否新建)。

    同一帖子被多条链接命中时后写的覆盖前写的（保持原有行为）。
    """
    posts_dir = posts_dir or config.POSTS_DIR
    pid = post_id_of(record.get("postUrl", ""))
    if not pid:
        return "", False
    os.makedirs(posts_dir, exist_ok=True)
    path = os.path.join(posts_dir, f"{pid}.json")
    is_new = not os.path.exists(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return path, is_new
