# -*- coding: utf-8 -*-
"""调试端口 target 归属白名单回归。

覆盖 ROI-4 的 P0：任意 Chromium / CEF 占用 9222 时曾因只看 type=="page"
而被误判成「洗衣管家已就绪」，导致精准模式连错应用。
"""
from result_state import (
    is_app_target, has_app_target,
    APP_TITLE_KEYWORD, APP_URL_KEYWORD, CDP_TARGET_TYPE_PAGE,
)


def test_app_title_matches():
    assert CDP_TARGET_TYPE_PAGE == "page"
    assert APP_TITLE_KEYWORD == "洗衣管家"
    assert is_app_target({
        "type": "page", "title": "洗衣管家 - 拍照页", "url": "http://127.0.0.1/#/",
    }) is True


def test_xiyijst_url_matches():
    assert APP_URL_KEYWORD == "xiyijst"
    assert is_app_target({
        "type": "page", "title": "Some App",
        "url": "https://xiyijst.example.com/clothManage/photograph",
    }) is True


def test_other_chromium_pages_do_not_match():
    for target in (
        {"type": "page", "title": "Chrome 新标签页", "url": "chrome://newtab/"},
        {"type": "page", "title": "微信开发者工具", "url": "devtools://devtools/"},
        {"type": "page", "title": "", "url": ""},
        {"type": "page", "title": "无关页面", "url": "about:blank"},
        {"type": "service_worker", "title": "洗衣管家", "url": "xiyijst"},
        {"type": "iframe", "url": "https://xiyijst.example.com/"},
        {"title": "洗衣管家", "url": "xiyijst"},   # 缺 type
    ):
        assert is_app_target(target) is False, target


def test_empty_and_malformed_data_is_safe():
    for target in (None, {}, [], "", 0, {"type": None, "title": None, "url": None}):
        assert is_app_target(target) is False, target
    for data in (None, [], (), {}, "", 123):
        assert has_app_target(data) is False, data


def test_has_app_target_needs_at_least_one_match():
    assert has_app_target([
        {"type": "page", "title": "Chrome", "url": "chrome://newtab/"},
        {"type": "page", "title": "洗衣管家", "url": "http://127.0.0.1/#/"},
    ]) is True
    assert has_app_target([
        {"type": "page", "title": "Chrome", "url": "chrome://newtab/"},
        {"type": "page", "title": "", "url": "about:blank"},
    ]) is False
