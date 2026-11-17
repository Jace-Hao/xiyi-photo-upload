# -*- coding: utf-8 -*-
"""清单导入校验回归：空条码 / 空路径必须标「跳过」且报告计数正确。"""
import os

from csv_import import import_list, ParseReport, TaskRecord


def _write(path, text, encoding="utf-8"):
    with open(path, "wb") as f:
        f.write(text.encode(encoding))
    return str(path)


def test_empty_barcode_and_empty_path_are_skipped(tmp_path):
    path = _write(os.path.join(tmp_path, "清单.csv"),
                  "条码,文件位置\n"
                  "110000044416,E:\\photos\\110000044416\n"
                  ",E:\\photos\\no_barcode\n"          # 空条码
                  "110000044418,\n"                     # 空路径
                  "110000044419,E:\\photos\\110000044419\n")

    tasks, report = import_list(path, check_folder=False)

    assert isinstance(report, ParseReport)
    assert len(tasks) == 4
    assert report.total_rows == 4
    assert report.header_used is True
    assert tasks[0].status == "待执行" and tasks[0].barcode == "110000044416"
    assert tasks[1].status == "跳过" and tasks[1].note == "条码为空"
    assert tasks[2].status == "跳过" and tasks[2].note == "文件夹位置为空"
    assert tasks[3].status == "待执行"
    assert report.valid_rows == 2, "只有 2 行条码与路径都有效"
    assert len(report.issues) == 2


def test_all_invalid_rows_report_zero_valid(tmp_path):
    path = _write(os.path.join(tmp_path, "清单.csv"),
                  "条码,文件位置\n"
                  ",E:\\photos\\a\n"
                  "B002,\n")
    tasks, report = import_list(path, check_folder=False)
    assert len(tasks) == 2
    assert all(t.status == "跳过" for t in tasks)
    assert report.valid_rows == 0
    assert report.total_rows == 2


def test_gbk_encoding_and_no_header(tmp_path):
    """GBK 编码与无表头两列格式仍可解析，短行自动补空。"""
    path = _write(os.path.join(tmp_path, "清单.csv"),
                  "110000044416,E:\\照片\\一\n"
                  "110000044417\n", encoding="gbk")     # 第二行缺路径列
    tasks, report = import_list(path, check_folder=False)
    assert report.encoding in ("gbk", "gb18030", "utf-8-sig")
    assert report.header_used is False
    assert tasks[0].status == "待执行"
    assert tasks[1].status == "跳过"
    assert tasks[1].note == "文件夹位置为空"


def test_task_record_defaults_and_display_files():
    t = TaskRecord(index=1, barcode="B001", folder="p")
    assert t.status == "待执行" and t.duration == 0.0
    assert t.display_files == "-"
    t.folder_exists = True
    t.file_count = 3
    assert t.display_files == "3"
