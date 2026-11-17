# -*- coding: utf-8 -*-
"""三态结果映射 / 统计累计回归（唯一实现位于 result_state.py）。"""
from result_state import (
    RESULT_OK, RESULT_SKIP, RESULT_FAIL,
    STATUS_OK, STATUS_SKIP, STATUS_FAIL, STATUS_DRY,
    KIND_TO_STATUS, new_run_stats, status_for, accumulate_stats,
)


def test_kind_constants_and_map_are_consistent():
    assert (RESULT_OK, RESULT_SKIP, RESULT_FAIL) == ("ok", "skip", "fail")
    assert KIND_TO_STATUS == {
        RESULT_OK: STATUS_OK,
        RESULT_SKIP: STATUS_SKIP,
        RESULT_FAIL: STATUS_FAIL,
    }
    assert (STATUS_OK, STATUS_SKIP, STATUS_FAIL, STATUS_DRY) == (
        "成功", "跳过", "失败", "演练")


def test_status_for_three_states():
    """ok→成功 / skip→跳过 / fail→失败，且未知 kind 安全降级为失败。"""
    assert status_for(RESULT_OK) == "成功"
    assert status_for(RESULT_SKIP) == "跳过"
    assert status_for(RESULT_FAIL) == "失败"
    assert status_for("unknown") == "失败"


def test_status_for_dry_always_dry():
    """演练批次无论 kind 一律写「演练」，绝不落入「成功」。"""
    for kind in (RESULT_OK, RESULT_SKIP, RESULT_FAIL):
        assert status_for(kind, dry=True) == "演练"
    assert status_for(RESULT_OK, dry=True) != "成功"


def test_accumulate_stats_counts_skip_and_dry():
    """「跳过」不再被记为成功：stats['skip'] 非 0，演练单独计数。"""
    stats = new_run_stats(total=4)
    assert stats == {"total": 4, "ok": 0, "fail": 0, "skip": 0, "dry": 0}

    accumulate_stats(stats, RESULT_OK)
    accumulate_stats(stats, RESULT_SKIP)
    accumulate_stats(stats, RESULT_SKIP, dry=True)
    accumulate_stats(stats, RESULT_FAIL, dry=True)

    assert stats["ok"] == 1
    assert stats["skip"] == 2 and stats["skip"] != 0
    assert stats["fail"] == 1
    assert stats["dry"] == 2
    assert stats["total"] == 4, "total 应始终保持本次执行快照长度"


def test_accumulate_stats_returns_same_dict_and_tolerates_missing_dry():
    stats = {"total": 0, "ok": 0, "fail": 0, "skip": 0}
    ret = accumulate_stats(stats, RESULT_SKIP, dry=True)
    assert ret is stats
    assert stats["dry"] == 1
    assert stats["skip"] == 1


def test_dry_batch_produces_no_success():
    """模拟整批演练：全部 kind=skip + dry，成功数必须为 0。"""
    stats = new_run_stats(total=3)
    for _ in range(3):
        assert status_for(RESULT_SKIP, dry=True) == "演练"
        accumulate_stats(stats, RESULT_SKIP, dry=True)
    assert stats["ok"] == 0
    assert stats["dry"] == 3
    assert stats["skip"] == 3
