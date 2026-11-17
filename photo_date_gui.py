#!/usr/bin/env python3
"""照片加日期 —— 独立 GUI 工具。

双击「启动工具.bat」运行。功能：
  - 添加单张照片 / 添加整个文件夹（含子文件夹）
  - 文件列表管理，点选即实时预览盖章效果
  - 日期来源：EXIF 拍摄时间 或 手动指定
  - 可调：日期格式、字号、颜色、横竖位置、边距、光晕/残影
  - 批量处理，进度条 + 日志，输出目录可选
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
import ctypes
import winreg
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

from PIL import Image, ImageTk

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stamp_core as core

APP_TITLE = "照片加日期 · 胶片日期戳工具"
PRESET_COLORS = [
    ("Pentax 橙红", "ff5c1c"),
    ("琥珀黄", "ff9b42"),
    ("经典红", "e23b2e"),
    ("暖白", "ffd9a0"),
]
FORMATS = [
    ("'26 11 17  撇号年(默认)", "'%y %m %d"),
    ("2026.11.17  点分隔", "%Y.%m.%d"),
    ("2026-11-17  横线", "%Y-%m-%d"),
    ("2026 11 17  空格", "%Y %m %d"),
    ("26 11 17   两位年", "%y %m %d"),
]


def detect_system_font():
    """读取 Windows 系统 UI 字体(名称与字号 pt)，失败则回退到 tkinter 默认。

    系统字号改变(设置->个性化->字体大小)后重启本工具，界面字体会随之变化。
    """
    face, pt = None, None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Control Panel\Desktop\WindowMetrics")
        raw = bytes(winreg.QueryValueEx(key, "MessageFont")[0])
        winreg.CloseKey(key)
        height_px = ctypes.c_int.from_buffer_copy(raw[:4]).value   # LOGFONT.lfHeight
        pt = max(8, round(abs(height_px) * 72 / 96))                # 96dpi: px -> pt
        name_buf = (ctypes.c_wchar * 32).from_buffer_copy(raw[28:28 + 64])
        face = name_buf.value or None
    except Exception:
        pass
    if not face or not pt:
        d = tkfont.nametofont("TkDefaultFont")
        face = face or d.cget("family")
        pt = pt or abs(d.cget("size")) or 9
    return face, pt


def setup_theme(root: tk.Tk):
    """按系统 UI 字体统一设置全部控件字号，并让界面随 DPI 缩放。"""
    face, sys_pt = detect_system_font()
    # 系统字号为基准；全屏/高分屏下略放大一档以保证可读，仍随系统字号联动。
    base = sys_pt + 2
    ui_scale = root.winfo_fpixels("1i") / 96.0  # DPI 缩放因子
    sizes = {
        "body": max(10, round(base * ui_scale)),
        "small": max(9, round((base - 1) * ui_scale)),
        "title": max(15, round((base + 6) * ui_scale)),
        "header": max(12, round((base + 2) * ui_scale)),
        "mono": max(9, round((base - 1) * ui_scale)),
        # 日志用系统 UI 字体并放大一档：Consolas 不含中文字形，中文会回退成另一种
        # 字体导致大小不一、发虚，日志里全是中文+文件名，用系统字体最清晰。
        "log": max(12, round((base + 2) * ui_scale)),
    }
    fonts = {
        "body": (face, sizes["body"]),
        "small": (face, sizes["small"]),
        "title": (face, sizes["title"], "bold"),
        "header": (face, sizes["header"], "bold"),
        "mono": ("Consolas", sizes["mono"]),
        "log": (face, sizes["log"]),
    }

    # 统一 ttk 命名样式，全局生效
    style = ttk.Style()
    for opt in ("TLabel", "TButton", "TCheckbutton", "TRadiobutton",
                "TEntry", "TCombobox", "TLabelframe.Label", "Treeview"):
        style.configure(opt, font=fonts["body"])
    style.configure("Title.TLabel", font=fonts["title"])
    style.configure("Header.TLabel", font=fonts["header"])
    style.configure("Small.TLabel", font=fonts["small"])
    style.configure("Mono.TLabel", font=fonts["mono"])
    style.configure("Treeview.Heading", font=fonts["body"])

    # 让 tkinter 原生 Text 等也跟随
    for n in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
        f = tkfont.nametofont(n)
        f.configure(family=face, size=sizes["body"])
    return fonts, sizes


def enable_file_drop(root: tk.Tk, on_paths) -> bool:
    """让整个窗口接受从资源管理器/桌面拖入的文件与文件夹（Windows 原生，零依赖）。

    通过子类化顶层窗口的窗口过程拦截 WM_DROPFILES，再把路径排队回主线程处理。
    对 PyInstaller 打包友好，不需要 tkdnd 等第三方 Tcl 插件。返回是否启用成功。
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        # 先固定函数原型，否则 64 位下指针会被 ctypes 默认的 32 位签名截断。
        shell32.DragAcceptFiles.argtypes = [wt.HWND, wt.BOOL]
        shell32.DragAcceptFiles.restype = None
        shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wt.UINT, wt.LPWSTR, wt.UINT]
        shell32.DragQueryFileW.restype = wt.UINT
        shell32.DragFinish.argtypes = [ctypes.c_void_p]
        shell32.DragFinish.restype = None
        user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        user32.CallWindowProcW.restype = ctypes.c_ssize_t

        WM_DROPFILES = 0x0233
        GWL_WNDPROC = -4
        hwnd = wt.HWND(root.winfo_id())

        # 用 PYFUNCTYPE：进入回调时自动获取 GIL（WINFUNCTYPE 不会，Tk 在处理消息时
        # 已释放 GIL，回调里碰 Python 对象会触发 "GIL released" 致命错误）。
        WNDPROC = ctypes.PYFUNCTYPE(
            ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM
        )
        state = {"old": None}
        # 窗口过程绝不能重入 tkinter/Tcl（会破坏 Tk 的线程状态而崩溃）。
        # 它只把拖入的路径写进纯 ctypes 缓冲区并置标志，由下面的主线程定时器取走。
        drop_buf = (ctypes.c_wchar * 32768)()
        drop_flag = ctypes.c_int(0)

        @WNDPROC
        def _proc(h, msg, wp, lp):
            try:
                if msg == WM_DROPFILES:
                    hdrop = ctypes.c_void_p(wp)
                    count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                    paths = []
                    for i in range(count):
                        buf = ctypes.create_unicode_buffer(2048)
                        shell32.DragQueryFileW(hdrop, i, buf, 2048)
                        if buf.value:
                            paths.append(buf.value)
                    shell32.DragFinish(hdrop)
                    if paths:
                        drop_buf.value = "\n".join(paths)
                        drop_flag.value = 1
                    return 0
            except Exception:
                pass
            return user32.CallWindowProcW(state["old"], h, msg, wp, lp)

        def _poll():
            if drop_flag.value:
                drop_flag.value = 0
                raw = drop_buf.value
                if raw:
                    on_paths(raw.split("\n"))
            root.after(120, _poll)

        get_fn = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        set_fn = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        get_fn.argtypes = [wt.HWND, ctypes.c_int]
        get_fn.restype = ctypes.c_void_p
        set_fn.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_void_p]
        set_fn.restype = ctypes.c_void_p

        state["old"] = get_fn(hwnd, GWL_WNDPROC)
        set_fn(hwnd, GWL_WNDPROC, _proc)
        # 持有引用，防止回调对象被 GC 后窗口过程失效导致崩溃
        root._drop_state = (state, _proc, _poll, hwnd)
        shell32.DragAcceptFiles(hwnd, True)
        root.after(120, _poll)   # 主线程定时取走缓冲区里的拖入路径
        return True
    except Exception as e:
        print("拖放初始化失败:", e)
        return False


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1220x860")
        self.root.minsize(1020, 700)

        self.files: list[Path] = []
        self.preview_img: Image.Image | None = None
        self.preview_tk: ImageTk.PhotoImage | None = None
        self.preview_full: Image.Image | None = None   # 原始方向图(未 exif_transpose)
        self.processing = False
        self.cancel_flag = False

        self.fonts, self.sizes = setup_theme(root)
        self._vars()
        self._build()
        # 启用系统级拖放：照片文件或文件夹直接拖进窗口即可加入列表
        self._drop_ok = enable_file_drop(root, self._on_drop_paths)
        face, pt = detect_system_font()
        hint = " · 支持拖放照片/文件夹" if self._drop_ok else ""
        self._log(f"就绪。系统字体 {face} {pt}pt · Python {sys.version.split()[0]} · Pillow {__import__('PIL').__version__}{hint}")

    def _vars(self):
        self.v_date_mode = tk.StringVar(value="exif")
        self.v_manual_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.v_format = tk.StringVar(value=FORMATS[0][1])
        self.v_size_mode = tk.StringVar(value="auto")
        self.v_size_px = tk.StringVar(value="90")
        self.v_size_ratio = tk.StringVar(value="0.032")
        self.v_color = tk.StringVar(value="ff5c1c")
        self.v_orient = tk.StringVar(value="auto")
        self.v_right = tk.StringVar(value="0.10")
        self.v_edge_auto = tk.BooleanVar(value=True)
        self.v_edge = tk.StringVar(value="0.089")
        self.v_glow = tk.BooleanVar(value=True)
        self.v_ghost = tk.BooleanVar(value=True)
        self.v_out = tk.StringVar(value="")
        self.v_quality = tk.StringVar(value="95")
        self.v_recursive = tk.BooleanVar(value=True)

    def _build(self):
        root = self.root
        # ---- 顶部标题栏 ----
        head = ttk.Frame(root, padding=(14, 10))
        head.pack(fill="x")
        ttk.Label(head, text="照片加日期 · 胶片日期戳", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text="模拟胶片相机背面曝光 · Pentax 橙红七段数码管",
                  style="Small.TLabel", foreground="#888").pack(side="left", padx=14)

        main = ttk.Frame(root, padding=(10, 4))
        main.pack(fill="both", expand=True)
        # 三列：0=文件列表(固定) 1=预览(弹性) 2=参数面板(固定)。不要给空列配 weight，
        # 否则全屏时多余空间会跑到空列，右侧留下一大片空白。
        main.columnconfigure(0, weight=0, minsize=270)
        main.columnconfigure(1, weight=1, minsize=360)
        main.columnconfigure(2, weight=0, minsize=410)
        main.rowconfigure(0, weight=1)

        # ================= 左列：文件列表 =================
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="照片列表 · 可拖入", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))

        listframe = ttk.Frame(left)
        listframe.grid(row=1, column=0, sticky="nsew")
        listframe.columnconfigure(0, weight=1)
        listframe.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(listframe, columns=("name",), show="headings", selectmode="extended")
        self.tree.heading("name", text="文件")
        self.tree.column("name", width=280, anchor="w")
        sb = ttk.Scrollbar(listframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btns = ttk.Frame(left)
        btns.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        for i in range(2):
            btns.columnconfigure(i, weight=1)
        ttk.Button(btns, text="添加照片", command=self.add_files).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(btns, text="添加文件夹", command=self.add_folder).grid(row=0, column=1, sticky="ew", padx=(3, 0))
        ttk.Button(btns, text="移除选中", command=self.remove_selected).grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(4, 0))
        ttk.Button(btns, text="清空列表", command=self.clear_list).grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(4, 0))
        self.v_recursive_widget = ttk.Checkbutton(left, text="添加文件夹时包含子文件夹",
                                                   variable=self.v_recursive)
        self.v_recursive_widget.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.count_lbl = ttk.Label(left, text="共 0 张", foreground="#666")
        self.count_lbl.grid(row=4, column=0, sticky="w", pady=(4, 0))

        # ================= 中列：预览 =================
        mid = ttk.LabelFrame(main, text="预览（点选左侧照片）", padding=8)
        mid.grid(row=0, column=1, sticky="nsew", padx=6)
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)
        self.preview_lbl = ttk.Label(mid, background="#2a2a2a", anchor="center")
        self.preview_lbl.grid(row=0, column=0, sticky="nsew")
        self.preview_info = ttk.Label(mid, text="未选择照片", foreground="#666", anchor="center")
        self.preview_info.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(mid, text="刷新预览", command=self.refresh_preview).grid(row=2, column=0, pady=(6, 0))

        # ================= 右列：参数 =================
        right = ttk.Frame(main)
        right.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        # 右列用 Canvas 实现滚动
        cv = tk.Canvas(right, highlightthickness=0)
        cv.grid(row=0, column=0, sticky="nsew")
        right.rowconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=cv.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        cv.configure(yscrollcommand=scrollbar.set)
        self.param = ttk.Frame(cv, padding=(4, 4))
        self.param.columnconfigure(0, weight=1)
        self._canvas_win = cv.create_window((0, 0), window=self.param, anchor="nw")
        self.param.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        # 让参数面板内部 frame 宽度始终跟随 Canvas，避免字体变大后右侧文字被裁切
        cv.bind("<Configure>", lambda e: cv.itemconfigure(self._canvas_win, width=e.width))
        cv.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_params(self.param)

        # ================= 底部：输出 + 执行 + 日志 =================
        bottom = ttk.Frame(root, padding=(12, 8))
        bottom.pack(fill="x")
        row1 = ttk.Frame(bottom)
        row1.pack(fill="x")
        ttk.Label(row1, text="输出目录：").pack(side="left")
        ttk.Entry(row1, textvariable=self.v_out, width=60).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="浏览…", command=self.choose_out).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="留空=原目录/dated", command=lambda: self.v_out.set("")).pack(side="left")

        row2 = ttk.Frame(bottom)
        row2.pack(fill="x", pady=(6, 0))
        self.run_btn = ttk.Button(row2, text="开始处理", command=self.start_process)
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(row2, text="取消", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.prog = ttk.Progressbar(row2, mode="determinate", length=360)
        self.prog.pack(side="left", padx=6)
        self.prog_lbl = ttk.Label(row2, text="")
        self.prog_lbl.pack(side="left")
        ttk.Button(row2, text="打开输出目录", command=self.open_out).pack(side="right")

        log_frame = ttk.LabelFrame(bottom, text="日志", padding=(4, 4))
        log_frame.pack(fill="x", pady=(8, 0))
        # 白底深字 + 系统字体 12pt + 留白/行距，日志里的中文和文件名都清晰可读
        self.log_text = tk.Text(
            log_frame, height=6, wrap="word", font=self.fonts["log"],
            foreground="#1a1a1a", background="#ffffff",
            insertbackground="#1a1a1a", relief="solid", borderwidth=1,
            padx=10, pady=6, spacing1=2, spacing3=2,
        )
        self.log_text.pack(fill="x")
        self.log_text.configure(state="disabled")

    def _build_params(self, p):
        r = 0
        # 日期来源
        f = ttk.LabelFrame(p, text="日期来源", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        f.columnconfigure(1, weight=1)
        ttk.Radiobutton(f, text="读取照片 EXIF 拍摄时间", variable=self.v_date_mode,
                        value="exif", command=self._toggle_date).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(f, text="手动指定日期", variable=self.v_date_mode,
                        value="manual", command=self._toggle_date).grid(row=1, column=0, sticky="w")
        self.manual_entry = ttk.Entry(f, textvariable=self.v_manual_date, width=14, state="disabled")
        self.manual_entry.grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(f, text="YYYY-MM-DD", foreground="#888").grid(row=1, column=2, sticky="w")

        # 日期格式
        f = ttk.LabelFrame(p, text="日期格式", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        f.columnconfigure(0, weight=1)
        fmtcb = ttk.Combobox(f, textvariable=self.v_format, values=[x[1] for x in FORMATS],
                             state="readonly", width=30)
        fmtcb.grid(row=0, column=0, sticky="ew")
        fmtcb.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())
        self.fmt_desc = ttk.Label(f, text="撇号年样式，最像胶片机", foreground="#888")
        self.fmt_desc.grid(row=1, column=0, sticky="w", pady=(4, 0))
        fmtcb.bind("<<ComboboxSelected>>", self._fmt_changed)

        # 字号
        f = ttk.LabelFrame(p, text="字号", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        f.columnconfigure(1, weight=1)
        ttk.Radiobutton(f, text="自动(按图大小)", variable=self.v_size_mode, value="auto",
                        command=self._toggle_size).grid(row=0, column=0, sticky="w")
        self.size_ratio_e = ttk.Entry(f, textvariable=self.v_size_ratio, width=8)
        self.size_ratio_e.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(f, text="= 短边的比例", foreground="#888").grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(f, text="固定像素", variable=self.v_size_mode, value="px",
                        command=self._toggle_size).grid(row=1, column=0, sticky="w")
        self.size_px_e = ttk.Entry(f, textvariable=self.v_size_px, width=8, state="disabled")
        self.size_px_e.grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(f, text="数字高度 px", foreground="#888").grid(row=1, column=2, sticky="w")

        # 颜色
        f = ttk.LabelFrame(p, text="颜色", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        f.columnconfigure(1, weight=1)
        colorcb = ttk.Combobox(f, textvariable=self.v_color,
                               values=[c[1] for c in PRESET_COLORS], width=12)
        colorcb.grid(row=0, column=0, sticky="w")
        colorcb.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())
        self.color_swatch = tk.Label(f, text="    ", background="#ff5c1c", width=4, relief="ridge")
        self.color_swatch.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(f, text="自定义…", command=self.choose_color).grid(row=0, column=2, sticky="w")
        ttk.Label(f, text="十六进制，如 ff5c1c", foreground="#888").grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # 位置
        f = ttk.LabelFrame(p, text="位置", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text="方向布局：").grid(row=0, column=0, sticky="w")
        orientcb = ttk.Combobox(f, textvariable=self.v_orient,
                                values=["auto", "landscape", "portrait"], state="readonly", width=16)
        orientcb.grid(row=0, column=1, sticky="w")
        orientcb.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())
        ttk.Label(f, text="auto=横图右下/竖图右上(旋转90°)", foreground="#888").grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))
        ttk.Label(f, text="距右边缘：").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(f, textvariable=self.v_right, width=8).grid(row=2, column=1, sticky="w", padx=6, pady=(4, 0))
        ttk.Label(f, text="= 图宽的比例 (默认 0.10)", foreground="#888").grid(row=2, column=2, sticky="w", pady=(4, 0))
        ttk.Checkbutton(f, text="纵向边距自动(横0.089/竖0.133)", variable=self.v_edge_auto,
                        command=self._toggle_edge).grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self.edge_e = ttk.Entry(f, textvariable=self.v_edge, width=8, state="disabled")
        self.edge_e.grid(row=4, column=1, sticky="w", padx=6)
        ttk.Label(f, text="自定义距下/上比例", foreground="#888").grid(row=4, column=2, sticky="w")

        # 质感
        f = ttk.LabelFrame(p, text="质感", padding=8)
        f.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        ttk.Checkbutton(f, text="柔光光晕", variable=self.v_glow,
                        command=self.refresh_preview).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(f, text="残影(未点亮段)", variable=self.v_ghost,
                        command=self.refresh_preview).grid(row=0, column=1, sticky="w")
        ttk.Label(f, text="JPEG 质量").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(f, textvariable=self.v_quality, width=8).grid(row=1, column=1, sticky="w", pady=(4, 0))

    # ---------------- 事件 ----------------
    def _toggle_date(self):
        self.manual_entry.configure(state="normal" if self.v_date_mode.get() == "manual" else "disabled")
        self.refresh_preview()

    def _toggle_size(self):
        auto = self.v_size_mode.get() == "auto"
        self.size_ratio_e.configure(state="normal" if auto else "disabled")
        self.size_px_e.configure(state="disabled" if auto else "normal")
        self.refresh_preview()

    def _toggle_edge(self):
        self.edge_e.configure(state="disabled" if self.v_edge_auto.get() else "normal")
        self.refresh_preview()

    def _fmt_changed(self, event=None):
        fmt = self.v_format.get()
        desc = next((d for label, d in FORMATS if d == fmt), "")
        self.fmt_desc.configure(text=desc or "自定义 strftime 格式")

    def choose_color(self):
        from tkinter import colorchooser
        hexv = self.v_color.get().lstrip("#")
        rgb = tuple(int(hexv[i:i+2], 16) for i in (0, 2, 4)) if len(hexv) == 6 else (255, 92, 28)
        result = colorchooser.askcolor(initialcolor=rgb, title="选择日期颜色")
        if result and result[1]:
            self.v_color.set(result[1].lstrip("#"))
            self.color_swatch.configure(background=result[1])
            self.refresh_preview()

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择照片（可多选）",
            filetypes=[("图片文件", "*.jpg *.jpeg *.jpe *.tif *.tiff *.png *.bmp *.webp"),
                       ("所有文件", "*.*")])
        self._add(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择照片文件夹")
        if not folder:
            return
        folder = Path(folder)
        files = []
        if self.v_recursive.get():
            it = folder.rglob("*")
        else:
            it = folder.glob("*")
        for p in it:
            if p.is_file() and p.suffix.lower() in core.IMAGE_SUFFIXES:
                files.append(p)
        self._add([str(p) for p in sorted(files)])

    def _add(self, paths):
        added = 0
        existing = {str(p) for p in self.files}
        for raw in paths:
            p = Path(raw)
            if str(p) in existing:
                continue
            self.files.append(p)
            existing.add(str(p))
            self.tree.insert("", "end", values=(p.name,), iid=str(p))
            added += 1
        self.count_lbl.configure(text=f"共 {len(self.files)} 张")
        self._log(f"添加 {added} 张，当前共 {len(self.files)} 张")
        if added and not self.preview_full:
            first = self.tree.get_children()
            if first:
                self.tree.selection_set(first[0])

    def _on_drop_paths(self, paths):
        """把从外部拖入的文件/文件夹展开为图片路径后加入列表。"""
        files = []
        skipped = 0
        for raw in paths:
            p = Path(raw)
            if p.is_dir():
                it = p.rglob("*") if self.v_recursive.get() else p.glob("*")
                for q in it:
                    if q.is_file() and q.suffix.lower() in core.IMAGE_SUFFIXES:
                        files.append(str(q))
            elif p.is_file() and p.suffix.lower() in core.IMAGE_SUFFIXES:
                files.append(str(p))
            else:
                skipped += 1
        if files:
            self._add(sorted(set(files)))
        if skipped:
            self._log(f"拖入的 {skipped} 项不是图片，已忽略")
        if not files and not skipped:
            self._log("拖入的文件夹里没有找到图片")

    def remove_selected(self):
        sel = self.tree.selection()
        for iid in sel:
            self.tree.delete(iid)
            self.files = [p for p in self.files if str(p) != iid]
        self.count_lbl.configure(text=f"共 {len(self.files)} 张")
        if not self.files:
            self._clear_preview()

    def clear_list(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.files.clear()
        self.count_lbl.configure(text="共 0 张")
        self._clear_preview()
        self._log("已清空列表")

    def _clear_preview(self):
        self.preview_full = None
        self.preview_img = None
        self.preview_tk = None
        self.preview_lbl.configure(image="")
        self.preview_info.configure(text="未选择照片")

    def _on_select(self, event=None):
        self.refresh_preview()

    def _collect_params(self) -> dict:
        def parse_color(s):
            s = s.lstrip("#")
            if len(s) != 6:
                raise ValueError("颜色需为 6 位十六进制")
            return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

        size = None if self.v_size_mode.get() == "auto" else int(self.v_size_px.get())
        size_ratio = float(self.v_size_ratio.get())
        edge = None if self.v_edge_auto.get() else float(self.v_edge.get())
        return dict(
            date_mode=self.v_date_mode.get(),
            manual_date=self.v_manual_date.get().strip(),
            date_format=self.v_format.get(),
            size=size, size_ratio=size_ratio,
            color=parse_color(self.v_color.get()),
            orientation=self.v_orient.get(),
            right_ratio=float(self.v_right.get()),
            edge_ratio=edge,
            glow=self.v_glow.get(), ghost=self.v_ghost.get(),
            quality=int(self.v_quality.get()),
        )

    def refresh_preview(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = Path(sel[0])
        try:
            with Image.open(path) as im:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(im)
                img.load()
            self.preview_full = img
        except Exception as e:
            self.preview_info.configure(text=f"无法预览: {e}")
            return
        try:
            p = self._collect_params()
            captured = None
            if p["date_mode"] == "manual":
                captured = datetime.strptime(p["manual_date"], "%Y-%m-%d")
            else:
                captured = core.read_exif_datetime(path)
            if captured is None:
                self.preview_info.configure(text=f"{path.name} · 无 EXIF 日期（处理时需手动指定日期）")
                self._render_preview(img.copy(), path)
                return
            text = captured.strftime(p["date_format"])
            result = core.apply_stamp(img.copy(), text, size=p["size"], size_ratio=p["size_ratio"],
                                      color=p["color"], glow=p["glow"], ghost=p["ghost"],
                                      orientation=p["orientation"], right_ratio=p["right_ratio"],
                                      edge_ratio=p["edge_ratio"])
            self._render_preview(result, path, text)
        except Exception as e:
            self.preview_info.configure(text=f"预览失败: {e}")

    def _render_preview(self, img: Image.Image, path: Path, text: str = ""):
        preview = img.copy()
        preview.thumbnail((560, 470), Image.LANCZOS)
        self.preview_tk = ImageTk.PhotoImage(preview)
        self.preview_lbl.configure(image=self.preview_tk)
        d = core.read_exif_datetime(path)
        dateinfo = d.strftime("%Y-%m-%d %H:%M") if d else "无 EXIF"
        orient = "竖" if img.height > img.width else "横"
        suffix = f"  日期 {text}" if text else ""
        self.preview_info.configure(text=f"{path.name} · {img.width}×{img.height} · {orient}构图 · EXIF {dateinfo}{suffix}")

    def choose_out(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.v_out.set(d)

    def open_out(self):
        out = self.v_out.get().strip()
        if not out and self.files:
            out = str(self.files[0].parent / "dated")
        if out and Path(out).exists():
            os.startfile(out)
        else:
            messagebox.showinfo("提示", "输出目录还不存在，先处理一次照片吧。")

    # ---------------- 处理 ----------------
    def start_process(self):
        if self.processing:
            return
        if not self.files:
            messagebox.showwarning("提示", "请先添加照片或文件夹。")
            return
        try:
            p = self._collect_params()
        except Exception as e:
            messagebox.showerror("参数错误", str(e))
            return
        self.processing = True
        self.cancel_flag = False
        self.run_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.prog.configure(maximum=len(self.files), value=0)
        t = threading.Thread(target=self._worker, args=(p,), daemon=True)
        t.start()

    def cancel(self):
        self.cancel_flag = True
        self._log("收到取消请求，将在当前张完成后停止…")

    def _worker(self, p: dict):
        out_dir = self.v_out.get().strip()
        success = 0
        fail = 0
        try:
            for idx, src in enumerate(self.files, 1):
                if self.cancel_flag:
                    self._log("已取消。")
                    break
                self.root.after(0, lambda i=idx, n=len(self.files): self.prog_lbl.configure(text=f"{i}/{n}"))
                self.root.after(0, lambda i=idx: self.prog.configure(value=i - 1))

                if out_dir:
                    dst = Path(out_dir) / src.name
                else:
                    dst = src.parent / "dated" / src.name

                captured = None
                if p["date_mode"] == "manual":
                    captured = p["manual_date"]
                ok, note = core.process_file(
                    src, dst, captured=captured, date_format=p["date_format"],
                    size=p["size"], size_ratio=p["size_ratio"], color=p["color"],
                    glow=p["glow"], ghost=p["ghost"], orientation=p["orientation"],
                    right_ratio=p["right_ratio"], edge_ratio=p["edge_ratio"],
                    quality=p["quality"])
                if ok:
                    success += 1
                    self._log(f"OK   {src.name}  →  {note}")
                else:
                    fail += 1
                    self._log(f"FAIL {src.name}  →  {note}")
            self.root.after(0, lambda: self.prog.configure(value=len(self.files) if not self.cancel_flag else self.prog["value"]))
        except Exception:
            self._log("处理异常:\n" + traceback.format_exc())
        finally:
            self.root.after(0, self._finish, success, fail)

    def _finish(self, success, fail):
        self.processing = False
        self.run_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.prog_lbl.configure(text="完成")
        self._log(f"\n处理结束：成功 {success} 张，失败 {fail} 张。")
        messagebox.showinfo("完成", f"处理结束\n成功 {success} 张，失败 {fail} 张")

    def _log(self, msg):
        def do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.root.after(0, do)


def main():
    # 必须在创建窗口前声明 DPI 感知，否则 Windows 会模糊缩放、fpixels 读数也不准。
    try:
        if sys.platform == "win32":
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    # 字体大小统一由 setup_theme 依据系统 UI 字体计算，不再额外叠加缩放。
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
