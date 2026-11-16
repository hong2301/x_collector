# 项目索引

按「想找什么 → 去哪里看」组织。新增文件请同步更新此表。

## 1. 目录职责

| 目录 | 放什么 | 不放什么 |
|---|---|---|
| `code/` | 可执行代码 + 输入清单 | 数据、日志 |
| `code/lib/` | 实现层，一个文件一个领域 | 业务流程编排 |
| `data/posts/` | **唯一产物**：每帖一个 JSON（已 gitignore） | 派生物 |
| `data/images/` | 图片截图 JSON（webp base64 + 空 ocr 字段） | 帖子正文 |
| `.env` | 本机指纹（profile / 代理 / Chrome / 端口），已 gitignore | 提交 |
| `doc/` | 字段定义、已知问题、端口槽位 | 代码 |
| `logs/` | 运行日志（已 gitignore） | — |

## 2. 代码文件索引

### 入口层

| 文件 | 职责 | 关键内容 |
|---|---|---|
| `code/features.py` | **功能层**（原子组合 + 参数 + CLI） | `collect_search_posts` / `show_stats` / `show_login` / `main` |
| `code/atoms.py` | **原子层**（最小可执行单元） | `open_port` / `check_login` / `account_info` / `collect_search_link` |
| `main.py` | 兼容入口 | 转发到 `code/features.py` |
| `code/check_login.py` | 只读检查登录 | 等价 `features.py login` |

### 实现层 `code/lib/`

| 文件 | 职责 | 关键内容 |
|---|---|---|
| `config.py` | 路径常量 + `.env` | `POSTS_DIR` / `IMAGES_DIR` / `LOG_DIR` / `env()` / `PROFILE_MAP` / `MAX_PER_LINK` |
| `logger.py` | 双写日志 | `get_logger()` / `setup()`，控制台 + `logs/*.log` |
| `browser.py` | Chrome CDP 接管 | `attach(port)` / `profile_name` / `profile_path` / `wait_doc` |
| `session.py` | 会话状态 | `open_port` / `pick_tab` / `get_tab` / `state` |
| `auth.py` | 登录检测 | `is_logged_in`（读 `auth_token`）/ `account_info`（twid） |
| `dom.py` | 选择器与安全取数 | `find_post_link` / `find_body` / `find_user` / `find_stats_label` / `find_reply_target` / `find_quote` / `is_ad` / `no_result` / `has_retry` / `click_expand` |
| `text.py` | 正文解析 | `parse_body`（emoji / hashtags / mentions / links） |
| `metrics.py` | 互动指标 | `parse_metrics`（aria-label）/ `pure_retweet` |
| `fiber.py` | React Fiber 取数 | `extract`（quote_count / conversation_id_str / in_reply_to_status_id_str / retweeted_status_result）/ `quote_url` |
| `link.py` | 外链展开 | `expand` / `expand_all` / `self_test` |
| `media.py` | 媒体 | `collect` / `save_image` |
| `scroll.py` | 滚动 | `to_top` / `step` / `reload_unless_retry` |
| `utils.py` | 通用工具 | `read_input` / `select_range` / `keyword_text` / `keyword_flags` / `count_keywords` / `pick_pause` |
| `store.py` | 落盘 | `post_id_of` / `build_record` / `write` |
| `post.py` | 单帖解析 | `extract`（组合 dom/text/metrics/fiber/media） |

## 3. 文档索引

| 文档 | 内容 |
|---|---|
| `README.md` | 给人看：结构、端口槽位、用法、配置 |
| `SKILL.md` | 给 AI 看：维护约定、禁区、验证清单 |
| `doc/INDEX.md` | 本文件：文件职责、数据流、新增代码放哪 |
| `doc/data-dictionary.md` | 帖子 JSON 字段定义与来源 |
| `doc/known-issues.md` | 已知问题：选择器脆弱点、未填充字段、登录态 |

## 4. 数据流

```
code/input.csv（url,关键词）
   │
   ▼
features.collect_search_posts(input_file, start, end, port, ...)
   │  utils.read_input → select_range（1-based 数据行）
   │  utils.count_keywords(data/posts) → 每词已有数
   ├─ atoms.open_port(port)          CDP 接管（profile 按端口映射）
   ├─ atoms.check_login()            只读 auth_token cookie
   └─ for (url, keyword) in tasks:
        atoms.collect_search_link(url, keyword, ...)
          ├─ tab.get(url) + 回顶 3 次
          ├─ while 未连续 N 轮空转:
          │    ├─ Retry 按钮 → 重新加载
          │    ├─ No results → 等 20~30s 跳过
          │    ├─ for article in 页面:
          │    │    post.extract(...) → dom + text + metrics + fiber
          │    │    store.write() → data/posts/<status_id>.json
          │    └─ scroll 300px
          └─ 达标（链接/词）或到底 → 返回原因
   │
   ▼
data/posts/<status_id>.json
```

## 5. 常用命令

```bash
python code/features.py                      # 默认全量采集
python code/features.py --port 5268 --start 1 --end 300
python code/features.py search --port 5269 --start 301 --end 600
python code/features.py search --media --no-expand-links
python code/features.py stats                # 各词已采数量
python code/features.py login                # 各端口登录态
python code/lib/link.py                      # 外链展开自检
```

## 6. 新增代码怎么放

| 要做的事 | 放哪 |
|---|---|
| 新的 DOM 取数（某字段/某选择器） | `lib/dom.py` 加函数，`lib/post.py` 调用 |
| 新的解析逻辑（文本/指标/媒体） | 对应 `lib/*.py`，不写进流程 |
| 新的原子能力 | `lib/` 实现 + `atoms.py` 加一个函数 |
| 新的业务流程（如评论采集） | `features.py` 加函数 + 子命令 |
| 新参数 | 功能函数签名 + `features.py` 的 argparse（参数跟功能走） |
| 新文档 | `doc/`，并更新本文件第 3 节 |
