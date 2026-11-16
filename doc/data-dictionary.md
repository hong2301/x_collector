# 帖子 JSON 字段定义

每个帖子一个文件：`data/posts/<status_id>.json`（`status_id` 从 `postUrl` 提取）。
所有字段都有，取不到时为空字符串（计数类为 `"0"` 或 `null`，见备注）。

## 身份与时间

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `username` | str | DOM `User-Name` 内的 `a` | 作者 handle，带 `@`，如 `@elonmusk` |
| `nickname` | str | 同上 | 作者显示名 |
| `profileUrl` | str | 同上 | 作者主页完整链接 |
| `postTime` | str | `<time datetime>` | ISO 8601 UTC，如 `2019-04-05T20:18:42.000Z` |
| `lang` | str | 正文容器 `lang` 属性 | 如 `en` / `th` / `zh` |
| `postUrl` | str | 时间戳链接 | 帖子完整链接，也是文件名来源 |
| `searchUrl` | str | 任务输入 | 触发本次采集的链接 |

## 正文

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `text` | str | 正文 `inner_html` 拍平 | emoji 保留（`<img alt>` 转文本），换行保留 |
| `hashtags` | str | 正文正则 `#\w+` | 空格分隔 |
| `mentions` | str | 正文正则 `@\w+` | 空格分隔 |
| `externalLink` | str | 正文 `a[href^=http]` | 空格分隔，通常是 `t.co` 短链 |
| `externalLinkFinal` | str | `lib/link.expand` | 跟随 301 后的最终地址；展开失败时为空 |
| `mediaData` | list | DOM | `[{mediaUrl, mediaType(img/video/gif), videoDuration}]`，默认不采 |

## 关系

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `isRetweet` | 0/1 | `socialContext` 文本 + fiber | 是否为转推 |
| `retweetedPostId` | str | fiber `retweeted_status_result` | 被转推帖 id，取不到为空 |
| `isReply` | 0/1 | `Replying to` 文本 + fiber | 是否为回复 |
| `inReplyToPostId` | str | fiber `in_reply_to_status_id_str` | 被回复帖 id |
| `inReplyToUserId` | str | `Replying to @xxx` 文本 | 被回复账号（**文本形式，可能多个**） |
| `isQuote` | 0/1 | DOM `div[role=link]` 内含 `tweetText` | 是否为引用转发 |
| `quotedPostId` | str | 引用卡片的 fiber | 被引用帖 id |
| `conversationId` | str | fiber `conversation_id_str` | 会话（= 根帖）id |
| `quotePostRetweetCount` | str | — | **恒为空**：被引帖转发数 DOM 上取不到 |

## 互动指标

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `likeCount` | str | 互动栏 `aria-label` | 原样字符串，可能带千分位逗号 |
| `replyCount` | str | 同上 | 注意是**页面上显示的回复数**（含未加载的） |
| `repostCount` | str | 同上 | 界面 `reposts` 总数（= 纯转发 + 引用） |
| `quoteCount` | str/int | fiber `quote_count` | 引用转发数；取不到为 `""` |
| `pureRetweetCount` | int/str | 计算 | `repostCount - quoteCount`，任一缺失为 `""` |
| `bookmarkCount` | str | aria-label | 部分帖不显示，为 `"0"` |
| `viewCount` | str | aria-label | 老帖或不公开浏览量时为 `"0"` |

## 归类与状态

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `keyword` | str | `input.csv` 关键词列 | **原值**，复合标记如 `E7\|reply\|0` |
| `keywordText` | str | 上者第一段 | 真正的词，如 `E7` |
| `keywordFlags` | str | 上者其余段 | 如 `reply\|0` |
| `postStatus` | str | DOM 文本 | `active` / `delete` / `suspended` |
| `writeTime` | str | 本地时间 | 写入时间，`YYYY-MM-DD HH:MM:SS` |

## 口径提醒

- **`replyCount` 不是已采到的回复条数**，是页面显示的计数；回复正文不在帖子 JSON 里。
- 同一帖子被多条链接命中时会**覆盖**，`keyword` / `searchUrl` 记为最后一次的。
- `data/images/<status_id>_<n>.json` 里是 HTML 截图（webp base64），不是原图；
  `ocr` 字段当前恒为空，留给后续 OCR。
