from __future__ import annotations

import asyncio
import ctypes
import datetime
import random
import time
from random import randint
from random import sample
from string import ascii_letters, digits
from typing import Callable, Generic, Literal, TypeVar, Union, overload

from aiohttp import ClientSession
from binary_reader import BinaryReader

from .path import BasePath

dll = ctypes.CDLL(BasePath.joinpath("trove.dll").as_posix())
calculate_hash = dll.calculate_hash
calculate_hash.restype = ctypes.c_uint32
calculate_hash.argtypes = [ctypes.c_char_p, ctypes.c_size_t]


def random_id(k=8):
    return "".join(sample(ascii_letters + digits, k=k))


T = TypeVar("T", bool, Literal[True], Literal[False])


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return "..."


class ExponentialBackoff(Generic[T]):
    def __init__(self, base: int = 1, *, integral: T = False):
        self._base: int = base
        self._exp: int = 0
        self._max: int = 10
        self._reset_time: int = base * 2**11
        self._last_invocation: float = time.monotonic()
        rand = random.Random()
        rand.seed()
        self._randfunc: Callable[..., Union[int, float]] = (
            rand.randrange if integral else rand.uniform
        )

    @overload
    def delay(self: ExponentialBackoff[Literal[False]]) -> float: ...

    @overload
    def delay(self: ExponentialBackoff[Literal[True]]) -> int: ...

    @overload
    def delay(self: ExponentialBackoff[bool]) -> Union[int, float]: ...

    def delay(self) -> Union[int, float]:
        invocation = time.monotonic()
        interval = invocation - self._last_invocation
        self._last_invocation = invocation
        if interval > self._reset_time:
            self._exp = 0
        self._exp = min(self._exp + 1, self._max)
        return self._randfunc(0, self._base * 2**self._exp)


def compute_timedelta(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.astimezone()
    now = datetime.datetime.now(datetime.timezone.utc)
    return max((dt - now).total_seconds(), 0)


def throttle(actual_handler, data={}, delay=0.5):
    """Throttles a function from running using python's memory gimmicks.

    This solves a race condition for searches to the database and loading data into the UI.
    Now you see Python will use that dict object for all the functions that run this decorator.
    Which means all delay times are shared, not ideal but saves the time of setting up the variables.
    Ideally I would not rely on this Python gimmick as it might change in the future.
    If for some reason this stopped working, check if python still defines and uses same dict object upon...
    ...function definition.

    I did not get a degree, don't sue me"""

    async def wrapper(*args, **kwargs):
        """Simple filter for queries that shouldn't run."""

        data["last_change"] = datetime.datetime.now(datetime.UTC).timestamp()
        await asyncio.sleep(delay)
        if (
            datetime.datetime.now(datetime.UTC).timestamp() - data["last_change"]
            >= delay - delay * 0.1
        ):
            await actual_handler(*args, **kwargs)

    return wrapper


def long_throttle(actual_handler, data={}, delay=1.5):
    """Throttles a function from running using python's memory gimmicks.

    This solves a race condition for searches to the database and loading data into the UI.
    Now you see Python will use that dict object for all the functions that run this decorator.
    Which means all delay times are shared, not ideal but saves the time of setting up the variables.
    Ideally I would not rely on this Python gimmick as it might change in the future.
    If for some reason this stopped working, check if python still defines and uses same dict object upon...
    ...function definition.

    I did not get a degree, don't sue me"""

    async def wrapper(*args, **kwargs):
        """Simple filter for queries that shouldn't run."""

        data["last_change"] = datetime.datetime.now(datetime.UTC).timestamp()
        await asyncio.sleep(delay)
        if (
            datetime.datetime.now(datetime.UTC).timestamp() - data["last_change"]
            >= delay - delay * 0.1
        ):
            await actual_handler(*args, **kwargs)

    return wrapper


def split_boosts(n):
    a = randint(0, n)
    b = randint(0, n - a)
    c = n - a - b
    return [a, b, c]


def get_key(iterable, obj: dict):
    for z in iterable:
        try:
            for x, y in obj.items():
                if z[x] == y:
                    ...
            return z
        except KeyError:
            ...
    return None


def get_attr(iterable, **kwargs):
    for z in iterable:
        try:
            for x, y in kwargs.items():
                if getattr(z, x) != y:
                    raise ValueError
            return z
        except ValueError:
            ...
    return None


def chunks(lst, n):
    result = []
    for i in range(0, len(lst), n):
        result.append(lst[i : i + n])
    return result


async def check_update(current_version):
    async with ClientSession() as session:
        async with session.get(
            "https://api.github.com/repos/Sly0511/TroveFileExtractor/releases"
        ) as response:
            version_data = await response.json()
            version = version_data[0]
            if current_version != version.get("name"):
                return version.get("html_url")
    return None


def ReadLeb128(buffer: BinaryReader, pos):
    result = 0
    shift = 0
    while 1:
        buffer.seek(pos)
        b = buffer.read_bytes()
        for i, byte in enumerate(b):
            result |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                result &= (1 << 32) - 1
                result = int(result)
                return result
            shift += 7
            if shift >= 64:
                raise Exception("Too many bytes when decoding varint.")


def WriteLeb128(value):
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)

    return bytes(result)
