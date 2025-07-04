"""Additional fields for Django forms."""

from __future__ import annotations

import copy
from typing import Any, Optional, TYPE_CHECKING, Union

import pytz
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, gettext
from typing_extensions import Self, TypeAlias

from djblets.conditions.choices import ConditionChoices
from djblets.conditions.conditions import ConditionSet
from djblets.conditions.errors import (ConditionChoiceNotFoundError,
                                       ConditionOperatorNotFoundError,
                                       InvalidConditionModeError,
                                       InvalidConditionValueError)
from djblets.forms.widgets import (ConditionsWidget,
                                   ConditionsWidgetChoices,
                                   ListEditWidget)

if TYPE_CHECKING:
    from djblets.conditions.conditions import ConditionSetData
    from djblets.util.typing import KwargsDict


TIMEZONE_CHOICES = tuple(zip(pytz.common_timezones, pytz.common_timezones))


#: The types of arguments available as choices to a ConditionsField.
#:
#: Version Added:
#:     5.3
ConditionsFieldChoices: TypeAlias = ConditionsWidgetChoices


class TimeZoneField(forms.ChoiceField):
    """A form field that only allows pytz common timezones as the choices."""

    def __init__(self, choices=TIMEZONE_CHOICES, *args, **kwargs):
        super(TimeZoneField, self).__init__(choices=choices, *args, **kwargs)


