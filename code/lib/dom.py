"""DOM 取数：所有 X 页面选择器集中在这里。

X 前端是 React + 原子化 CSS，class 名（`css-146c3p1 r-bcqeeo ...`）会随改版变化。
策略：优先用稳定的 `data-testid` / `role` / `aria-label`，class 只做兜底。
改版导致采集为空时，先来改这个文件。
"""

import re


# ---------- 安全取值 ----------
def safe_text(ele):
    try:
        return ele.text or ""
    except Exception:
        return ""


def safe_attr(ele, name):
    try:
        return ele.attr(name) or ""
    except Exception:
        return ""


def safe_link(ele):
    """元素链接的绝对地址（DrissionPage 的 .link 已补全域名）。"""
    try:
        return ele.link or ""
    except Exception:
        return ""


def eles(ele, locator, timeout=0.1):
    try:
        return ele.eles(locator, timeout=timeout) or []
    except Exception:
        return []


def ele(ele, locator, timeout=0.1):
    try:
        return ele.ele(locator, timeout=timeout)
    except Exception:
        return None


# ---------- 帖子卡片 ----------
# 时间戳链接（帖子详情入口）
_LINK_CLASSES = (
    "@@tag()=a@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr "
    "r-a023e6 r-rjixqe r-16dba41 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui "
    "r-3s2u2q r-1loqt21",
    "@@tag()=a@@class=css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3 "
    "r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21",
)
# 正文容器
_BODY_CLASSES = (
    "@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 "
    "r-rjixqe r-16dba41 r-bnwqim",
    "@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-1inkyih "
    "r-16dba41 r-bnwqim r-135wba7",
)
# 互动栏（aria-label 形如 "12 replies, 34 likes, 5 reposts, 6 bookmarks, 1,234 views"）
_STATS_CLASS = (
    "@@class=css-g5y9jx r-1kbdv8c r-18u37iz r-1wtj0ep r-1ye8kvj r-1s2bzr4"
)
# 回复图标 path（互动栏兜底定位）
_REPLY_ICON_PATH = (
    "M1.751 10c0-4.42 3.584-8 8.005-8h4.366c4.49 0 8.129 3.64 8.129 8.13 "
    "0 2.96-1.607 5.68-4.196 7.11l-8.054 4.46v-3.69h-.067c-4.49.1-8.183"
    "-3.51-8.183-8.01zm8.005-6c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 "
    "6.08 6.138 6.01l.351-.01h1.761v2.3l5.087-2.81c1.951-1.08 3.163-3.13 "
    "3.163-5.36 0-3.39-2.744-6.13-6.129-6.13H9.756z"
)
# 帖子失效提示
DEAD_TEXT = (
    "Post is unavailable", "This Post is unavailable",
    "此帖子不可用", "帖子不可用", "Post unavailable",
    "This Post was deleted by the Post author",
    "This Post is from a suspended account",
    "该帖子已被删除",
)
# 广告标记（必须整段相等，避免正文含 "Ad" 的帖子被误杀）
AD_LABELS = {"Ad", "广告", "Promoted", "推广"}


def find_post_link(post_ele):
    """帖子时间戳链接 → (url, datetime 字符串)。拿不到时返回 ("", "")。"""
    link = None
    for locator in _LINK_CLASSES:
        link = ele(post_ele, locator, timeout=0.05)
        if link:
            break
    if not link:
        # 兜底：带 <time> 且不在引用卡片里的 /status/ 链接
        link = ele(
            post_ele,
            'xpath:.//a[contains(@href,"/status/")][.//time]'
            '[not(ancestor::div[@role="link"])]',
            timeout=0.05,
        )
    if not link:
        return "", ""
    url = safe_link(link) or safe_attr(link, "href") or ""
    if url.startswith("/"):
        url = "https://x.com" + url
    time_ele = ele(link, "@tag()=time", timeout=0.05)
    when = safe_attr(time_ele, "datetime") if time_ele else ""
    return url, when


def find_body(post_ele):
    """正文容器；优先 data-testid=tweetText。"""
    body = ele(post_ele, '@@data-testid=tweetText', timeout=0.05)
    if body:
        return body
    for locator in _BODY_CLASSES:
        body = ele(post_ele, locator, timeout=0.05)
        if body:
            return body
    return None


