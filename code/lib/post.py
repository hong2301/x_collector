"""单帖解析：把一个 <article> 卡片变成一条记录。"""

import random
import re
import time

from . import dom, fiber, link, media, metrics, store, text


def _inner_html(ele):
    try:
        return ele.inner_html or ""
    except Exception:
        return ""


def _status_id(url):
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else ""


def extract(post_ele, task_url, keyword="", with_media=False,
            expand_links=False, images_dir=None, logger=None):
    """解析一个帖子卡片，返回记录 dict。

    无法定位帖子链接（广告 / 推荐卡片 / 已失效）时返回 None。
    """
    # 1. 状态与广告
    post_status = dom.dead_status(post_ele)
    if dom.is_ad(post_ele):
        if logger:
            logger.debug("跳过广告卡片")
        return None

    # 2. 帖子链接与时间
    post_url, post_time = dom.find_post_link(post_ele)
    if not post_url:
        if logger and dom.is_dead(post_ele):
            logger.info("跳过已失效帖子（无 status 链接）")
        return None

    # 3. 展开被折叠的正文
    if dom.click_expand(post_ele):
        time.sleep(random.uniform(1, 2))

    # 4. 正文
    body = dom.find_body(post_ele)
    lang = dom.safe_attr(body, "lang") if body else ""
    parsed = text.parse_body(_inner_html(body) if body else "")
    external = parsed["links"]
    external_final = link.expand_all(external) if (external and expand_links) else ""

    # 5. 作者
    handle, nickname, profile_url = dom.find_user(post_ele)

    # 6. 回复 / 引用 / 转发
    reply_target = dom.find_reply_target(post_ele)
    fields = fiber.extract(post_ele)

    quote_ele = dom.find_quote(post_ele)
    quote_url = fiber.quote_url(quote_ele) if quote_ele else ""
    quoted_id = _status_id(quote_url)

    retweeted_id = fields["retweetedPostId"]
    ctx = dom.social_context(post_ele)
    is_retweet = 1 if (retweeted_id or re.search(r"repost|retweet|转推|转帖", ctx, re.I)) else 0
    is_reply = 1 if (reply_target or fields["inReplyToPostId"]) else 0

    # 7. 互动指标
    counts = metrics.parse_metrics(dom.find_stats_label(post_ele))

    record = store.build_record(
        username=handle,
        nickname=nickname,
        profileUrl=profile_url,
        postTime=post_time or "",
        text=parsed["text"],
        lang=lang,
        mentions=parsed["mentions"],
        externalLink=external,
        externalLinkFinal=external_final,
        mediaData=[],
        isRetweet=is_retweet,
        isReply=is_reply,
        isQuote=1 if quote_ele else 0,
        conversationId=fields["conversationId"],
        retweetedPostId=retweeted_id,
        quotedPostId=quoted_id,
        inReplyToPostId=fields["inReplyToPostId"],
        inReplyToUserId=reply_target,
        quotePostRetweetCount="",     # 被引帖的转发数 DOM 上取不到
        likeCount=counts["likes"],
        replyCount=counts["replies"],
        bookmarkCount=counts["bookmark"],
        repostCount=counts["repost"],
        quoteCount=fields["quoteCount"] if fields["quoteCount"] is not None else "",
        pureRetweetCount=metrics.pure_retweet(counts["repost"], fields["quoteCount"]),
        viewCount=counts["views"],
        hashtags=parsed["hashtags"],
        keyword=keyword,
        postUrl=post_url,
        searchUrl=task_url,
        postStatus=post_status,
    )

    # 8. 媒体（截图较慢，默认关闭）
    if with_media:
        record["mediaData"] = media.collect(
            post_ele, post_url,
            images_dir=images_dir if images_dir is not None else None,
            logger=logger)

    return record
