# 已知问题

## 1. 选择器依赖 X 前端结构（脆弱点）

X 用原子化 CSS，class 名形如 `css-146c3p1 r-bcqeeo r-1ttztb7 ...`，会随改版变化。
`code/lib/dom.py` 的策略是 **`data-testid` / `role` / `aria-label` 优先，class 兜底**。

改版后若出现「采到的帖子字段大面积变空」或「一条都采不到」：

1. 在浏览器里 F12 看当前帖子的 DOM；
2. 只改 `lib/dom.py` 的选择器，不要动解析流程；
3. 用 `python code/features.py search --start 1 --end 1 --max-per-link 2 -o data/_probe`
   验证，然后 `data/_probe` 可删。

已知强依赖的 testid：`tweetText`、`User-Name`、`socialContext`、`tweetPhoto`、`videoPlayer`。

## 2. `x1` profile 目录是空的

`browser-profile\x1`（端口 5268，主账号）目录下没有 `Default`，即**没有登录态**；
`x2` / `x3` 有。用 5268 采集前需要先手动登录（登录后 cookie 会落进该目录）。
`features.py login` 会显示「登录=False auth_token cookie 不存在」。

## 3. 恒为空 / 不可靠的字段

| 字段 | 情况 |
|---|---|
| `quotePostRetweetCount` | 恒为空。被引帖的转发数在 DOM 与 fiber 里都拿不到 |
| `inReplyToUserId` | 存的是 `Replying to @a @b` 的**文本**，不是用户 id |
| `viewCount` | 老帖或页面不显示浏览量时为 `"0"`，无法区分「真的是 0」和「没显示」 |
| `bookmarkCount` | 同上 |
| `isRetweet` | 依赖 `socialContext`（"Reposted"）或 fiber 的 `retweeted_status_result`，两者都拿不到时误判为 0 |
| `conversationId` / `inReplyToPostId` / `retweetedPostId` | 来自 fiber 字符串匹配（JSON.stringify 后正则），X 改字段名就失效 |

## 4. fiber 取数是「字符串匹配」不是结构化解析

`lib/fiber.py` 用 `JSON.stringify(memoizedProps)` 后正则取字段，只扫前 50 层 fiber、
每个帖子最多 3 秒。原因：递归遍历大对象会把浏览器卡死。

副作用：同一个值可能在多层 fiber 里重复出现，已做去重；字段名变化会导致静默返回空。

## 5. t.co 展开必须用非浏览器 UA

`t.co` 对浏览器 UA 返回 **200 中间页**（不跟随跳转），对简单 UA 返回 301。
所以 `lib/link.py` 用 `User-Agent: curl/8.5.0`——**不要**改成 Chrome UA，否则
`externalLinkFinal` 会退化成 `t.co` 原链（历史数据里就是这个问题）。

## 6. 同一帖子被覆盖

文件名是 `status_id`，同一帖子被多条链接命中时后写的覆盖前写的，`keyword` /
`searchUrl` 只保留最后一次。需要多关键词归因时，应在采集后另行记录映射，
不要指望帖子 JSON 里有多个关键词。

## 7. 回复内容不在帖子 JSON 里

`isReply` / `inReplyToPostId` 只说明「这条是回复」，回复正文要单独采
（`采集帖子评论` 模块尚未实现，见 README 的模块表）。

## 8. 并发限制

一个 `user-data-dir` 只能被一个 Chrome 实例占用，同一端口也不能同时跑两个采集进程。
多账号并行只能靠 **不同端口 + `--start/--end` 分段**。

## 9. 风控表现

- 页面出现 `Retry` 按钮：已自动重新加载，最多 3 次；
- 出现 `No results`：等 20~30 秒后跳过该链接；
- 连续滚动无新帖：`--empty-limit` 轮后判定到底；
- 仍未加载：降低 `--max-per-link`、加大 `--empty-limit`，或换账号槽位。
