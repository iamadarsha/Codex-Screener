from __future__ import annotations

import sys
from urllib.error import URLError
from urllib.request import urlopen


def main() -> int:
    try:
        with urlopen("http://127.0.0.1:8000/health", timeout=3) as response:
            if response.status != 200:
                return 1
    except URLError:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
