"""进程正则白名单过滤"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence

from heartbeat.protocol.models import ProcessInfo

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    r".* Helper",
    r".* Renderer",
    r"crashpad_handler",
)


def candidate_names(name: str, exe: str | None, cmdline0: str | None) -> tuple[str, ...]:
    """三路候选进程名，name、basename(exe)、basename(cmdline0)"""
    values = [name]
    if exe:
        values.append(os.path.basename(exe))
    if cmdline0:
        values.append(os.path.basename(cmdline0))
    return tuple(dict.fromkeys(values))


def aggregate_key(name: str, exe: str | None, cmdline0: str | None) -> str:
    """去重聚合键，优先 basename(exe)"""
    if exe:
        return os.path.basename(exe)
    return name


def aggregate(names: Iterable[str]) -> list[ProcessInfo]:
    """按名称聚合计数并按名称排序"""
    counter: dict[str, int] = {}
    for name in names:
        counter[name] = counter.get(name, 0) + 1
    return [ProcessInfo(name=key, count=counter[key]) for key in sorted(counter)]


class ProcessFilter:
    """进程白名单匹配器，空名单不采集"""

    def __init__(
        self,
        patterns: Sequence[str] = (),
        exclude: Sequence[str] | None = None,
    ) -> None:
        self._allow = tuple(re.compile(pattern) for pattern in patterns)
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS if exclude is None else exclude
        self._exclude = tuple(re.compile(pattern) for pattern in exclude_patterns)

    @property
    def enabled(self) -> bool:
        """白名单非空时才采集"""
        return bool(self._allow)

    def matches(self, name: str, exe: str | None, cmdline0: str | None) -> bool:
        """三路 fullmatch 命中白名单且未命中排除表"""
        candidates = candidate_names(name, exe, cmdline0)
        if any(pattern.fullmatch(item) for item in candidates for pattern in self._exclude):
            return False
        return any(pattern.fullmatch(item) for item in candidates for pattern in self._allow)
