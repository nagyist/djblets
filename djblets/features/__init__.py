"""Feature switch support for applications.

This module contains convenience imports for:

* :py:class:`~djblets.features.feature.Feature`
* :py:class:`~djblets.features.feature.FeatureLevel`
* :py:class:`~djblets.features.registry.get_features_registry`
"""

from __future__ import annotations

from djblets.features.feature import Feature
from djblets.features.level import FeatureLevel
from djblets.features.registry import get_features_registry


__all__ = [
    'Feature',
    'FeatureLevel',
    'get_features_registry',
]


__autodoc_excludes__ = __all__
