# 照片加日期 · Film Date Stamp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue.svg)](https://www.microsoft.com/windows)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Pillow: 11+](https://img.shields.io/badge/Pillow-11%2B-orange.svg)](https://python-pillow.org/)

一个给照片批量添加**胶片相机风格日期戳**的独立 GUI 工具。橙红色七段数码管字体、柔光与段亮度不均，采用「滤色（screen）」方式叠加——暗处发光、亮处自然淡去，模拟胶片背面曝光的真实观感。

支持横构图放右下、竖构图放右上并旋转 90°，位置比例来自真实 Pentax 胶片样片测量。原图不会被修改，输出保留 EXIF 与 ICC 色彩配置。

**完全独立运行**，不依赖 Alcedo Studio 或任何私有 Skill。

> English documentation: [README_EN.md](README_EN.md)

---

## 功能特性

- 🖼️ **三种导入方式**：添加单张照片、添加整个文件夹（含子文件夹）、从资源管理器直接拖放文件或文件夹到窗口
- 🔍 **实时预览**：点选列表中的任意照片，右侧即时显示盖章后的效果
- 📅 **日期来源**：自动读取照片 EXIF 拍摄时间（`DateTimeOriginal` → `DateTimeDigitized` → `DateTime`），无 EXIF 时可手动指定
- 🎨 **高度可调**：日期格式、字号、颜色、横竖位置、边距、光晕 / 残影均可调整并实时刷新
- 🧾 **批量处理**：进度条 + 日志，输出目录可选（默认输出到每张照片所在目录下的 `dated/` 子文件夹）
- 💾 **无损原图**：原图不改动，输出保留 EXIF 与 ICC
- 🪟 **开箱即用**：提供自包含单文件 EXE（内置 Python + tkinter + Pillow），64 位 Windows 10/11 双击即用
- 🔤 **跟随系统字体**：界面字号读取 Windows 系统 UI 字体设置并随 DPI 缩放

---

## 快速开始

### 方式一：下载预编译 EXE（推荐）

前往 [Releases](../../releases) 下载最新的 `照片加日期.exe`，放到任意目录双击运行即可，无需安装 Python 或任何依赖。

### 方式二：从源码运行

需要 Windows + Python 3.10+：

```bat
git clone https://github.com/<你的用户名>/photo-date-stamp.git
cd photo-date-stamp
pip install -r requirements.txt
python photo_date_gui.py
```

也可双击 `run.bat` 启动（需先将其中 Python 路径改为本机路径，或确保 `python` 在 PATH 中）。

> 注意：GUI 使用 `tkinter` 与 Windows 原生 API（`winreg`、`ctypes`），仅支持 Windows。

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
│   └── icon.ico           # 程序图标（由 make_icon.py 生成，不入库）
├── make_icon.py           # 纯 Pillow 日历图标生成器
├── docs/
│   └── screenshots/       # 界面截图
├── .github/
│   ├── ISSUE_TEMPLATE/    # Issue 模板
│   └── workflows/         # CI / 自动打包
├── build.spec             # PyInstaller 单文件配置
├── build.bat              # 一键打包脚本
├── run.bat                # 源码启动脚本
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

## 从源码打包 EXE

```bat
pip install -r requirements-dev.txt
build.bat
```

构建脚本会先用 `make_icon.py` 生成 `assets/icon.ico`（纯 Pillow、无外部素材），再交给 PyInstaller，因此仓库里不需要提交二进制图标。产物为 `dist/照片加日期.exe`（单文件，约 30 MB）。`build.spec` 中已内置 `stamp_core`、`PIL._tkinter_finder`、`ctypes.wintypes` 等隐藏导入。

也可手动：

```bat
pyinstaller build.spec --noconfirm --clean
```

---

## 贡献

欢迎提交 Issue 和 Pull Request。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE) © 2026 Horse

## 致谢

- [Pillow](https://python-pillow.org/) —— 图像处理
- 真实 Pentax 胶片样片 —— 位置与配色参考
