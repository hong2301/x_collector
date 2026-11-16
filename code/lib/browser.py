"""浏览器附着：从 CDP 端口接管已登录的 Chrome。

端口 = 账号槽位。profile 目录由 .env 的 X_PROFILE_ROOT / X_PROFILE_MAP 决定，
默认 5268→x1、5269→x2、5270→x3。
"""

import os
import time

from DrissionPage import Chromium, ChromiumOptions

from . import config


def profile_name(port=None):
    """端口对应的 profile 目录名；未登记的端口回退 `x<port>`。"""
    port = port or config.DEFAULT_PORT
    return config.PROFILE_MAP.get(port, f"x{port}")


def profile_path(port=None):
    """登录态 profile 目录：PROFILE_ROOT/<name>。"""
    return os.path.join(config.PROFILE_ROOT, profile_name(port))


def attach(port=None, timeout=20):
    """接管端口上的 Chrome。

    必须同时设置 user_data_path：否则端口空着时 DrissionPage 会拿临时 profile
    拉一个空白浏览器，登录态就丢了。
    """
    port = port or config.DEFAULT_PORT
    co = ChromiumOptions()
    if config.CHROME:
        co.set_browser_path(config.CHROME)
    co.set_user_data_path(profile_path(port))
    co.set_local_port(port)
    if config.PROXY:
        co.set_proxy(config.PROXY)
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")
    co.set_argument("--hide-crash-restore-bubble")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--disable-popup-blocking")
    return Chromium(co)


def wait_doc(tab, timeout=15):
    """等待页面加载完成；刷新瞬间会抛异常，容错重试。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if tab.run_js("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False
