"""Error classes for conditions."""

from __future__ import annotations

from djblets.registries.errors import AlreadyRegisteredError, ItemLookupError


class ConditionChoiceConflictError(AlreadyRegisteredError):
    """A condition choice conflicts with another registered choice."""


class ConditionChoiceNotFoundError(ItemLookupError):
    """A condition choice was not found.

    Version Changed:
        6.0:
        Added support for Python type hints.
    """

    ######################
    # Instance variables #
    ######################

    #: The ID of the choice that could not be found.
    choice_id: str | None

    #: The index of the condition this error applies to within the set.
    condition_index: int | None

    def __init__(
        self,
        message: str,
        condition_index: (int | None) = None,
        choice_id: (str | None) = None,
    ) -> None:
        """Initialize the error.

        Args:
            message (str):
                The error message.

            condition_index (int, optional):
                The index of the condition this error applies to within
                the condition set.

            choice_id (str, optional):
                The ID of the choice that could not be found.
        """
        super().__init__(message)

        self.condition_index = condition_index
        self.choice_id = choice_id


class ConditionOperatorConflictError(AlreadyRegisteredError):
    """A condition operator conflicts with another registered operator."""


class ConditionOperatorNotFoundError(ItemLookupError):
    """A condition operator was not found.

    Version Changed:
        6.0:
        Added support for Python type hints.
    """

    ######################
    # Instance variables #
    ######################

    #: The index of the condition this error applies to within the set.
    condition_index: int | None

    #: The ID of the operator that could not be found.
    operator_id: str | None

    def __init__(
        self,
        message: str,
        condition_index: (int | None) = None,
        operator_id: (str | None) = None,
    ) -> None:
        """Initialize the error.

        Args:
            message (str):
                The error message.

            condition_index (int, optional):
                The index of the condition this error applies to within
                the condition set.

            operator_id (str, optional):
                The ID of the operator that could not be found.
        """
        super().__init__(message)

        self.condition_index = condition_index
        self.operator_id = operator_id


class InvalidConditionModeError(ValueError):
    """The condition mode provided was invalid."""


class InvalidConditionValueError(ValueError):
    """The condition value provided was invalid.

    Version Changed:
        6.0:
        Added support for Python type hints.
    """

    ######################
    # Instance variables #
    ######################

    #: The error code.
    #:
    #: This will generally correspond to a form validation error code.
    code: str | None

    #: The index of the condition this error applies to within the set.
    condition_index: int | None

    def __init__(
        self,
        message: str,
        code: (str | None) = None,
        condition_index: (int | None) = None,
    ) -> None:
        """Initialize the error.

        Args:
            message (str):
                The error message.

            code (str, optional):
                The error code. This will generally correspond to a form
                validation error code.

            condition_index (int, optional):
                The index of the condition this error applies to within
                the condition set.
        """
        super().__init__(message)

        self.code = code
        self.condition_index = condition_index
