"""功能层：atoms.py 的原子函数组合出的业务流程 + CLI。

| 功能                | 函数                          |
|--------------------|-------------------------------|
| 按关键词/搜索链接采帖 | `collect_search_posts(...)`   |
| 查看已采数量         | `show_stats(...)`             |
| 检查各端口登录态      | `show_login(...)`             |

直接运行本文件即按默认参数采集：`python code/features.py`。
"""

import argparse
import glob
import os
import sys

# 允许 `python code/features.py` 直接运行（把 code/ 加入 sys.path）
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

import atoms
from lib import auth, browser, config, session, utils
from lib.logger import get_logger, setup

log = get_logger("x")

COMMANDS = ("search", "stats", "login")


def collect_search_posts(input_file=config.INPUT_FILE, start=1, end=0,
                         port=config.DEFAULT_PORT, posts_dir=config.POSTS_DIR,
                         images_dir=config.IMAGES_DIR,
                         max_per_link=config.MAX_PER_LINK,
                         max_per_keyword=config.MAX_PER_KEYWORD,
                         empty_limit=config.EMPTY_SCROLL_LIMIT,
                         with_media=False, expand_links=True,
                         with_replies=True):
    """按输入清单批量采集搜索页帖子。

    Args:
        input_file:    清单 CSV（url,关键词）
        start/end:     按数据行 1-based 切片，end=0 表示到末尾
        port:          浏览器调试端口（= 账号槽位）
        max_per_link:  每条链接最多采集帖数，0=不限
        max_per_keyword: 每个词的目标条数，0=不限；达标跳过该词剩余链接
        empty_limit:   连续多少轮没有新帖就认为到底
        with_media:    是否采集媒体并截图到 data/images
        expand_links:  是否把 t.co 展开成最终地址（默认开，较慢）
        with_replies:  False 时单帖链接只采主帖

    Returns:
        (成功链接数, 失败链接数)
    """
    items = utils.read_input(input_file)
    tasks = utils.select_range(items, start, end)
    if not tasks:
        log.error("没有可采集的链接（清单共 %s 条，切片 %s~%s）",
                  len(items), start, end or "末尾")
        return 0, 0

    os.makedirs(posts_dir, exist_ok=True)
    if with_media:
        os.makedirs(images_dir, exist_ok=True)

    counter = utils.count_keywords(posts_dir)
    log.info("端口=%s 链接=%s 条（%s~%s） 输出=%s", port, len(tasks),
             start, (start + len(tasks) - 1), posts_dir)
    log.info("已有各词有效数：%s", dict(sorted(counter.items())))

    atoms.open_port(port)
    if not atoms.check_login():
        return 0, len(tasks)

    ok = fail = 0
    for i, (url, keyword) in enumerate(tasks, start):
        kw = utils.keyword_text(keyword)
        if max_per_keyword and counter.get(kw, 0) >= max_per_keyword:
            log.info("[%s] 词[%s] 已有 %s 条 ≥ 目标 %s，跳过",
                     i, kw, counter.get(kw, 0), max_per_keyword)
            continue
        log.info("[%s/%s] %s | 关键词: %s", i, len(items), url, keyword)
        try:
            result = atoms.collect_search_link(
                url, keyword,
                posts_dir=posts_dir,
                images_dir=images_dir,
                max_per_link=max_per_link,
                max_per_keyword=max_per_keyword,
                keyword_counter=counter,
                with_media=with_media,
                expand_links=expand_links,
                with_replies=with_replies,
                empty_limit=empty_limit)
            log.info("[%s] 完成：新增 %s / 处理 %s，原因 %s",
                     i, result["added"], result["total"], result["reason"])
            ok += 1
        except KeyboardInterrupt:
            log.warning("用户中断，停止后续任务")
            break
        except Exception as exc:
            fail += 1
            log.error("[%s] 采集失败，跳过：%r", i, exc)
    log.info("结束：成功 %s，失败 %s，累计各词有效数 %s",
             ok, fail, dict(sorted(counter.items())))
    return ok, fail


def show_stats(posts_dir=config.POSTS_DIR):
    """打印已落盘帖子数与各词有效数。"""
    files = glob.glob(os.path.join(posts_dir, "*.json"))
    counter = utils.count_keywords(posts_dir)
    log.info("帖子文件：%s 个（%s）", len(files), posts_dir)
    for kw, n in sorted(counter.items(), key=lambda kv: -kv[1]):
        log.info("  %-30s %s", kw or "(空)", n)


