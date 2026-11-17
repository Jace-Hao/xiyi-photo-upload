# -*- coding: utf-8 -*-
"""历史去重回归：只认「成功」，排除演练状态与 [演练] 备注。

覆盖 ROI-1 的 P0：演练结果曾以「成功」写入 执行结果_*.csv，导致该条码
在后续导入时被永久标记「已上传」而漏传。
"""
import csv
import os

from upload_history import load_uploaded_barcodes, match_tasks
from csv_import import TaskRecord


HEADER = ["序号", "条码", "文件夹位置", "文件数", "结果", "耗时(秒)", "备注"]


def _write_result(path, rows):
    """按真实导出格式写一份结果 CSV：3 行 # 注释 + 1 行表头 + 数据行。"""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# 洗衣管家 · 照片批量上传助手 v1.12 执行结果"])
        w.writerow(["# 导出时间：2024-01-01 00:00:00"])
        w.writerow(["# 合计：若干条，成功 0，失败 0，跳过 0，演练 0"])
        w.writerow(HEADER)
        for row in rows:
            w.writerow(row)
    return path


def test_only_success_is_loaded_and_dry_is_excluded(tmp_path):
    """成功被识别；跳过/失败/已上传/演练/备注含 [演练] 的成功行都不识别。"""
    _write_result(os.path.join(tmp_path, "执行结果_20240101_000000.csv"), [
        [1, "B001", "p1", 3, "成功", "1.0", "完成"],
        [2, "B002", "p2", 3, "跳过", "1.0", "订单已有照片"],
        [3, "B003", "p3", 3, "失败", "1.0", "异常"],
        [4, "B004", "p4", 3, "已上传", "-", "历史已上传（本次不再执行）"],
        [5, "B005", "p5", 3, "演练", "0.0", "[演练] 检查：本地 3 张图片"],
        # 二次保险：即便状态被写成「成功」，备注含 [演练] 也必须排除。
        [6, "B006", "p6", 3, "成功", "0.0", "[演练] 检查：本地 3 张图片"],
        [7, "B007", "p7", 3, "成功", "1.0", "完成 2"],
    ])
    barcodes, files = load_uploaded_barcodes(str(tmp_path))
    assert barcodes == {"B001", "B007"}
    assert files == 1


def test_dry_result_file_is_not_scanned(tmp_path):
    """演练批次自动导出的 演练结果_*.csv 不参与历史比对。"""
    _write_result(os.path.join(tmp_path, "执行结果_20240101_000000.csv"), [
        [1, "B001", "p1", 3, "成功", "1.0", "完成"],
    ])
    _write_result(os.path.join(tmp_path, "演练结果_20240101_000001.csv"), [
        [1, "B999", "p9", 3, "成功", "0.0", "不该被识别"],
        [2, "B998", "p8", 3, "演练", "0.0", "[演练] 检查"],
    ])
    barcodes, files = load_uploaded_barcodes(str(tmp_path))
    assert barcodes == {"B001"}
    assert files == 1, "只应扫描到 1 份 执行结果_*.csv"


def test_comment_short_and_header_rows_are_tolerated(tmp_path):
    """注释行、表头行、短行、空行、条码前导零都不应造成误判或异常。"""
    path = os.path.join(tmp_path, "执行结果_20240102_000000.csv")
    _write_result(path, [
        [1, "0000123", "p1", 1, "成功", "1.0", "完成"],
        [2, "B_SHORT"],                       # 短行（列数 < 5）容错
        [],                                   # 空行容错
        ["# 注释样式的伪数据", "B_COMMENT", "p", 1, "成功", "1.0", ""],
    ])
    barcodes, files = load_uploaded_barcodes(str(tmp_path))
    assert "0000123" in barcodes, "条码须按文本处理，前导零不能丢"
    assert "B_SHORT" not in barcodes
    assert "B_COMMENT" not in barcodes, "以 # 开头的行必须跳过"
    assert files == 1


def test_invalid_dir_returns_empty(tmp_path):
    barcodes, files = load_uploaded_barcodes(str(tmp_path / "not_exist"))
    assert barcodes == set() and files == 0


def test_match_tasks_only_touches_pending(tmp_path):
    """命中历史成功条码只改「待执行」状态，不覆盖既有执行结果。"""
    tasks = [
        TaskRecord(index=1, barcode="B001", status="待执行"),
        TaskRecord(index=2, barcode="B002", status="失败"),
        TaskRecord(index=3, barcode="B003", status="待执行"),
    ]
    n = match_tasks(tasks, {"B001", "B002"})
    assert n == 1
    assert tasks[0].status == "已上传"
    assert tasks[1].status == "失败"
    assert tasks[2].status == "待执行"
