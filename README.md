# x_collector

X（Twitter）数据采集工具集，基于 DrissionPage 通过 CDP 接管**已登录的真实 Chrome**，
不走 API、不用 token。分层结构：**功能层 → 原子层 → 实现层**。

## 怎么读这个项目

| 顺序 | 看什么 | 能知道什么 |
|---|---|---|
| 1 | `doc/INDEX.md` | 每个文件干什么、数据怎么流、新增代码放哪 |
| — | `SKILL.md` | 给 AI/维护者：约定、禁区、验证清单 |
| 2 | `code/features.py` | 业务入口：有哪些功能，参数是什么 |
| 3 | `code/atoms.py` | 原子能力：开端口、查登录、采一条搜索链接 |
| 4 | `code/lib/` | 具体实现：DOM 取数、fiber 取数、正文/指标解析、落盘 |
| 5 | `doc/` | 字段定义、已知问题、端口槽位 |

## 结构

```
x_collector/
├── README.md            给人看：怎么用、怎么读
├── SKILL.md             给 AI 看：维护约定、禁区、验证清单
├── main.py              兼容入口（等价 python code/features.py）
├── .env.example         本机指纹模板（profile / 代理 / Chrome / 端口）
├── code/
│   ├── features.py      功能层（原子组合 + 功能参数 + CLI）
│   ├── atoms.py         原子层（开端口 / 查登录 / 采一条搜索链接）
│   ├── check_login.py   只读检查各端口登录的账号
│   ├── input.csv        输入清单（url,关键词）
│   └── lib/             实现层
│       ├── config.py      路径常量 + .env
│       ├── logger.py      双写日志（控制台 + logs/*.log）
│       ├── browser.py     Chrome CDP 接管 + profile 映射
│       ├── session.py     会话状态（端口 / 浏览器 / 标签页）
│       ├── auth.py        登录检测 / 账号指纹
│       ├── dom.py         页面选择器与安全取数（改版先改这里）
│       ├── text.py        正文解析（emoji / 话题 / 提及 / 外链）
│       ├── metrics.py     互动指标（aria-label）
│       ├── fiber.py       React Fiber 取数（quote_count / 会话 ID / 转发来源）
│       ├── link.py        t.co 短链展开
│       ├── media.py       媒体列表 + 图片截图
│       ├── scroll.py      滚动与重试
│       ├── utils.py       输入清单 / 切片 / 关键词统计 / 停顿
│       ├── store.py       帖子 JSON 落盘
│       └── post.py        单帖解析（组合上面这些）
├── data/
│   ├── posts/           每帖一个 JSON（唯一产物，已 gitignore）
│   └── images/          图片截图 JSON（webp base64）
├── doc/                 细分文档
└── logs/                运行日志（已 gitignore）
```

## 数据源约定

**`data/posts/<status_id>.json` 是唯一产物。** `data/images/` 是图片的截图，
统计和交付请直接读 `data/posts`。

字段定义见 `doc/data-dictionary.md`；统计已采数量：

```bash
python code/features.py stats
```

## 端口 = 账号槽位

X 的搜索页和帖子页都要登录态。做法是：手动启动若干**带调试端口**的 Chrome，
每个实例绑定**独立的用户数据目录**，各登录不同账号；采集脚本通过 CDP 接管对应实例。

| 槽位 | 调试端口 | 用户数据目录 |
|------|----------|--------------|
| 账号 1 | `5268` | `C:\Users\jiang\.pi\agent\browser-profile\x1` |
| 账号 2 | `5269` | `C:\Users\jiang\.pi\agent\browser-profile\x2` |
| 账号 3 | `5270` | `C:\Users\jiang\.pi\agent\browser-profile\x3` |

映射写在 `.env` 的 `X_PROFILE_MAP`，已登记在 `browser-profile\registry.json`（`platform=x`）。

> 迁移记录：用户数据目录原在 `%LOCALAPPDATA%\Temp\DrissionPage\userData\<端口>`，
> 因 Temp 被清理导致登录态丢失，现统一放在 `browser-profile\` 下。

### 启动（PowerShell）

```powershell
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$base   = 'C:\Users\jiang\.pi\agent\browser-profile'

