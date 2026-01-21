"""App configuration for djblets.privacy."""

from __future__ import annotations

from django.apps import AppConfig


class PrivacyAppConfig(AppConfig):
    """Default app configuration for djblets.privacy."""

    name = 'djblets.privacy'
    label = 'djblets_privacy'
