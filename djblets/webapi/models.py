from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from djblets.db.fields import JSONField
from djblets.webapi.managers import WebAPITokenManager
from djblets.webapi.signals import webapi_token_updated


class BaseWebAPIToken(models.Model):
    """Base class for an access token used for authenticating with the API.

    Each token can be used to authenticate the token's owner with the API,
    without requiring a username or password to be provided. Tokens can
    be revoked, and new tokens added.

    Tokens can store policy information, which will later be used for
    restricting access to the API.
    """

    user = models.ForeignKey(User,
                             related_name='webapi_tokens',
                             on_delete=models.CASCADE)

    token = models.CharField(max_length=40, unique=True)
    time_added = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    note = models.TextField(blank=True)
    policy = JSONField(null=True)

    extra_data = JSONField(null=True)

    objects = WebAPITokenManager()

    def is_accessible_by(self, user):
        return user.is_superuser or self.user == user

    def is_mutable_by(self, user):
        return user.is_superuser or self.user == user

    def is_deletable_by(self, user):
        return user.is_superuser or self.user == user

    def __str__(self):
        return 'Web API token for %s' % self.user

    def save(self, *args, **kwargs):
        """Save the token.

        If the token is being updated, the
        :py:data:`~djblets.webapi.signals.webapi_token_updated` signal will be
        emitted.

        Args:
            *args (tuple):
                Positional arguments to pass to the superclass.

            **kwargs (dict):
                Keyword arguments to pass to the superclass.
        """
        is_new = self.pk is None

        super(BaseWebAPIToken, self).save(*args, **kwargs)

        if not is_new:
            webapi_token_updated.send(instance=self, sender=type(self))

    @classmethod
    def get_root_resource(self):
        raise NotImplementedError

    @classmethod
    def validate_policy(cls, policy):
        """Validate an API policy.

        This will check to ensure that the policy is in a suitable format
        and contains the information required in a format that can be parsed.

        If a failure is found, a ValidationError will be raised describing
        the error and where it was found.
        """
        if not isinstance(policy, dict):
            raise ValidationError(_('The policy must be a JSON object.'))

        if not policy:
            # Empty policies are equivalent to allowing full access. If this
            # is empty, we can stop here.
            return

        if 'resources' not in policy:
            raise ValidationError(
                _('The policy is missing a "resources" section.'))

        resources_section = policy['resources']

        if not isinstance(resources_section, dict):
            raise ValidationError(
                _('The policy\'s "resources" section must be a JSON object.'))

        if not resources_section:
            raise ValidationError(
                _('The policy\'s "resources" section must not be empty.'))

        if '*' in resources_section:
            cls._validate_policy_section(resources_section, '*',
                                         'resources.*')

        resource_policies = [
            (section_name, section)
            for section_name, section in resources_section.items()
            if section_name != '*'
        ]

        if resource_policies:
            valid_policy_ids = \
                cls._get_valid_policy_ids(cls.get_root_resource())

            for policy_id, section in resource_policies:
                if policy_id not in valid_policy_ids:
                    raise ValidationError(
                        _('"%s" is not a valid resource policy ID.')
                        % policy_id)

                for subsection_name, subsection in section.items():
                    if not isinstance(subsection_name, str):
                        raise ValidationError(
                            _('%s must be a string in "resources.%s"')
                            % (subsection_name, policy_id))

                    cls._validate_policy_section(
                        section, subsection_name,
                        'resources.%s.%s' % (policy_id, subsection_name))

    @classmethod
    def _validate_policy_section(cls, parent_section, section_name,
                                 full_section_name):
        section = parent_section[section_name]

        if not isinstance(section, dict):
            raise ValidationError(
                _('The "%s" section must be a JSON object.')
                % full_section_name)

        if 'allow' not in section and 'block' not in section:
            raise ValidationError(
                _('The "%s" section must have "allow" and/or "block" '
                  'rules.')
                % full_section_name)

        if 'allow' in section and not isinstance(section['allow'], list):
            raise ValidationError(
                _('The "%s" section\'s "allow" rule must be a list.')
                % full_section_name)

        if 'block' in section and not isinstance(section['block'], list):
            raise ValidationError(
                _('The "%s" section\'s "block" rule must be a list.')
                % full_section_name)

    @classmethod
    def _get_valid_policy_ids(cls, resource, result=None):
        if result is None:
            result = set()

        if hasattr(resource, 'policy_id'):
            result.add(resource.policy_id)

        for child_resource in resource.list_child_resources:
            cls._get_valid_policy_ids(child_resource, result)

        for child_resource in resource.item_child_resources:
            cls._get_valid_policy_ids(child_resource, result)

        return result

    class Meta:
        abstract = True
        verbose_name = _('Web API token')
        verbose_name_plural = _('Web API tokens')
