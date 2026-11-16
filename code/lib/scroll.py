"""页面滚动：回顶、翻页、重试。"""

import random
import time


def to_top(tab, times=3, pause=1.0):
    """回顶，触发顶部内容的懒加载。"""
    for _ in range(times):
        try:
            tab.scroll.to_top()
        except Exception:
            pass
        time.sleep(pause)


def step(tab, px=300, pause=(0.1, 0.2)):
    """向下滚一小段并停顿，让新卡片加载出来。"""
    try:
        tab.scroll(px)
    except Exception:
        pass
    time.sleep(random.uniform(*pause))


def reload_unless_retry(tab, url, retries=3, wait=2.0):
    """页面出现 Retry（风控/加载失败）时重新打开链接，返回是否重载过。"""
    from . import dom

    reloaded = False
    for _ in range(retries):
        if not dom.has_retry(tab):
            break
        try:
            tab.get(url)
        except Exception:
            pass
        time.sleep(wait)
        reloaded = True
    return reloaded
