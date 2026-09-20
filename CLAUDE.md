# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

MMleo 是基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的《偶像梦幻祭2》自动化助手（MaaFramework 的 "Agent 项目"）。

- 外部 GUI（MFAAvalonia，C#）加载 `assets/interface.json`，连接控制器（Adb / Win32），再按 `agent.child_exec/child_args` 拉起 `python agent/main.py <socket_id>` 作为 **AgentServer**。
- 本仓库不含 GUI，只有 Python Agent + 任务/资源定义。**没有可直接 `python xxx.py` 运行的"主程序"**，Agent 由 GUI 以 AgentServer 协议经 socket 驱动。
- 依赖见 `requirements.txt`：`maafw==5.6.0`（**v5 破坏性变更见下**）、loguru、pillow、pytz。

## 常用命令

- 校验 pipeline 能否被 MaaFramework 加载：`python check_resource.py assets/resource/base`
- 格式化 / 静态检查：`pre-commit run --all-files`（oxipng 压图、prettier 格式化 json/yaml、markdownlint 查 docs）
- 装依赖：`pip install -r requirements.txt`（虚拟环境在 `.venv/`；`agent/main.py` 启动时也会自动补装缺失依赖）
- 打包发布：`.github/workflows/install.yml`（下载 MaaFramework v5.6.0 + MFAAvalonia、搭嵌入式 Python、PyInstaller）；本地打包入口见 `launcher/MMleo.py` 头部注释
- 无单元测试，`check_resource.py` 是最接近的校验手段

## 架构（需跨文件才能看懂）

### 自定义动作/识别的注册与调用

1. `assets/interface.json` 的 `task[].entry` 指向 pipeline 节点；节点里 `action: "Custom"` + `custom_action: "Xxx"`（或 `recognition: "Custom"` + `custom_recognition: "Xxx"`）即触发 Python 侧对应类。
2. 注册靠 **import 副作用**：`agent/main.py` 里 `import custom` → `custom/__init__.py` → `action/__init__.py` / `reco/__init__.py` 用 `from .X import *` 导入各模块，模块内 `@AgentServer.custom_action("Xxx")` / `@AgentServer.custom_recognition("Xxx")` 装饰器完成注册。
   - **只有被 `__init__.py` import 的才生效**。当前已注册：动作 `TargetAreaSearchAndSave`、`MusicPlayer`、`CompositeGamePlayer`、`CompositeGamePlayer_mini`、`CountTask`、`TourConcert`、`DailyTask`；识别 `SearchMusic`。
   - `tour_concert_new.py`、`consert.py` 未被 import，属草稿/占位，别当活跃代码改（`TourConcert` 生效的是 `tour_concert.py`）。
3. 自定义动作签名 `run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult`，返回 `CustomAction.RunResult(success=bool)`；节点参数经 `argv.custom_action_param`（JSON 字符串，来自 interface.json 的 `custom_action_param`）传入。识别为 `analyze(self, context, argv)`。
4. Agent 内驱动入口：`context.run_task(entry)`、`context.run_recognition(entry, image)`、`context.tasker.controller.post_screencap()/.post_click(x,y)/.post_key()` 等。

### 目录职责

- `agent/` — Python Agent（活跃代码）：`main.py` 入口，`custom/action/`、`custom/reco/` 自定义动作/识别，`utils/logger.py`。
- `assets/` — 资源：`interface.json`（任务清单/控制器/资源路径/option/pipeline_override）、`resource/base/`（`pipeline/*.json` 及带注释的 `*.jsonc`、`image/` 模板、`model/ocr/`）、`resource/bside/`（B 服增量覆盖）。
- `tools/ci/` — 打包/CI 脚本；`tools/migrate_pipeline_v5.py` — 官方 v4→v5 迁移脚本（留存备用）。
- `legacy/` — 废弃文件；`launcher/MMleo.py` — 仅一行启动 GUI。

## ⚠️ maafw v5 破坏性变更（本仓库已适配，改代码务必遵守）

- `RecognitionDetail.filtered_results`（v4 的 `filterd_results` 是拼写错误，**已删**）。
- `run_recognition` 只要尝试识别就返回 `RecognitionDetail`，**未命中不再返回 None**，必须用 `.hit` 判断；仅 entry 不存在 / node disabled / 传入 image 为空时才返回 None。参考 `music_player.py` 的 `_reco_hit` 助手。
- Pipeline JSON 的 `interrupt` 字段**已移除**，改为把节点写进 `next` 并加 `[JumpBack]` 前缀（见 `StartUp.json` 的 `"[JumpBack]BackMainInMenu"`）。
- `run_action` 返回 `ActionDetail`（`.success`），`run_recognition` 返回 `RecognitionDetail`（`.hit`）。

## 代码规范

- Python：4 空格缩进、UTF-8、中文注释/日志；日志用 `from utils import logger`（loguru），**不要用 print**。
- Pipeline JSON 需要注释时用 `.jsonc` 后缀，别往 `.json` 塞注释（`//` 只在 .jsonc 合法）。
- 格式化由 prettier + markdownlint 管理（`.prettierrc`、`.pre-commit-config.yaml`）：JSON 用 tab 缩进、`bracketSameLine: false`、数组多元素自动换行（`multiline-arrays` 插件，所以 pipeline 里 `next`/`roi` 是多行数组）；YAML 2 空格；printWidth 120。

## gitignore（这些目录/文件不参与版本控制）

- 构建/下载产物：`build/`、`install/`、`config/`、`debug/`、`deps/`；编译产物 `*.exe` `*.dll` `*.so` `*.dylib` `*.msp`。
- Python 字节码 `__pycache__/`、`*.pyc`；前端 `node_modules/`；IDE `.idea/`、`.vscode/*`（settings/extensions 除外）；`tools/ImageCropper/**/*.png`。
- 注意：`local/` **未**被 gitignore（`.gitignore` 里只有 `.local/*`），`local/temp/*.json` 是已提交的运行时状态（自定义动作读写，如 `Easy.json`）；`.venv/` 靠 venv 自带的 `.gitignore` 忽略。
- 因此改代码只动 `agent/`、`assets/`、`tools/`、`launcher/`；不要改或提交这些产物目录。
- 已知坑：`.gitignore` 末尾 `debug.github/` 一行编码损坏（含 NUL 字节，git 把整个文件当二进制），编辑时避开该行或整体重写。
