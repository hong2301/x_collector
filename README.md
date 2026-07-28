# X 采集器

基于 DrissionPage 的 X（Twitter）平台数据批量采集工具集，按功能拆分为多个独立模块。

## 功能模块

| 模块 | 说明 | 状态 |
|------|------|------|
| [输入关键词采集帖子](./输入关键词采集帖子/) | 根据搜索链接批量采集帖子（正文、互动数据等） | ✅ 已完成 |
| 采集帖子评论 | 根据帖子链接采集评论区内容 | 🚧 规划中 |

## 环境要求

- Python 3.8+
- Chrome 浏览器（需开启调试端口 2728）
- DrissionPage

```bash
pip install DrissionPage
```

## 通用流程

1. 启动 Chrome 调试模式（端口 2728）
2. 进入对应模块目录，准备 `input.csv`
3. 运行 `python main.py`
4. 查看输出的 `output.csv`

## 目录结构

```
x采集器/
├── README.md                   # 项目总览
├── 输入关键词采集帖子/           # 模块 1
│   ├── main.py
│   ├── README.md
│   ├── input.csv
│   └── output.csv
├── 采集帖子评论/                 # 模块 2（规划中）
│   └── ...
└── ...
```
