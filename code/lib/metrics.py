"""互动指标：aria-label 解析。"""

import re

PATTERNS = {
    "repost": r"(\d[\d,]*)\s*repost",
    "likes": r"(\d[\d,]*)\s*likes?",
    "replies": r"(\d[\d,]*)\s*repl(?:y|ies)",
    "bookmark": r"(\d[\d,]*)\s*bookmark",
    "views": r"(\d[\d,]*)\s*views?",
}


def parse_metrics(label):
    """从 aria-label 解析 5 个指标，缺省为 "0"（与原采集口径一致）。

    "12 replies, 3 reposts, 45 likes, 6 bookmarks, 1,234 views"
    """
    out = {}
    for name, pattern in PATTERNS.items():
        m = re.search(pattern, label or "")
        out[name] = m.group(1) if m else "0"
    return out


def to_int(value):
    """带千分位的字符串 → int；失败返回 None。"""
    digits = str(value or "").replace(",", "").strip()
    return int(digits) if digits.isdigit() else None


def pure_retweet(repost_count, quote_count):
    """纯转发数 = 界面 reposts - quote_count（拿不到返回空）。"""
    repost = to_int(repost_count)
    if quote_count is None or repost is None:
        return ""
    return repost - quote_count
