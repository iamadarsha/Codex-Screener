"""Rate limiter singleton — imported by main.py and route modules."""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage (per-process). Safe for single Railway instance.
# To share limits across multiple instances, set storage_uri to Redis URL here.
limiter = Limiter(key_func=get_remote_address)
