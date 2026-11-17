# -*- coding: utf-8 -*-
"""
result_state.py — 可独立导入的纯函数集合（零第三方依赖）
================================================================
本模块刻意不 import tkinter / pyautogui / win32* / websocket / requests，
也不读取配置文件、不联网、不访问系统 API，因此可在纯净环境里被 pytest
直接导入，用于回归验证以下两类核心判定：

  1. CDP 调试端口 target 归属判定（is_app_target / has_app_target）：
     避免任意 Chromium / CEF 占用调试端口时被误判成「洗衣管家已就绪」。
  2. 单条执行结果三态 → 界面状态映射与统计累计
     （RESULT_OK / RESULT_SKIP / RESULT_FAIL / STATUS_DRY / status_for /
     accumulate_stats / new_run_stats）：automation.py 与 run_batch 的唯一实现。

历史 bug：run_one 曾只返回 bool，「订单已有照片跳过」「疑似未传完」也被
记为成功并写入历史去重集合，造成永久漏传；演练批次也曾被记成「成功」。
三态 + 演练独立状态在这里集中定义，避免多处各写一份、口径漂移。

CDP 归属判定关键字与 cdp_control.connect 的页面匹配条件保持一致：
    type == "page" 且 (title 含「洗衣管家」 或 url 含 xiyijst)
"""

# ----------------------------------------------------------------------------
# 一、CDP 调试端口 target 归属白名单
# ----------------------------------------------------------------------------
# 归属白名单关键字（与 cdp_control.connect 的匹配条件一致）
APP_TITLE_KEYWORD = "洗衣管家"
APP_URL_KEYWORD = "xiyijst"

# CDP /json 目标类型
CDP_TARGET_TYPE_PAGE = "page"


def is_app_target(target):
    """判断单个 CDP target 是否属于洗衣管家主页面。

    Args:
        target: /json 返回列表里的一项，通常是 dict；也可能是 None 或非 dict。

    Returns:
        bool —— 仅当 type == "page" 且标题含「洗衣管家」或 url 含 xiyijst
        时为 True。其他 Chromium / CEF 页面、devtools 页、空数据一律 False。
    """
    if not isinstance(target, dict):
        return False
    if target.get("type") != CDP_TARGET_TYPE_PAGE:
        return False
    title = target.get("title") or ""
    url = target.get("url") or ""
    return (APP_TITLE_KEYWORD in title) or (APP_URL_KEYWORD in url)


def has_app_target(data):
    """判断 /json 返回的 target 列表里是否存在本应用页面。

    Args:
        data: /json 解析结果，通常是 list[dict]；None / 非列表 / 空列表均安全。

    Returns:
        bool
    """
    if not isinstance(data, (list, tuple)):
        return False
    return any(is_app_target(t) for t in data)


# ----------------------------------------------------------------------------
# 二、单条执行结果三态与界面状态
# ----------------------------------------------------------------------------
RESULT_OK = "ok"        # 真实完成上传 → 成功
RESULT_SKIP = "skip"    # 未行动 / 已跳过 → 跳过（不计入成功、不写历史）
RESULT_FAIL = "fail"    # 执行失败 → 失败

STATUS_OK = "成功"
STATUS_SKIP = "跳过"
STATUS_FAIL = "失败"
STATUS_DRY = "演练"       # 演练批次统一状态：不参与历史去重
STATUS_UPLOADED = "已上传"  # 导入清单时命中历史成功条码的状态（upload_history 使用）
STATUS_PENDING = "待执行"

# 结果种类 → 界面状态（非演练批次）。未知 kind 一律按失败处理，保证安全。
KIND_TO_STATUS = {
    RESULT_OK: STATUS_OK,
    RESULT_SKIP: STATUS_SKIP,
    RESULT_FAIL: STATUS_FAIL,
}


def status_for(kind, dry=False):
    """把执行结果种类映射为任务状态字符串。

    Args:
        kind: RESULT_OK / RESULT_SKIP / RESULT_FAIL 之一。
        dry: 是否为演练批次；演练时无论 kind 一律返回「演练」。

    Returns:
        任务状态字符串（成功 / 跳过 / 失败 / 演练）。
    """
    if dry:
        return STATUS_DRY
    return KIND_TO_STATUS.get(kind, STATUS_FAIL)


def new_run_stats(total=0):
    """创建一次批量执行的统计字典（含演练计数）。"""
    return {"total": int(total), "ok": 0, "fail": 0, "skip": 0, "dry": 0}


def accumulate_stats(stats, kind, dry=False):
    """按执行结果种类累计统计（原地修改 stats 并返回）。

    演练批次额外计入 dry 计数；ok/fail/skip 始终按真实 kind 累计，
    不再沿用旧的 bool 语义把「跳过」误记为「成功」。

    Args:
        stats: 统计字典，至少含 ok/fail/skip 键；缺 dry 键时自动补 0。
        kind: RESULT_OK / RESULT_SKIP / RESULT_FAIL 之一。
        dry: 是否为演练批次。

    Returns:
        同一个 stats 字典（便于链式调用）。
    """
    stats.setdefault("ok", 0)
    stats.setdefault("fail", 0)
    stats.setdefault("skip", 0)
    stats.setdefault("dry", 0)
    if kind == RESULT_OK:
        stats["ok"] += 1
    elif kind == RESULT_SKIP:
        stats["skip"] += 1
    else:
        stats["fail"] += 1
    if dry:
        stats["dry"] += 1
    return stats
