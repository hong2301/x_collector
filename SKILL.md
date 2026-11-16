# SKILL —— 给维护者 / AI 的工作约定

## 定位

X 搜索页与帖子页的批量采集。核心手段是 **CDP 接管已登录的 Chrome**，
不碰 API、不用 token、不模拟登录。端口 = 账号槽位。

## 分层与放代码

| 层 | 文件 | 放什么 | 不放什么 |
|---|---|---|---|
| 功能层 | `code/features.py` | 业务流程、功能参数、CLI | DOM 细节 |
| 原子层 | `code/atoms.py` | 开端口、查登录、采一条搜索链接 | 字段解析 |
| 实现层 | `code/lib/*.py` | 一个文件一个领域 | 流程编排 |

新增字段：先在 `lib/dom.py`（或 `text/metrics/fiber`）加取数函数，再在 `lib/post.py` 组装，
最后更新 `doc/data-dictionary.md`。

## 禁区

1. **不要改 `lib/link.py` 的 UA 为浏览器 UA**——`t.co` 会对浏览器 UA 返回 200 中间页，展开就失效。
2. **不要在 `lib/fiber.py` 里改成递归遍历对象**——会把浏览器卡死；只用 `JSON.stringify` + 正则。
3. **不要用 `print`**，用 `lib.logger` 的 `log`，保证日志同时进 `logs/`。
4. **不要写死本机路径**（profile / Chrome / 代理），一律走 `.env` + `lib/config.env()`。
5. **不要删除 `data/posts` 下的 json** 做"清理"，那是唯一数据源。
6. 改完选择器必须用真实浏览器验证，不能只靠语法检查。
7. commit / push 只在用户明确要求时做。

## 验证清单（改完必跑）

```bash
python -m compileall -q code main.py                     # 语法
python code/features.py --help                           # CLI
python code/features.py stats                            # 读已有数据
python code/features.py login --ports 5269               # 登录态
python code/features.py search --port 5269 \
       --start 1 --end 1 --max-per-link 2 -o data/_probe  # 2 条真采
```

检查 `data/_probe/*.json`：

| 检查项 | 期望 |
|---|---|
| `username` | 形如 `@handle`（**不是** `ahttps://...`） |
| `nickname` / `profileUrl` | 非空，profileUrl 是 `https://x.com/<handle>` |
| `postTime` | ISO 时间，不是空 |
| `text` | 非空，emoji 未丢 |
| `likeCount` / `repostCount` | 数字字符串（可为 `"0"`） |
| `keywordText` / `keywordFlags` | 从 `keyword` 正确拆出 |
| 回复帖 | `isReply=1` 且 `inReplyToPostId` 有值 |
| 外链帖 | `externalLinkFinal` 不是 `t.co` 原链 |

验证后删掉 `data/_probe`。

## 常见故障定位

| 现象 | 先看 |
|---|---|
| 一条都采不到 | `features.py login`（登录态）→ `lib/dom.py` 选择器 |
| 字段大面积变空 | `lib/dom.py` 的 testid/class 兜底 |
| `externalLinkFinal` 等于 `externalLink` | `lib/link.py` 的 UA / 代理 |
| 一直"到底" | `--empty-limit` 太小，或页面被风控（看 `Retry`） |
| 词数统计不对 | `utils.keyword_text`（第一段才是词） |
| 端口连不上 | Chrome 是否带 `--remote-debugging-port`，profile 是否被占用 |
