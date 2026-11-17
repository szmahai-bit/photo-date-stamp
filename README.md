# 照片加日期 · Film Date Stamp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows / macOS](https://img.shields.io/badge/Platform-Windows%20%2F%20macOS-blue.svg)](https://github.com/szmahai-bit/photo-date-stamp)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Pillow: 11+](https://img.shields.io/badge/Pillow-11%2B-orange.svg)](https://python-pillow.org/)

一个给照片批量添加**胶片相机风格日期戳**的独立 GUI 工具。橙红色七段数码管字体、柔光与段亮度不均，采用「滤色（screen）」方式叠加——暗处发光、亮处自然淡去，模拟胶片背面曝光的真实观感。

支持横构图放右下、竖构图放右上并旋转 90°，位置比例来自真实 Pentax 胶片样片测量。原图不会被修改，输出保留 EXIF 与 ICC 色彩配置。

**完全独立运行**，不依赖 Alcedo Studio 或任何私有 Skill。

> English documentation: [README_EN.md](README_EN.md)

---

## 功能特性

- 🖼️ **三种导入方式**：添加单张照片、添加整个文件夹（含子文件夹）、Windows 上还可从资源管理器直接拖放文件 / 文件夹到窗口（macOS 用按钮添加）
- 🔍 **实时预览**：点选列表中的任意照片，右侧即时显示盖章后的效果
- 📅 **日期来源**：自动读取照片 EXIF 拍摄时间（`DateTimeOriginal` → `DateTimeDigitized` → `DateTime`），无 EXIF 时可手动指定
- 🎨 **高度可调**：日期格式、字号、颜色、横竖位置、边距、光晕 / 残影均可调整并实时刷新
- 🧾 **批量处理**：进度条 + 日志，输出目录可选（默认输出到每张照片所在目录下的 `dated/` 子文件夹）
- 💾 **无损原图**：原图不改动，输出保留 EXIF 与 ICC，并已修正 EXIF 方向避免竖拍导出后变横
- 📦 **跨平台**：Windows 提供自包含单文件 EXE，macOS 提供 `.app` / `.dmg`，双击即用
- 🔤 **跟随系统字体**：界面字号读取系统 UI 字体设置（Windows 读注册表，macOS 用系统字体）并随 DPI 缩放

---

## 快速开始

### Windows：下载预编译 EXE（推荐）

前往 [Releases](../../releases) 下载最新的 `照片加日期.exe`，放到任意目录双击运行即可，无需安装 Python 或任何依赖。

### macOS：下载 .app / .dmg（推荐）

前往 [Releases](../../releases) 下载最新的 `照片加日期.dmg`（或 Actions 构建产物里的 `照片加日期.app`）：

- `.dmg`：双击打开，把「照片加日期」拖进「应用程序」即可。
- `.app`：可直接双击运行。若 macOS 提示「无法打开，因为来自身份不明的开发者」，右键 → 打开 → 再点「打开」；或在「系统设置 → 隐私与安全性」里点「仍要打开」。

> macOS App 由 GitHub Actions 在 macOS 机器上自动构建，本仓库不直接提供在 Windows 上制作的 Mac 安装包。

### 从源码运行（Windows / macOS 通用）

需要 Python 3.10+（含 tkinter）：

```bash
git clone https://github.com/szmahai-bit/photo-date-stamp.git
cd photo-date-stamp
pip install -r requirements.txt
python photo_date_gui.py
```

Windows 也可双击 `run.bat` 启动（需确保 `python` 在 PATH 中，或把脚本里的 Python 路径改为本机路径）。

> 注意：Windows 上支持系统级拖放（Win32 API）；macOS 上用「添加照片 / 添加文件夹」按钮导入，其余功能一致。核心渲染 `stamp_core.py` 仅依赖 Pillow，全平台通用。

---

## 使用说明

1. **添加照片**：点「添加照片」多选图片；点「添加文件夹」批量导入；或直接把照片 / 文件夹拖进窗口。
2. **预览**：点左侧列表任一张照片，右侧显示加上日期后的效果。
3. **设置**：
   - 日期来源：默认读 EXIF；无 EXIF 的照片切换为「手动指定日期」。
   - 日期格式：默认撇号年（`'26 11 17`），可选 `2026.11.17` 等。
   - 字号 / 颜色 / 位置 / 边距 / 光晕：均可调，改完预览实时更新。
   - 位置 `auto`：横图右下、竖图右上并旋转 90°，与真实胶片相机一致。
