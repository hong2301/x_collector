"""登录状态检测与账号指纹（只读，不导航页面）。"""

from .config import LOGIN_COOKIE
from .session import get_tab


def _cookies(tab):
    try:
        return tab.cookies(all_domains=False) or []
    except Exception:
        return []


def is_logged_in(tab=None):
    """只读 cookie 判断登录态。返回 (bool, 说明)。"""
    tab = tab or get_tab()
    names = {c.get("name") for c in _cookies(tab) if isinstance(c, dict)}
    if LOGIN_COOKIE not in names:
        return False, f"{LOGIN_COOKIE} cookie 不存在"
    if "/login" in (tab.url or "") or "/i/flow/login" in (tab.url or ""):
        return False, "页面被重定向到登录页"
    return True, "ok"


def account_info(tab=None):
    """读当前标签页的账号指纹：url / 显示名 / twid。"""
    tab = tab or get_tab()
    info = {"url": "", "name": "", "twid": "", "logged_in": False}
    try:
        info["url"] = (tab.url or "")[:120]
    except Exception:
        pass
    try:
        btn = tab.ele("@data-testid=SideNav_AccountSwitcher_Button", timeout=1)
        if btn:
            info["name"] = " ".join((btn.text or "").split())[:60]
    except Exception:
        pass
    for c in _cookies(tab):
        if isinstance(c, dict) and c.get("name") == "twid":
            info["twid"] = (c.get("value") or "")[:40]
    info["logged_in"], _ = is_logged_in(tab)
    return info
