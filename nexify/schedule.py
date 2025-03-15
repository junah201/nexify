from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Annotated, Literal

from nexify.dependencies.utils import get_dependant
from nexify.middleware import RequestParsingMiddleware
from nexify.operation import Operation, OperationManager
from nexify.types import HandlerType
from typing_extensions import Doc


class ScheduleExpression(ABC):
    """
    Represents a schedule expression for AWS Lambda event triggers.

    This is a base class that should be extended by specific scheduling types,
    such as `Rate` and `Cron`.
    """

    @abstractmethod
    def __str__(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def rule_key(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def rule_name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def permission_key(self):
        raise NotImplementedError


class Rate(ScheduleExpression):
    """
    Represents a rate-based schedule expression for AWS Lambda event triggers.

    This allows defining recurring execution intervals using minutes, hours, or days.
    """

    MINUTES: Annotated[str, Doc("Unit representing minutes for rate-based scheduling.")] = "MINUTES"
    HOURS: Annotated[str, Doc("Unit representing hours for rate-based scheduling.")] = "HOURS"
    DAYS: Annotated[str, Doc("Unit representing days for rate-based scheduling.")] = "DAYS"

    def __init__(
        self,
        value: Annotated[
            int,
            Doc(
                """
                The numeric value representing the rate interval.

                Must be a positive integer. If `1` is provided, the unit
                will be singular (e.g., "1 minute" instead of "1 minutes").
                """
            ),
        ],
        unit: Annotated[
            Literal["MINUTES", "HOURS", "DAYS"],
            Doc(
                """
                The unit of time for the rate expression.

                Accepted values:
                - `"MINUTES"`: Defines the interval in minutes.
                - `"HOURS"`: Defines the interval in hours.
                - `"DAYS"`: Defines the interval in days.
                """
            ),
        ],
        name: Annotated[
            str | None,
            Doc(
                """
                The name of the rule that will be used in the CloudFormation template.

                This is a unique identifier for the rate rule.
                """
            ),
        ] = None,
    ) -> None:
        self.value = value
        self.unit = unit
        self.name = name

    def __str__(self):
        """
        Returns the AWS-compatible rate expression string.

        Example:
        - `Rate(5, "MINUTES")` -> `"rate(5 minutes)"`
        - `Rate(1, "HOURS")` -> `"rate(1 hour)"` (singular form)
        """
        unit = self.unit.lower()
        if self.value == 1:
            # Remove the 's' from the unit
            unit = unit[:-1]
        return f"rate({self.value} {unit})"

    @property
    def rule_key(self):
        """
        The key of the rule that will be used in the CloudFormation template.

        This is a unique identifier for the rate rule.
        """

        return self.name or f"RuleRate{self.value}{self.unit}"

    @property
    def rule_name(self):
        """
        The name of the rule that will be used in the CloudFormation template.

        This is a unique identifier for the rate rule.
        """

        return self.name or f"RuleRate{self.value}{self.unit}"

    @property
    def permission_key(self):
        """
        Permission key for the CloudFormation template.

        This permission allows the CloudWatch Events rule to invoke the Lambda function.
        """
        return f"{self.rule_key}Permission"


class Cron(ScheduleExpression):
    """
    Represents a cron-based schedule expression for AWS Lambda event triggers.

    This allows defining precise execution schedules based on cron syntax.
    """

    def __init__(
        self,
        minutes: Annotated[
            str | int, Doc("Specifies the minute(s) at which the function should run (0-59, `*`, or cron expressions).")
        ],
        hours: Annotated[
            str | int, Doc("Specifies the hour(s) at which the function should run (0-23, `*`, or cron expressions).")
        ],
        day_of_month: Annotated[
            str | int,
            Doc("Specifies the day of the month when the function should run (1-31, `*`, or cron expressions)."),
        ],
        month: Annotated[
            str | int, Doc("Specifies the month when the function should run (1-12, `*`, or cron expressions).")
        ],
        day_of_week: Annotated[
            str | int,
            Doc(
                "Specifies the day of the week when the function should run (0-6, `SUN-SAT`, `*`, or cron expressions)."
            ),
        ],
        year: Annotated[
            str | int,
            Doc("Specifies the year when the function should run (`*` for any year or specific year values)."),
        ],
        name: Annotated[
            str | None,
            Doc(
                """
                The name of the rule that will be used in the CloudFormation template.

                This is a unique identifier for the rate rule.
                """
            ),
        ] = None,
    ):
        self.minutes = minutes
        self.hours = hours
        self.day_of_month = day_of_month
        self.month = month
        self.day_of_week = day_of_week
        self.year = year
        self.name = name

    def __str__(self):
        """
        Returns the AWS-compatible cron expression string.

        Example:
        - `Cron(0, 12, "*", "*", "?", "*")` -> `"cron(0 12 * * ? *)"`
        """
        return f"cron({self.minutes} {self.hours} {self.day_of_month} {self.month} {self.day_of_week} {self.year})"

    @property
    def rule_key(self):
        """
        The key of the rule that will be used in the CloudFormation template.

        This is a unique identifier for the cron rule.
        """

        cron_attrs = ["minutes", "hours", "day_of_month", "month", "day_of_week", "year"]
        result = "Rule" + "".join(
            str(getattr(self, attr)) if getattr(self, attr) == "*" else "all" for attr in cron_attrs
        )
        return self.name or result

    @property
    def rule_name(self):
        """
        The name of the rule that will be used in the CloudFormation template.

        This is a unique identifier for the cron rule.
        """

        return self.name or self.rule_key

    @property
    def permission_key(self):
        """
        Permission key for the CloudFormation template.

        This permission allows the CloudWatch Events rule to invoke the Lambda function.
        """
        return f"{self.rule_key}Permission"


class Schedule(Operation):
    def __init__(self, handler: Callable, expressions: list[ScheduleExpression]):
        super().__init__(handler=handler, middlewares=[RequestParsingMiddleware()])
        self.expressions = expressions

        self.dependant = get_dependant(
            path="/",
            call=self.handler,
        )


class Scheduler(OperationManager[Schedule]):
    def __init__(self):
        super().__init__(middlewares=[])

    def create_schedule(self, handler: Callable, expressions: list[ScheduleExpression]):
        return Schedule(handler, expressions)

    def schedule(self, expressions: list[ScheduleExpression]):
        def decorator(handler: HandlerType):
            schedule = self.create_schedule(handler=handler, expressions=expressions)
            self.operations.append(schedule)
            return schedule

        return decorator
