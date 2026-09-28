"""进程正则白名单过滤"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence

from heartbeat.protocol.models import ProcessInfo

DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    r".* Helper.*",
    r".*Helper$",
    r".* Renderer.*",
    r".*Worker.*",
    r".*Service.*",
    r".*Daemon$",
    r".*Server$",
    r".*Handler$",
    r".*Compiler$",
    r".*Agent.*",
    r".*XPC.*",
    r".*Plugin.*",
    r".*Extension.*",
    r".*Launcher$",
    r".*Monitor$",
    r".*Ingestor$",
    r".*Intents$",
    r"crashpad_handler",
    r".*com\.apple\..*",
    r"kernel_task",
    r"launchd",
    r"loginwindow",
    r"WindowServer",
    r"distnoted",
    r"cfprefsd",
    r"opendirectoryd",
    r"secd",
    r"sharingd",
    r"trustd",
    r"nsurlsessiond",
    r"nsurlstoraged",
    r"hidd",
    r"bluetoothd",
    r"coreaudiod",
    r"powerd",
    r"syslogd",
    r"UserEventAgent",
    r"fseventsd",
    r"mds_stores",
    r"mdworker.*",
    r"spotlight.*",
    r"TimeMachine.*",
    r"backupd.*",
)

_USER_APP_EXE_HINTS: tuple[str, ...] = (
    "/Applications/",
    ".app/Contents/MacOS/",
    "\\AppData\\Local\\",
    "C:\\Program Files",
    "/opt/homebrew/",
    "/usr/local/",
)

_SYSTEM_PATH_HINTS: tuple[str, ...] = (
    "/System/",
    "/usr/libexec/",
    "/usr/sbin/",
    "/usr/bin/",
    "/Library/Apple/",
    "/private/",
    "/sbin/",
    "\\Windows\\System32\\",
    "\\Windows\\SysWOW64\\",
    "\\Windows\\WinSxS\\",
    "C:\\Windows\\",
    "\\Program Files\\Windows Defender\\",
    "\\Program Files\\Microsoft\\",
    "\\Program Files (x86)\\Microsoft\\",
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
    """进程匹配器，支持白名单或采集全部可见应用"""

    def __init__(
        self,
        patterns: Sequence[str] = (),
        exclude: Sequence[str] | None = None,
        collect_all: bool = False,
    ) -> None:
        self._allow = tuple(re.compile(pattern) for pattern in patterns)
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS if exclude is None else exclude
        self._exclude = tuple(re.compile(pattern) for pattern in exclude_patterns)
        self._collect_all = collect_all

    @property
    def enabled(self) -> bool:
        """白名单非空或 collect_all 时采集"""
        return bool(self._allow) or self._collect_all

    def matches(self, name: str, exe: str | None, cmdline0: str | None) -> bool:
        """命中排除表则拒绝；白名单非空时只认白名单，否则 collect_all 收可见应用"""
        candidates = candidate_names(name, exe, cmdline0)
        if any(pattern.fullmatch(item) for item in candidates for pattern in self._exclude):
            return False
        if self._allow:
            return any(pattern.fullmatch(item) for item in candidates for pattern in self._allow)
        return self._collect_all and self._looks_like_user_app(name, exe, cmdline0)

    def _looks_like_user_app(self, name: str, exe: str | None, cmdline0: str | None) -> bool:
        paths = [item for item in (exe, cmdline0) if item]
        if any(path.startswith(prefix) or prefix in path for path in paths for prefix in _SYSTEM_PATH_HINTS):
            return False
        blob = " ".join(part for part in (name, exe, cmdline0) if part)
        if any(hint in blob for hint in _USER_APP_EXE_HINTS):
            return True
        if paths:
            return False
        clean = name.strip()
        return bool(clean) and len(clean) <= 64 and clean[:1].isupper() and not clean.islower()
