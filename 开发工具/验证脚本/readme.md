# 验证脚本（开发工具）

本目录归档「洗衣管家 · 照片批量上传助手」的关键验证脚本。

## 首选：自动化回归测试（pytest）

**每次改动状态机、历史去重、CDP 端口判定、清单导入后都应先跑这一条**：

```bat
py -3 -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

- 测试目录：项目根目录下的 `tests/`（配置见 `pytest.ini`）
- 依赖：仅 `pytest>=7.0`（见 `requirements-dev.txt`），**不需要** tkinter /
  pyautogui / pywin32 / websocket-client，不联网、不启动 GUI、不依赖 9222 端口，
  也不会实例化 `App()`。
- 被测纯函数集中在零依赖模块 `result_state.py`；`upload_history.py`、
  `csv_import.py` 本身也无第三方依赖，可直接导入。

| 用例文件 | 覆盖点 |
|---|---|
| `tests/test_upload_history.py` | 只认「成功」、排除演练状态与 `[演练]` 备注、`演练结果_*.csv` 不参与历史去重、注释/短行容错、前导零 |
| `tests/test_result_state.py` | 三态 → 状态映射（ok/skip/fail/dry）、`stats["skip"]` 非 0、`stats["dry"]` 累计、演练批次不产生成功 |
| `tests/test_cdp_target.py` | 调试端口 target 归属白名单（「洗衣管家」title / `xiyijst` url），其他 Chromium / 空数据不误判 |
| `tests/test_csv_import.py` | 空条码 / 空路径标「跳过」、`ParseReport` 计数、GBK 与无表头兼容 |

> 说明：本目录下的两个旧脚本属于**手工/半自动联网验证**，与新 pytest 回归集定位不同，
> 发版前按需单独运行即可，不作为日常改动的第一道关卡。

## 旧手工脚本（按需）

建议在改动**更新模块**或**发版后**各跑一遍：

```bat
py -3.14 test_updater_download.py
py -3.14 test_update_ui.py
```

| 脚本 | 覆盖点 | 预期结果 | 耗时 / 流量 |
|---|---|---|---|
| `test_updater_download.py` | 慢源自动切换、换源断点续传（Range）、哈希一致、校验值取回降级 | 各用例输出 `sha match: True`；T4 输出 `None` | 数分钟，约 200MB（会多次下载 56MB 安装包） |
| `test_update_ui.py` | 状态栏「国内加速」与进度显示、日志换源记录 | 状态栏为 `正在下载 v9.9（国内加速） … 42%`；日志含「已自动切换国内加速线路：gh-proxy.com」 | 约 8 秒 |

## 备注

- `test_updater_download.py` 顶部 `ASSET` / `LOCAL` 两个常量需指向一组「同一版本」的发布地址与本地对照安装包；
- 两个旧脚本都从本机 `E:\软件开发\洗衣管家上传助手` 载入代码（换机器需改路径）；**新 pytest 测试无此限制**，用相对导入、换机器直接可跑；
- 旧脚本中间文件默认写系统 `%TEMP%`；pytest 用例使用 `tmp_path` 临时目录，由框架自动清理。