def find_user(post_ele):
    """作者信息 → (handle, nickname, profileUrl)。

    handle 形如 `@elonmusk`；profileUrl 形如 `https://x.com/elonmusk`。
    """
    handle = nickname = profile_url = ""
    name_box = ele(post_ele, '@@data-testid=User-Name', timeout=0.05)
    if name_box:
        for a in eles(name_box, "@tag()=a", timeout=0.05):
            href = safe_attr(a, "href")
            text = safe_text(a).strip()
            if href.startswith("/") and text.startswith("@"):
                handle = handle or text
                profile_url = profile_url or "https://x.com" + href.split("?")[0]
                continue
            if href.startswith("/") and text and not nickname:
                nickname = text
                profile_url = profile_url or "https://x.com" + href.split("?")[0]
        if not handle:
            m = re.search(r"@\w+", safe_text(name_box))
            if m:
                handle = m.group(0)
    if not handle:
        # 旧 class 兜底
        for div in eles(post_ele, "@@class=css-g5y9jx r-1wbh5a2 r-dnmrzs@@tag()=div",
                        timeout=0.05):
            text = safe_text(div).strip()
            if text.startswith("@"):
                handle = text
                break
    if not nickname:
        for a in eles(post_ele,
                      "@@tag()=a@@class=css-g5y9jx r-1wbh5a2 r-dnmrzs r-1ny4l3l "
                      "r-1loqt21", timeout=0.05):
            text = safe_text(a).strip()
            if text and not text.startswith("@"):
                nickname = text
                profile_url = profile_url or safe_link(a) or safe_attr(a, "href")
                break
    return handle, nickname, profile_url


def find_stats_label(post_ele):
    """互动栏 aria-label（含全部指标）。"""
    for box in eles(post_ele, '@@tag()=div@@role=group', timeout=0.05):
        label = safe_attr(box, "aria-label")
        if label and "view" in label:
            return label
    for box in eles(post_ele, _STATS_CLASS, timeout=0.05):
        label = safe_attr(box, "aria-label")
        if label:
            return label
    # 兜底：靠回复图标 path 反查父节点
    for path in eles(post_ele, "@tag()=path", timeout=0.5):
        if safe_attr(path, "d") == _REPLY_ICON_PATH:
            parent = path.parent(7)
            label = safe_attr(parent, "aria-label")
            if label:
                return label
    return ""


def find_reply_target(post_ele):
    """被回复账号文本（"Replying to @a @b"），非回复返回 ''。"""
    text = safe_text(post_ele)
    m = re.search(r"Replying to\s+(@\w+(?:\s+@\w+)*)", text)
    if m:
        return m.group(1).strip()
    box = ele(post_ele, "@@class=css-g5y9jx r-4qtqp9 r-zl2h9q", timeout=0.1)
    if box:
        t = safe_text(box)
        if "Replying" in t:
            return t.split("Replying to", 1)[-1].strip()
    return ""


def find_quote(post_ele):
    """引用卡片元素（内部含 tweetText 的 div[role=link]）；无引用返回 None。"""
    for q in eles(post_ele, 'xpath:.//div[@role="link"]', timeout=0.1):
        if 'data-testid="tweetText"' in (q.inner_html or ""):
            return q
    return None


def is_ad(post_ele):
    """是否为广告卡片：存在 dir=ltr 且整段文本等于广告标签的元素。"""
    for div in eles(post_ele, 'xpath:.//div[@dir="ltr"]', timeout=0.05):
        if safe_text(div).strip() in AD_LABELS:
            return True
    return False


def is_dead(post_ele):
    """帖子是否已删除/不可用。"""
    text = safe_text(post_ele)
    return any(k in text for k in DEAD_TEXT)


def dead_status(post_ele):
    """删除 / 封禁状态标识，正常帖返回 active。"""
    text = safe_text(post_ele)
    if "deleted by the Post author" in text or "已被删除" in text:
        return "delete"
    if "suspended account" in text:
        return "suspended"
    return "active"


def social_context(post_ele):
    """卡片上方的社交上下文文本（"Reposted" / "转帖" 等），没有返回 ''。"""
    box = ele(post_ele, '@@data-testid=socialContext', timeout=0.05)
    return safe_text(box).strip() if box else ""


# ---------- 页面状态 ----------
def no_result(tab):
    """搜索页是否显示 "No results"。"""
    try:
        for span in tab.eles("@@class=css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 "
                            "r-poiln3@@tag()=span", timeout=0.5):
            if "No results" in safe_text(span):
                return True
    except Exception:
        pass
    return False


def has_retry(tab):
    """页面是否出现 Retry 按钮（风控/加载失败）。"""
    for btn in eles(tab, "@tag()=button", timeout=0.1):
        if "Retry" in safe_text(btn):
            return True
    return False


def click_expand(ele_):
    """点开 "Show more" / "Show replies"，成功返回 True。"""
    for btn in eles(ele_,
                    "@@tag()=button@@class=css-146c3p1 r-bcqeeo r-qvutc0 r-37j5jr "
                    "r-a023e6 r-rjixqe r-16dba41 r-fdjqy7", timeout=0.05):
        if "Show more" in safe_text(btn):
            btn.click(by_js=True)
            return True
    for btn in eles(ele_,
                    "@@tag()=button@@class=css-g5y9jx r-16y2uox r-1cwvpvk "
                    "r-1noe1sz r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l",
                    timeout=0.05):
        if "Show replies" in safe_text(btn):
            btn.click(by_js=True)
            return True
    return False
