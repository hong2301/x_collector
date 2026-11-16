"""浏览器会话状态：接管端口、选择标签页。

session 持有全局状态，其它模块通过 get_tab() 取用。
"""

from . import browser

_state = {"port": None, "br": None, "tab": None}


def open_port(port):
    """接管端口；未启动时按 profile 拉起（保留登录态）。"""
    br = browser.attach(port)
    _state.update(port=port, br=br, tab=None)
    return br


def is_connected():
    return _state["br"] is not None


def get_browser():
    if _state["br"] is None:
        raise RuntimeError("浏览器尚未连接，请先调用 open_port(port)")
    return _state["br"]


def pick_tab(keyword="x.com"):
    """优先复用已打开目标站点的标签页，避免新开丢状态。"""
    br = get_browser()
    tabs = br.get_tabs()
    for tab in tabs:
        if keyword in (tab.url or ""):
            _state["tab"] = tab
            return tab
    tab = tabs[0] if tabs else br.new_tab()
    _state["tab"] = tab
    return tab


def get_tab():
    if _state["tab"] is None:
        return pick_tab()
    return _state["tab"]


def state():
    """调试用：查看当前会话状态。"""
    return dict(_state)
