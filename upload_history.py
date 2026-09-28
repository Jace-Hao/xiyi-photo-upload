# -*- coding: utf-8 -*-
"""
upload_history.py — 历史上传记录比对模块
==========================================
职责：
  扫描 输出结果/执行结果_*.csv 历史文件，提取「成功」过的条码集合，
  供导入清单时直接标记「已上传」，无需再次过系统对比。

设计要点：
  · 只认状态列 = 成功 的记录（失败/跳过不算）；
  · CSV 前 4 行是 # 开头的注释行，真正表头为：序号/条码/文件夹位置/文件数/结果/耗时(秒)/备注；
  · 条码按文本处理并 strip，避免前导零丢失；空行跳过；
  · 任意一个文件解析失败不影响其余文件（容错）。
"""
import csv
import glob
import os


def load_uploaded_barcodes(result_dir):
    """扫描结果目录下所有 执行结果_*.csv，返回按成功条码集合。

    返回 (barcodes:set[str], files:int)
    """
    barcodes = set()
    files = 0
    if not result_dir or not os.path.isdir(result_dir):
        return barcodes, files
    for path in sorted(glob.glob(os.path.join(result_dir, "执行结果_*.csv"))):
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
        except Exception:
            continue
        files += 1
        for row in rows:
            if not row or len(row) < 5:
                continue
            if row[0].startswith("#"):
                continue
            barcode = (row[1] or "").strip()
            status = (row[4] or "").strip()
            if barcode and status == "成功":
                barcodes.add(barcode)
    return barcodes, files


def match_tasks(tasks, barcodes):
    """把任务列表中命中历史成功条码的任务标记为 已上传。

    返回命中数量。不覆盖已有执行状态（成功/失败/跳过/进行中保持原样）。
    """
    n = 0
    for t in tasks:
        if t.status != "待执行":
            continue
        if (t.barcode or "").strip() in barcodes:
            t.status = "已上传"
            t.note = "历史已上传（本次不再执行）"
            n += 1
    return n