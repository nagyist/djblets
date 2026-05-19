"""Common symbols useful for function signatures.

Version Changed:
    6.0:
    This module now just forwards to :py:mod:`typelets.symbols`. Imports to
    this module will be deprecated in a future release.

Version Added:
    3.3
"""

from __future__ import annotations

from typelets.symbols import UNSET, UnsetSymbol, Unsettable


__all__ = [
    'UNSET',
    'UnsetSymbol',
    'Unsettable',
]
