"""通用工具：输入清单读取、按行号切片、关键词统计、随机停顿。"""

import csv
import glob
import json
import os
import random


def read_input(path):
    """读取输入清单，返回 [(url, keyword)]。

    格式（有表头，列名 `url` / `关键词` 或 `keyword`）：
        url,关键词
        https://x.com/search?q=...&src=typed_query,E7|reply|0

    关键词列是复合标记：`词|类型|分段`，第一段是词，其余段由
    `keyword_text()` / `keyword_flags()` 拆出。允许为空。
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f) if r and str(r[0]).strip()]
    if not rows:
        return []
    header = [str(c).strip().lower() for c in rows[0]]
    if "url" in header:
        url_idx = header.index("url")
        kw_idx = next((header.index(h) for h in ("关键词", "keyword")
                       if h in header), None)
        body = rows[1:]
    else:
        url_idx, kw_idx, body = 0, 1, rows
    out = []
    for r in body:
        if url_idx >= len(r):
            continue
        url = str(r[url_idx]).strip()
        if not url or url.startswith("#"):
            continue
        kw = ""
        if kw_idx is not None and kw_idx < len(r):
            kw = str(r[kw_idx]).strip()
        out.append((url, kw))
    return out


def select_range(items, start, end):
    """按 1-based 行号切片（对应 input.csv 数据行）；end=0 表示到末尾。"""
    total = len(items)
    if not total:
        return []
    start = max(1, min(start, total))
    end = total if not end else max(start, min(end, total))
    return items[start - 1:end]


def keyword_text(keyword):
    """复合关键词取词：`E7|reply|0` → `E7`。"""
    return (keyword or "").split("|")[0].strip()


def keyword_flags(keyword):
    """复合关键词取其余段：`E7|reply|0` → `reply|0`。"""
    parts = (keyword or "").split("|", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def count_keywords(posts_dir):
    """统计已落盘帖子按词去重的有效链接数（keyword 第一段为词）。"""
    seen = {}
    for fp in glob.glob(os.path.join(posts_dir, "*.json")):
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        url = str(d.get("postUrl", ""))
        if not url.startswith("http"):
            continue
        kw = keyword_text(str(d.get("keyword", "")))
        seen.setdefault(kw, set()).add(url)
    return {k: len(v) for k, v in seen.items()}


def pick_pause(lo, hi):
    """随机停顿，避免机械节奏。"""
    lo, hi = min(lo, hi), max(lo, hi)
    return random.uniform(lo, hi)
