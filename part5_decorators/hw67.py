import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
INVALID_TRIGGERS_ERR = "triggers_on must be Exception type or tuple of them!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime.datetime):
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


def _is_exception_class(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, Exception)


def _validate_breaker_args(count: int, recovery: int, triggers: Any) -> None:
    errors: list[Exception] = []

    if not isinstance(count, int) or count <= 0:
        errors.append(ValueError(INVALID_CRITICAL_COUNT))
    if not isinstance(recovery, int) or recovery <= 0:
        errors.append(ValueError(INVALID_RECOVERY_TIME))

    is_valid = _is_exception_class(triggers)
    if isinstance(triggers, tuple):
        is_valid = all(_is_exception_class(trg) for trg in triggers)

    if not is_valid:
        errors.append(TypeError(INVALID_TRIGGERS_ERR))

    if errors:
        raise ExceptionGroup(VALIDATIONS_FAILED, errors)


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] | tuple[type[Exception], ...] = Exception,
    ):
        _validate_breaker_args(critical_count, time_to_recover, triggers_on)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self.fail_count = 0
        self.block_time: datetime.datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check_block(func)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as err:
                self._handle_failure(func, err)
                raise
            else:
                self.fail_count = 0
                self.block_time = None
                return result

        return wrapper

    def _handle_failure(
        self,
        func: CallableWithMeta[Any, Any],
        err: Exception,
    ) -> None:
        self.fail_count += 1
        if self.fail_count >= self.critical_count:
            self.block_time = datetime.datetime.now(datetime.UTC)
            raise BreakerError(
                func_name=f"{func.__module__}.{func.__name__}",
                block_time=self.block_time,
            ) from err

    def _check_block(self, func: CallableWithMeta[Any, Any]) -> None:
        if not self.block_time:
            return
        recovery_delta = datetime.timedelta(seconds=self.time_to_recover)
        now = datetime.datetime.now(datetime.UTC)
        if now < self.block_time + recovery_delta:
            raise BreakerError(
                func_name=f"{func.__module__}.{func.__name__}",
                block_time=self.block_time,
            )


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    get_comments(1)
