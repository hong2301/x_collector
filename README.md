# X 采集器

基于 DrissionPage 的 X（Twitter）平台数据批量采集工具集，按功能拆分为多个独立模块。

## 模块

| 模块 | 说明 | 状态 |
|------|------|------|
| [输入关键词采集帖子](./输入关键词采集帖子/) | 根据搜索链接批量采集帖子正文及互动数据 | ✅ |
| 采集帖子评论 | 根据帖子链接采集评论区内容 | 🚧 |

---

## 多登录态浏览器（常驻端口）

### 原理

X 的搜索页和帖子页都需要登录态才能完整加载。本项目的做法是：

1. 手动启动若干个 **带调试端口** 的 Chrome，每个实例绑定 **独立的用户数据目录**（`--user-data-dir`）；
2. 每个实例里登录 **不同的 X 账号**，登录态就落在这个目录里；
3. 采集脚本通过 `Chromium(port)` 用 CDP **接管**对应实例，跟随该账号的登录态工作。

因此：**端口 = 账号槽位**，一一对应，端口和 `--user-data-dir` 必须配对记忆，改端口就等于换账号。

### 常驻端口

三个固定常驻端口，长期使用，不随临时调试改动：

| 槽位 | 调试端口 | 用户数据目录 |
|------|----------|--------------|
| 账号 1 | `5268` | `%LOCALAPPDATA%\Temp\DrissionPage\userData\5268` |
| 账号 2 | `5269` | `%LOCALAPPDATA%\Temp\DrissionPage\userData\5269` |
| 账号 3 | `5270` | `%LOCALAPPDATA%\Temp\DrissionPage\userData\5270` |

> `main.py` 的 `--port` 默认值即 **5268**（主账号）。
> 历史调试用过的其它端口（如 2728、9222 等）已废弃，不要再用。

### 启动（PowerShell）

```powershell
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$base   = Join-Path $env:LOCALAPPDATA 'Temp\DrissionPage\userData'

foreach ($p in 5268, 5269, 5270) {
    $dir = Join-Path $base "$p"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $args = @(
        "--remote-debugging-port=$p"
        "--user-data-dir=$dir"
        '--no-first-run'
        '--no-default-browser-check'
        '--hide-crash-restore-bubble'
        '--disable-features=PrivacySandboxSettings4'
        'https://x.com/home'
    )
    Start-Process -FilePath $chrome -ArgumentList $args
    Start-Sleep -Milliseconds 800
}
```

三个窗口起来后，分别在各自窗口登录不同的 X 账号（首次或登录态失效时才需要）。

### 验证端口是否就绪

```powershell
5270, 5269, 5268 | ForEach-Object {
    try { (Invoke-RestMethod "http://127.0.0.1:$_/json/version").Browser }
    catch { "port $_ : 未启动" }
}
```

能返回 Chrome 版本号即说明该端口已被 DrissionPage 正常接管。

### 采集（多账号分段并行）

`input.csv` 每行一条搜索链接，用 `--start/--end` 把行号切段，一个端口跑一段：

```bash
python main.py --port 5268 --start 1   --end 300
python main.py --port 5269 --start 301 --end 600
python main.py --port 5270 --start 601 --end 900
```

不传 `--start/--end` 则从头采到末尾，单账号串行跑：

```bash
python main.py --port 5268
```

### 关闭

直接关掉对应的 Chrome 窗口即可；脚本用 `Ctrl+C` 停止。

### 注意

- **一个 `user-data-dir` 同时只能被一个 Chrome 实例占用**。重复启动同一端口会复用不生效，必须先关掉旧实例。
- 端口被占用时先查进程：`Get-NetTCPConnection -LocalPort 5268 -State Listen`，再对应结束进程。
- Chrome 跟随系统代理（当前为 `192.168.31.238:7897`），需要代理才能访问 X。
- 登录态失效（被踢下线、改密、长期未登录）会在页面表现为未登录或风控页，重新在该端口的窗口里登录即可，目录不用重建。
- 采集期间不要手动操作被接管的窗口，避免抢焦点导致元素读取失败。
