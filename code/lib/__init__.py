"""lib —— 实现层（按领域拆分，不含业务流程）。

config.py    路径常量 + .env（本机指纹）
logger.py    双写日志
browser.py   Chrome CDP 接管 + profile 映射
session.py   会话状态（端口 / 浏览器 / 标签页）
auth.py      登录检测 / 账号指纹
dom.py       页面选择器与安全取数（改版先改这里）
text.py      正文解析（emoji / 话题 / 提及 / 外链）
metrics.py   互动指标（aria-label）
fiber.py     React Fiber 取数（quote_count / 会话 ID / 转发来源）
link.py      t.co 短链展开
media.py     媒体列表 + 图片截图
scroll.py    滚动与重试
utils.py     输入清单 / 切片 / 关键词统计 / 停顿
store.py     帖子 JSON 落盘
post.py      单帖解析（组合上面这些）
"""