def show_login(ports):
    """逐个端口读当前账号（必要时导航到 x.com 首页，不做任何交互）。"""
    for port in ports:
        try:
            session.open_port(port)
            tab = session.pick_tab()
            if "x.com" not in (tab.url or ""):
                tab.get("https://x.com/home")
                browser.wait_doc(tab, timeout=20)
            info = atoms.account_info()
            ok, detail = auth.is_logged_in(tab)
            log.info("端口 %s（profile %s）：登录=%s 账号=%s twid=%s url=%s",
                     port, browser.profile_name(port), ok,
                     info["name"] or "(未读到)",
                     info["twid"] or "(无)", (info["url"] or "")[:80])
            if not ok:
                log.warning("  说明：%s", detail)
        except Exception as exc:
            log.error("端口 %s：连接失败 %r", port, exc)


def _add_search_args(p):
    p.add_argument("-i", "--input-file", default=config.INPUT_FILE,
                   help="输入清单 CSV（url,关键词）")
    p.add_argument("--start", type=int, default=1, help="起始数据行号（1-based）")
    p.add_argument("--end", type=int, default=0, help="结束数据行号，0=末尾")
    p.add_argument("--port", type=int, default=config.DEFAULT_PORT,
                   help=f"浏览器调试端口（默认 {config.DEFAULT_PORT}）")
    p.add_argument("-o", "--posts-dir", default=config.POSTS_DIR)
    p.add_argument("--images-dir", default=config.IMAGES_DIR)
    p.add_argument("--max-per-link", type=int, default=config.MAX_PER_LINK,
                   help="每条链接最多采集帖数，0=不限")
    p.add_argument("--max-per-keyword", type=int, default=config.MAX_PER_KEYWORD,
                   help="每个词的目标条数，0=不限")
    p.add_argument("--empty-limit", type=int, default=config.EMPTY_SCROLL_LIMIT,
                   help="连续多少轮没有新帖就认为到底")
    p.add_argument("--media", action="store_true", help="采集媒体并截图")
    p.add_argument("--expand-links", dest="expand_links", action="store_true",
                   default=True, help="展开 t.co 短链（默认开）")
    p.add_argument("--no-expand-links", dest="expand_links", action="store_false",
                   help="不展开 t.co（快）")
    p.add_argument("--no-replies", dest="with_replies", action="store_false",
                   help="单帖链接只采主帖")
    p.add_argument("-q", "--quiet", action="store_true")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="features.py",
        description="X 搜索页帖子采集（端口 = 账号槽位）")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("search", help="按输入清单采帖（默认）")
    _add_search_args(s)

    st = sub.add_parser("stats", help="查看已采数量")
    st.add_argument("-o", "--posts-dir", default=config.POSTS_DIR)
    st.add_argument("-q", "--quiet", action="store_true")

    lg = sub.add_parser("login", help="检查各端口登录态")
    lg.add_argument("--ports", type=int, nargs="*", default=None,
                    help="要检查的端口，默认全部已登记槽位")
    lg.add_argument("-q", "--quiet", action="store_true")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # 兼容旧用法：python code/features.py --port 5268 --start 1 --end 300
    if not argv or (argv[0] not in COMMANDS and argv[0] not in ("-h", "--help")):
        argv = ["search"] + argv

    args = build_parser().parse_args(argv)
    setup(quiet=getattr(args, "quiet", False))

    if args.cmd == "stats":
        show_stats(posts_dir=args.posts_dir)
    elif args.cmd == "login":
        ports = args.ports or sorted(config.PROFILE_MAP) or [config.DEFAULT_PORT]
        show_login(ports)
    else:
        collect_search_posts(
            input_file=args.input_file,
            start=args.start, end=args.end,
            port=args.port,
            posts_dir=args.posts_dir, images_dir=args.images_dir,
            max_per_link=args.max_per_link,
            max_per_keyword=args.max_per_keyword,
            empty_limit=args.empty_limit,
            with_media=args.media,
            expand_links=args.expand_links,
            with_replies=args.with_replies)


if __name__ == "__main__":
    main()
