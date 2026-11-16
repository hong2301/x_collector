"""只读检查各端口登录的 X 账号（不导航、不点击）。

用法：
    python code/check_login.py
    python code/check_login.py --ports 5268 5269
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features import main  # noqa: E402

if __name__ == "__main__":
    main(["login"] + sys.argv[1:])