class ConditionsField(forms.Field):
    """A form field for customizing conditions required for an operation.

    This field is used for defining conditions under which something should
    be processed or run. It takes a condition choice registry, which may be
    one of the following:

    1. A :py:class:`~djblets.conditions.choices.ConditionChoices` instance
       (recommended)

    2. A :py:class:`~djblets.conditions.choices.ConditionChoices` subclass

    2. A callable returning a
       :py:class:`~djblets.conditions.choices.ConditionChoices` instance

    These define all the possible condition choices, each containing possible
    operators for that choice (such as "is," "is not," "starts with," etc.) and
    possible fields for inputting values.

    Version Changed:
        5.3:
        This class now explicitly supports instances of
        :py:class:`~djblets.conditions.choices.ConditionChoices`. Previous
        versions of Djblets supported this, but didn't document support.
    """

    widget = ConditionsWidget

    default_error_messages = {
        'condition_errors': _('There was an error with one of your '
                              'conditions.'),
        'invalid_mode': _('Must select either "All" or "Any".'),
        'value_required': _('A value is required for this condition.'),
    }

    ######################
    # Instance variables #
    ######################

    #: The field for selecting a choice.
    choice_field: forms.ChoiceField

    #: The field for selecting a mode for the choice.
    mode_field: forms.ChoiceField

    #: The field for selecting an operator.
    operator_field: forms.ChoiceField

    def __init__(
        self,
        choices: ConditionsFieldChoices,
        choice_kwargs: Optional[KwargsDict] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the field.

        Version Changed:
            5.3:
            ``choices`` may now be an instance of
            :py:class:`~djblets.conditions.choices.ConditionChoices`. Previous
            versions of Djblets supported this, but didn't document support.

        Args:
            choices (djblets.conditions.choices.ConditionChoices or type or
                     callable):
                The registry of choices available for the conditions.

                This should be an instance, a class, or a function that returns
                an instance. If a class or function is provided, the resulting
                instance will be constructed when the field is first
                instantiated and will be bound to the field. An instance
                should be used if you want to offer central registration of
                choices.

            choice_kwargs (dict, optional):
                Optional keyword arguments to pass to each
                :py:class:`~djblets.conditions.choices.BaseConditionChoice`
                constructor. This is useful for more advanced conditions that
                need additional data from the form.

            *args (tuple):
                Extra positional arguments for the field.

            **kwargs (dict):
                Extra keyword arguments for the field.
        """
        widget_cls = kwargs.get('widget', self.widget)

        self.mode_field = forms.ChoiceField(
            required=True,
            choices=(
                (ConditionSet.MODE_ALWAYS,
                 mark_safe(_('Always match'))),
                (ConditionSet.MODE_ALL,
                 mark_safe(_('Match <b>all</b> of the following:'))),
                (ConditionSet.MODE_ANY,
                 mark_safe(_('Match <b>any</b> of the following:')))
            ),
            widget=forms.widgets.RadioSelect())

        self.choice_field = forms.ChoiceField(
            required=True,
            choices=lambda: (
                (choice.choice_id, choice.name)
                for choice in self.choices
            ))

        self.operator_field = forms.ChoiceField(required=True)

        super().__init__(
            widget=widget_cls(choices=choices,
                              mode_widget=self.mode_field.widget,
                              choice_widget=self.choice_field.widget,
                              operator_widget=self.operator_field.widget,
                              choice_kwargs=choice_kwargs or {}),
            *args, **kwargs)

    @property
    def choices(self) -> ConditionChoices:
        """The condition choices for the field.

        Type:
            djblets.conditions.choices.ConditionChoices
        """
        return self.widget.choices

    @choices.setter
    def choices(
        self,
        value: ConditionsFieldChoices,
    ) -> None:
        """Set the condition choices for the field.

        Args:
            value (djblets.conditions.choices.ConditionChoices or type or
                   callable):
                The new choices value.
        """
        self.widget.choices = value

    @property
    def choice_kwargs(self) -> KwargsDict:
        """The keyword arguments passed to ConditionChoice functions.

        This is useful for more advanced conditions that need additional data
        from the form.

        This can be updated dynamically by the form during initialization.

        Type:
            dict
        """
        return self.widget.choice_kwargs

    @choice_kwargs.setter
    def choice_kwargs(
        self,
        value: KwargsDict,
    ) -> None:
        """The keyword arguments passed to ConditionChoice functions.

        Args:
            value (dict):
                The new condition choices value to set.
        """
        self.widget.choice_kwargs = value

    def prepare_value(
        self,
        value: Union[ConditionSet,
                     ConditionSetData],
    ) -> ConditionSetData:
        """Prepare the value for loading into the field.

        This will handle both a loaded
        :py:class:`~djblets.conditions.conditions.ConditionSet` instance or a
        serialized version of one (used when the form is saved), allowing
        either to be fed in.

        Args:
            data (object):
                The data as either a
                :py:class:`~djblets.conditions.conditions.ConditionSet`
                instance or a serialized dictionary.

        Returns:
            dict:
            The resulting serialized condition set for the widget.

        Raises:
            ValueError:
                The value provided is not valid for the widget.
        """
        if isinstance(value, ConditionSet):
            value = value.serialize()
        elif value is None:
            value = {
                'mode': ConditionSet.DEFAULT_MODE,
                'conditions': [],
            }

        if not isinstance(value, dict):
            raise ValueError(
                gettext('%r is not a valid value for a %s')
                % (value, self.__class__.__name__))

        return value

    def to_python(
        self,
        value: Optional[Any],
    ) -> Optional[ConditionSet]:
        """Parse and return conditions from the field's data.

        This takes the serialized values provided by the field's widget,
        ensures they're valid, and returns a list of the resulting conditions.

        Args:
            value (dict):
                The raw form data, as provided by the widget.

        Returns:
            djblets.conditions.conditions.ConditionSet:
            The resulting condition set from the form.

        Raises:
            django.core.exceptions.ValidationError:
                The data failed to deserialize or validate.
        """
        if not value:
            # Let validate() handle this. It will be run by clean() after this
            # method returns.
            return None

        widget = self.widget

        try:
            condition_set = ConditionSet.deserialize(
                self.choices,
                value,
                choice_kwargs=widget.choice_kwargs)
        except InvalidConditionModeError as e:
            raise forms.ValidationError(str(e),
                                        code='invalid_mode')
        except (ConditionChoiceNotFoundError,
                ConditionOperatorNotFoundError,
                InvalidConditionValueError) as e:
            error_messages = self.error_messages

            if getattr(e, 'code', None) == 'required':
                message = error_messages['value_required']
            else:
                message = str(e)

            widget.condition_errors[e.condition_index] = message

            raise forms.ValidationError(
                error_messages['condition_errors'],
                code='condition_errors')

        return condition_set

    def __deepcopy__(
        self,
        memo: dict[int, Any],
    ) -> Self:
        """Return a deep copy of the field.

        This will return a deep copy of this field and all subfields, so that
        a particular form instance can easily manipulate state without
        affecting other instances.

        Only the state that may be manipulated by an instance will be deep
        copied.

        Args:
            memo (dict):
                The memo dictionary used to track IDs to objects.

        Returns:
            ConditionsField:
            A deep copy of this field's instance.
        """
        obj = super().__deepcopy__(memo)
        obj.choice_field = copy.deepcopy(self.choice_field, memo)
        obj.mode_field = copy.deepcopy(self.mode_field, memo)
        obj.operator_field = copy.deepcopy(self.operator_field, memo)

        return obj


class ListEditField(forms.Field):
    """A form field for customizing a string representing a list of values.

    Version Added:
        3.0
    """

    widget = ListEditWidget

    def __init__(self, sep=',', *args, **kwargs):
        """Initialize the field.

        Args:
            sep (unicode, optional):
                The item separator.

            *args (tuple):
                Extra positional arguments for the field.

            **kwargs (dict):
                Extra keyword arguments for the field.
        """
        self._sep = sep

        super(ListEditField, self).__init__(*args, **kwargs)

    def prepare_value(self, data):
        """Prepare the value for loading into the field.

        This will take a string and split it into a list of
        strings according to the item separator.

        Args:
            data (unicode):
                The data as a unicode string.

        Returns:
            list:
            A list of strings for the widget.

        Raises:
            ValueError:
                The value provided is not valid for the widget.
        """
        if data is None:
            data = ''
        elif isinstance(data, list):
            return data
        elif not isinstance(data, str):
            raise ValueError(
                gettext('%r is not a valid value for a %s')
                % (data, self.__class__.__name__))

        return list(item.strip() for item in data.split(self._sep))

    def to_python(self, value):
        """Return a string of values from the field's data.

        This takes the list of values provided by the field's widget and
        returns a string of the values separated by the item separator.

        Args:
            value (list):
                The raw form data, as provided by the widget.

        Returns:
            unicode:
            The string representing the list of values.
        """
        if not value:
            return ''

        return self._sep.join(v.strip() for v in value)


class ListEditDictionaryField(ListEditField):
    """A form field for customizing a dictionary.

    Version Added:
        3.0
    """

    default_error_messages = {
        'duplicate_key_errors': _('All keys must be unique.')
    }

    def prepare_value(self, data):
        """Prepare the value for loading into the field.

        This will take a dictionary and split it into a list of
        (key, value) tuples.

        Args:
            data (dict):
                The data as a dictionary.

        Returns:
            list:
            A list of (key, value) tuples for the widget.

        Raises:
            ValueError:
                The value provided is not valid for the widget.
        """
        if data is None:
            data = {}
        elif isinstance(data, list):
            return data
        elif not isinstance(data, dict):
            raise ValueError(
                gettext('%r is not a valid value for a %s')
                % (data, self.__class__.__name__))

        return_data = []

        for key, value in data.items():
            return_data.append((key, value))

        return return_data

    def to_python(self, value):
        """Return a dictionary from the field's data.

        This takes the list of (key, value) tuples provided by the
        field's widget and returns a dictionary containing the keys
        with their corresponding values.

        Args:
            value (list):
                The raw form data, as provided by the widget.

        Returns:
            dict:
            The dictionary representing the list of (key, value) pairs.

        Raises:
            django.forms.ValidationError:
                The list contains duplicate keys.
        """
        if not value:
            return {}

        return_dict = {}

        for key, val in value:
            if key in return_dict:
                raise forms.ValidationError(
                    self.error_messages['duplicate_key_errors'],
                    code='duplicate_key_errors')

            return_dict[key] = val

        return return_dict
