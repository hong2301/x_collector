"""全局配置：路径常量与可配置参数。

本机指纹（profile 根目录 / 代理 / Chrome / 默认端口）全部来自 .env，
代码里不留本机绝对路径，见 .env.example。
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))       # code/lib
CODE_DIR = os.path.dirname(HERE)                        # code
ROOT = os.path.dirname(CODE_DIR)                        # 项目根

DATA_DIR = os.path.join(ROOT, "data")
POSTS_DIR = os.path.join(DATA_DIR, "posts")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
ARCHIVE_DIR = os.path.join(DATA_DIR, "_archive")
LOG_DIR = os.path.join(ROOT, "logs")
INPUT_FILE = os.path.join(CODE_DIR, "input.csv")

# 登录态判定用的 cookie
LOGIN_COOKIE = "auth_token"


def _load_env(path):
    """极简 .env 解析：KEY=VALUE，支持 # 注释与引号。"""
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


_ENV = _load_env(os.path.join(ROOT, ".env"))


def env(name, default=""):
    """优先环境变量，其次 .env，最后默认值。"""
    return os.environ.get(name) or _ENV.get(name) or default


def _parse_profile_map(raw):
    """解析 `5268=x1,5269=x2` 形式的端口 → profile 目录名映射。"""
    mapping = {}
    for item in (raw or "").split(","):
        if "=" not in item:
            continue
        port, name = item.split("=", 1)
        port, name = port.strip(), name.strip()
        if port.isdigit() and name:
            mapping[int(port)] = name
    return mapping


# ---------- 本机指纹 ----------
PROFILE_ROOT = env("X_PROFILE_ROOT", os.path.expanduser("~/.pi/agent/browser-profile"))
PROFILE_MAP = _parse_profile_map(env("X_PROFILE_MAP", "5268=x1,5269=x2,5270=x3"))
PROXY = env("X_PROXY", "")
CHROME = env("X_CHROME", "")
DEFAULT_PORT = int(env("X_PORT", "5268"))

# ---------- 采集参数默认值（CLI 可覆盖） ----------
# 每条搜索链接最多采集的帖子数
MAX_PER_LINK = int(env("X_MAX_PER_LINK", "30"))
# 每个关键词的目标条数，达标后跳过该词剩余链接；0 表示不限制
MAX_PER_KEYWORD = int(env("X_MAX_PER_KEYWORD", "310"))
# 连续多少轮滚动没有新帖就认为该搜索已到底
EMPTY_SCROLL_LIMIT = int(env("X_EMPTY_SCROLL_LIMIT", "5"))
# 外链展开（t.co 跟随重定向）超时
EXPAND_TIMEOUT = float(env("X_EXPAND_TIMEOUT", "10"))
