"""Evolution to remove unique constraint from StoredConsentData."""

from __future__ import annotations

from django_evolution.mutations import ChangeField


MUTATIONS = [
    ChangeField('StoredConsentData', 'audit_identifier', initial=None,
                unique=False),
]