foreach ($x in @(@{p=5268;d='x1'}, @{p=5269;d='x2'}, @{p=5270;d='x3'})) {
    $dir = Join-Path $base $x.d
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $args = @(
        "--remote-debugging-port=$($x.p)"
        "--user-data-dir=$dir"
        '--no-first-run'
        '--no-default-browser-check'
        '--hide-crash-restore-bubble'
        '--disable-features=PrivacySandboxSettings4'
        'https://x.com/home'
    )
    Start-Process -FilePath $chrome -ArgumentList $args
    Start-Sleep -Seconds 10   # 必须等够，太短会被转发到前一个实例
}
```

三个窗口起来后，分别在各自窗口登录不同的 X 账号（首次或登录态失效时才需要）。

### 检查登录态

```bash
python code/features.py login            # 全部已登记槽位
python code/check_login.py --ports 5268  # 指定端口
```

## 用法

```bash
pip install DrissionPage lxml requests   # 依赖

python code/features.py                  # 默认：全量采 input.csv
python code/features.py --port 5268 --start 1 --end 300    # 旧式参数也兼容
python code/features.py search --port 5268 --start 1 --end 300
python code/features.py search --port 5269 --start 301 --end 600 --max-per-link 30
python code/features.py search -i code/input_round3_top27.csv --max-per-keyword 100
python code/features.py search --media --no-expand-links   # 开媒体、不展开外链
python code/features.py stats
```

也可以用 `python main.py ...`（兼容旧命令）或 `python code/check_login.py`。

### 多账号分段并行

`input.csv` 每行一条链接，用 `--start/--end`（**数据行号，1-based**）把清单切段，
一个端口跑一段：

```bash
python code/features.py search --port 5268 --start 1   --end 300
python code/features.py search --port 5269 --start 301 --end 600
python code/features.py search --port 5270 --start 601 --end 900
```

## 输入清单

`code/input.csv`，有表头：

```csv
url,关键词
https://x.com/search?q=Beijing%20since%3A2026-01-01%20until%3A2026-01-31&src=typed_query,Beijing|2026-01-01~2026-01-31
https://x.com/josebcollazo/status/1114261097983430656,E7|reply|0
```

关键词列是**复合标记**：`词|分段`，词用于「每词达标即停」的去重统计，
其余段由调用方自行解释（例如时间区间或任务类型）。采集时整串原样存进
`keyword`，拆出的词存进 `keywordText`。

## 采集控制逻辑

- 每条链接最多采 `--max-per-link` 条（默认 30），达到后进入下一条
- 每个词达到 `--max-per-keyword` 条（默认 310）就跳过该词剩余链接（启动时先统计 `data/posts`）
- 连续 `--empty-limit` 轮滚动没有新帖就认为该搜索到底（默认 5）
- 页面出现 `No results` 等 20~30 秒后跳过；出现 `Retry` 按钮自动重新加载最多 3 次
- 每条链接采得少于 60 条时额外等 10~20 秒，避免请求过密被限流
- 同一帖子被多条链接命中时后写的覆盖前写的（文件名是 status id）

## 配置（本机指纹）

复制 `.env.example` 为 `.env` 后按本机情况填写，`.env` 不进版本库：

```
X_PROFILE_ROOT=C:\Users\<you>\.pi\agent\browser-profile
X_PROFILE_MAP=5268=x1,5269=x2,5270=x3
X_PROXY=http://192.168.31.238:7897     # 外链展开与 Chrome 都走它
X_CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
X_PORT=5268
```

采集参数也能用环境变量给默认值：`X_MAX_PER_LINK` / `X_MAX_PER_KEYWORD` /
`X_EMPTY_SCROLL_LIMIT` / `X_EXPAND_TIMEOUT`。

## 注意

- **一个 `user-data-dir` 同时只能被一个 Chrome 实例占用**。重复启动同一端口会复用不生效，必须先关掉旧实例。
- 端口被占用先查进程：`Get-NetTCPConnection -LocalPort 5268 -State Listen`。
- 采集期间不要手动操作被接管的窗口，避免抢焦点导致元素读取失败。
- X 前端改版会让 class 选择器失效，采集为空时先看 `code/lib/dom.py`（`data-testid` 优先，class 兜底）。
