"""外链展开：t.co 等短链跟随重定向取最终地址。"""

import requests

try:                      # 作为模块导入（正常用法）
    from . import config
except ImportError:       # 直接运行本文件做自检：python code/lib/link.py
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib import config

# 不要伪装浏览器 UA：t.co 对浏览器 UA 返回 200 中间页，就不跟随跳转了；
# 用简单 UA 才能拿到真实 301 链
HEADERS = {"User-Agent": "curl/8.5.0"}


def _proxies():
    return {"http": config.PROXY, "https": config.PROXY} if config.PROXY else None


def expand(url, timeout=None):
    """展开链接返回最终 URL；超时/失败返回空字符串。

    GET 优先（一定拿到跟随 302 后的地址），再退 HEAD。
    """
    timeout = timeout or config.EXPAND_TIMEOUT
    for method in ("get", "head"):
        try:
            resp = getattr(requests, method)(
                url, allow_redirects=True, timeout=timeout,
                headers=HEADERS, proxies=_proxies())
            return resp.url or ""
        except Exception:
            continue
    return ""


def expand_all(links):
    """空格分隔的多条链接逐个展开，返回空格分隔的结果。"""
    return " ".join(expand(x) for x in (links or "").split())


def self_test():
    """自检：展开真实链接、无跳转原样、不可达兜底。"""
    cases = [
        "https://x.com/iChongqing_CIMC",
        "https://en.wikipedia.org/wiki/Twitter",
        "https://www.chinadaily.com.cn/",
        "https://nonexistent-domain-xyz-12345.invalid/a",
    ]
    for url in cases:
        print(f"{url}\n  -> {expand(url)}\n")


if __name__ == "__main__":
    self_test()
