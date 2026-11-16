"""原子层：最小可执行单元，每个函数只做一件事。

| 原子能力            | 函数                                     |
|--------------------|------------------------------------------|
| 打开/接管端口        | open_port(port)                          |
| 检测是否登录         | check_login()                            |
| 读账号指纹           | account_info()                           |
| 采集一条搜索链接      | collect_search_link(url, keyword, ...)   |

组合与命令行走 code/features.py，实现细节走 code/lib/。
"""

import os
import random
import time

from lib import auth, browser, config, dom, post as postlib, scroll, session, store, utils
from lib.logger import get_logger

log = get_logger("x")

# 采完一条链接后，若新增帖子数低于该值则额外等待，避免连续请求被限流
LOW_YIELD = 60


def open_port(port=None):
    """接管浏览器端口（未启动则按 profile 拉起，保留登录态）。"""
    port = port or config.DEFAULT_PORT
    br = session.open_port(port)
    log.info("端口已连接：%s → profile %s", port, browser.profile_name(port))
    return br


def check_login(port=None):
    """只读 cookie 判断登录态，不导航页面。"""
    if port is not None:
        session.open_port(port)
    tab = session.pick_tab()
    ok, detail = auth.is_logged_in(tab)
    if ok:
        log.info("登录检查通过（端口 %s）", session.state().get("port"))
    else:
        log.error("登录检查未通过：%s", detail)
    return ok


def account_info(port=None):
    """读当前标签页的账号信息（url / 显示名 / twid）。"""
    if port is not None:
        session.open_port(port)
    info = auth.account_info(session.pick_tab())
    info["port"] = session.state().get("port")
    info["profile"] = config.PROFILE_MAP.get(info["port"])
    return info


def collect_search_link(url, keyword="", posts_dir=None, images_dir=None,
                        max_per_link=None, max_per_keyword=None,
                        keyword_counter=None, with_media=False,
                        expand_links=False, with_replies=True,
                        empty_limit=None):
    """【核心】采集一条搜索链接：打开 → 回顶 → 循环滚动解析 → 停止。

    Args:
        url:             搜索链接
        keyword:         input.csv 的关键词列原值（复合标记）
        posts_dir:       帖子输出目录
        keyword_counter: {词: 已有有效数}，会就地累加（达标即停）
        with_media:      是否采集媒体并截图
        expand_links:    是否展开 t.co 外链
        with_replies:    False 时只采单帖链接里的主帖

    Returns:
        {"added": 新增数, "total": 处理数, "reason": 停止原因, "no_result": bool}
    """
    posts_dir = posts_dir or config.POSTS_DIR
    max_per_link = config.MAX_PER_LINK if max_per_link is None else max_per_link
    max_per_keyword = config.MAX_PER_KEYWORD if max_per_keyword is None else max_per_keyword
    empty_limit = config.EMPTY_SCROLL_LIMIT if empty_limit is None else empty_limit
    kw = utils.keyword_text(keyword)
    counter = keyword_counter if keyword_counter is not None else {}

    tab = session.get_tab()
    tab.get(url)
    scroll.to_top(tab)

    seen = set()
    added = total = 0
    empty_rounds = 0
    no_result = False
    reason = "done"

    while empty_rounds < empty_limit:
        if scroll.reload_unless_retry(tab, url):
            log.warning("页面加载失败已重新打开：%s", url)

        empty_rounds += 1
        time.sleep(random.uniform(0.1, 0.2))

        if dom.no_result(tab):
            log.info("无结果，跳过：%s", url)
            time.sleep(random.uniform(20, 30))
            no_result = True
            reason = "no_result"
            break

        for post_ele in tab.eles("@tag()=article", timeout=1) or []:
            try:
                record = postlib.extract(
                    post_ele, url, keyword,
                    with_media=with_media,
                    expand_links=expand_links,
                    images_dir=images_dir if with_media else None,
                    logger=log)
            except Exception as exc:
                log.warning("解析失败，跳过该卡片：%r", exc)
                continue
            if not record or record["postUrl"] in seen:
                continue

            seen.add(record["postUrl"])
            empty_rounds = 0
            try:
                post_ele.scroll.to_see()
            except Exception:
                pass

            path, is_new = store.write(record, posts_dir)
            if not path:
                continue
            total += 1
            if is_new:
                added += 1
                counter[kw] = counter.get(kw, 0) + 1
            log.info("[%s] 已写入 %s | %s | %s%s", kw,
                     os.path.basename(path), record["username"],
                     record["postTime"], "" if is_new else "（覆盖）")

            if max_per_keyword and counter.get(kw, 0) >= max_per_keyword:
                log.info("词[%s] 已达 %s 条，停止剩余链接", kw, counter.get(kw, 0))
                reason = "keyword_quota"
                return {"added": added, "total": total,
                        "reason": reason, "no_result": no_result}
            if max_per_link and total >= max_per_link:
                reason = "link_quota"
                break
            if not with_replies and store.post_id_of(url) == store.post_id_of(record["postUrl"]):
                reason = "main_post_only"
                break

            time.sleep(random.uniform(0.01, 0.02))

        if reason != "done":
            break
        scroll.step(tab, 300)

    # 采得少说明页面没铺开，多等一会儿再进下一条链接（原限流保护）
    if total < LOW_YIELD and not no_result:
        time.sleep(random.uniform(10, 20))
    return {"added": added, "total": total, "reason": reason, "no_result": no_result}
