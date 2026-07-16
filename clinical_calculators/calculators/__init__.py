"""Implemented calculator modules.

Each implemented formula lives in a specialty-oriented subpackage. The registry
imports this package to build the name-to-function implementation map.
"""

from .common import IMPLEMENTATIONS as COMMON_IMPLEMENTATIONS
from .common import IMPLEMENTATIONS_BY_ID as COMMON_IMPLEMENTATIONS_BY_ID

IMPLEMENTATIONS = {
    **COMMON_IMPLEMENTATIONS,
}

IMPLEMENTATIONS_BY_ID = {
    **COMMON_IMPLEMENTATIONS_BY_ID,
}

__all__ = ["IMPLEMENTATIONS", "IMPLEMENTATIONS_BY_ID"]
