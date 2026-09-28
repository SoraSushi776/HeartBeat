"""进程过滤与聚合测试"""

from heartbeat.adapters.processes.filter import (
    ProcessFilter,
    aggregate,
    aggregate_key,
    candidate_names,
)


def test_candidate_names_covers_three_routes() -> None:
    names = candidate_names("Code", "/usr/bin/Code", "/usr/local/bin/code")
    assert names == ("Code", "code")


def test_candidate_names_dedupes() -> None:
    names = candidate_names("Code", "/usr/bin/Code", "/usr/bin/Code")
    assert names == ("Code",)


def test_aggregate_key_prefers_exe_basename() -> None:
    assert aggregate_key("python3", "/usr/local/bin/python3.10", None) == "python3.10"
    assert aggregate_key("python3", None, None) == "python3"


def test_aggregate_counts_and_sorts() -> None:
    result = aggregate(["Safari", "Code", "Safari"])
    assert [(item.name, item.count) for item in result] == [("Code", 1), ("Safari", 2)]


def test_empty_whitelist_disables_collection() -> None:
    assert not ProcessFilter().enabled
    assert ProcessFilter(["Safari"]).enabled


def test_fullmatch_whitelist() -> None:
    process_filter = ProcessFilter([r"Safari", r"Music"])
    assert process_filter.matches("Safari", None, None)
    assert process_filter.matches("Music", "/Applications/Music.app/Contents/MacOS/Music", None)
    assert not process_filter.matches("SafariTab", None, None)


def test_helper_excluded_by_default() -> None:
    process_filter = ProcessFilter([r".*"])
    assert process_filter.matches("Safari", None, None)
    assert not process_filter.matches("Safari Helper", None, None)
    assert not process_filter.matches("Safari Renderer", None, None)
    assert not process_filter.matches("crashpad_handler", None, None)


def test_custom_exclude_overrides_default() -> None:
    process_filter = ProcessFilter([r".*Helper"], exclude=())
    assert process_filter.matches("Safari Helper", None, None)
