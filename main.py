"""兼容入口：等价于 `python code/features.py`。

保留旧命令习惯，例如：
    python main.py --port 5268 --start 1 --end 300
"""

import os
import sys

CODE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from features import main  # noqa: E402

if __name__ == "__main__":
    main()