4. **输出目录**：留空则输出到每张照片所在目录下的 `dated/` 子文件夹；也可点「浏览」自选。
5. **开始处理**：点「开始处理」，成品保存到输出目录，原图保持不变。

---

## 渲染原理

日期戳不是简单的半透明文字贴图，而是按胶片背面曝光的物理特性设计：

1. 用自绘多边形生成**七段数码管**字形，模拟段与段之间的亮度差异（`_segment_gain`）。
2. 熄灭的段保留极暗的「残影」（ghost），模拟未完全熄灭的荧光。
3. 高斯模糊制造柔光与光晕（glow）。
4. 生成一个黑色背景、彩色发光的「光量图层」，与原图做 **screen（滤色）** 混合：
   - 暗处（接近黑）叠上去仍然发光；
   - 亮处（接近白）叠上去几乎不变，自然淡去。

这正是胶片机日期打印在亮背景上变淡、在暗背景上鲜明的原因。

---

## 项目结构

```
photo-date-stamp/
├── photo_date_gui.py      # GUI 主程序（tkinter）
├── stamp_core.py          # 渲染与处理核心（仅依赖 Pillow，可独立调用）
├── assets/
│   ├── icon.ico           # Windows EXE 图标（由 make_icon.py 生成，不入库）
│   └── icon.iconset/      # macOS 图标源 PNG（生成，不入库）
├── make_icon.py           # 纯 Pillow 日历图标生成器（ico + iconset）
├── docs/
│   └── screenshots/       # 界面截图
├── .github/
│   ├── ISSUE_TEMPLATE/    # Issue 模板
│   └── workflows/         # CI / 自动打包（Windows EXE + macOS App）
├── build.spec             # PyInstaller 单文件配置（Windows）
├── build_mac.spec         # PyInstaller .app 配置（macOS）
├── build.bat              # Windows 一键打包脚本
├── build_mac.sh           # macOS 一键打包脚本
├── run.bat                # Windows 源码启动脚本
├── requirements.txt
└── README.md
```

`stamp_core.py` 是纯逻辑模块，不依赖 GUI，可作为库在其它 Python 程序中直接调用：

```python
from stamp_core import process_file

ok, text = process_file("input.jpg", "output.jpg")
# ok: 是否成功；text: 实际盖上的日期文本
```

---

## 从源码打包

### Windows EXE

```bat
pip install -r requirements-dev.txt
build.bat
```

构建脚本会先用 `make_icon.py` 生成 `assets/icon.ico`（纯 Pillow、无外部素材），再交给 PyInstaller，因此仓库里不需要提交二进制图标。产物为 `dist/照片加日期.exe`（单文件，约 30 MB）。`build.spec` 中已内置 `stamp_core`、`PIL._tkinter_finder`、`ctypes.wintypes` 等隐藏导入。

也可手动：

```bat
pyinstaller build.spec --noconfirm --clean
```

### macOS App

在 macOS 上（需 Python 3.10+ 与系统自带 `iconutil`）：

```bash
pip install -r requirements-dev.txt
bash build_mac.sh
```

脚本会生成图标（ico + iconset → 用 `iconutil` 转成 `.icns`），再用 `build_mac.spec` 打出 `dist/照片加日期.app`。可直接运行，或拖入「应用程序」。如需 `.dmg`：

```bash
hdiutil create -volname "照片加日期" -srcfolder "dist/照片加日期.app" -ov -format UDZO "dist/照片加日期.dmg"
```

> PyInstaller 不能跨平台编译——macOS App 必须在 macOS 上构建。本仓库的 GitHub Actions 会在 `macos-latest` 上自动完成构建，并在打 tag（如 `v1.1.0`）时把 `.dmg` 附到 Release。

---

## 贡献

欢迎提交 Issue 和 Pull Request。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE) © 2026 Horse

## 致谢

- [Pillow](https://python-pillow.org/) —— 图像处理
- 真实 Pentax 胶片样片 —— 位置与配色参考
