import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
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


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] | tuple[type[Exception], ...] = Exception,
    ):
        errors = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self.fail_count = 0
        self.block_time: datetime.datetime | None = None

    def _check_block(self, func: CallableWithMeta[Any, Any]) -> None:
        if not self.block_time:
            return
        recovery_delta = datetime.timedelta(seconds=self.time_to_recover)
        if datetime.datetime.now(datetime.UTC) < self.block_time + recovery_delta:
            raise BreakerError(
                func_name=f"{func.__module__}.{func.__name__}",
                block_time=self.block_time,
            )

    def _handle_error(self, func: CallableWithMeta[Any, Any], error: Exception) -> None:
        if not isinstance(error, self.triggers_on):
            raise error
        self.fail_count += 1
        if self.fail_count >= self.critical_count:
            self.block_time = datetime.datetime.now(datetime.UTC)
            raise BreakerError(
                func_name=f"{func.__module__}.{func.__name__}",
                block_time=self.block_time,
            ) from error
        raise error

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check_block(func)
            try:
                result = func(*args, **kwargs)
            except Exception as error:
                self._handle_error(func, error)
                raise
            else:
                self.fail_count = 0
                self.block_time = None
                return result

        return wrapper


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    get_comments(1)
