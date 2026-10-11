#!/usr/bin/env python3
"""TendiesPy - iOS 27 壁纸格式转换工具

将老格式 .tendies 壁纸转换为 iOS 27 Clownfish 格式，恢复景深效果。
转换核心基于经过验证的 Python 实现（family→Clownfish、双 depth plist、
状态壳补全、资源修复等），不包含实验性修改。
"""
import os
import sys
import threading
import zipfile
import tempfile
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import converter as conv


APP_TITLE = "TendiesPy - iOS 27 壁纸转换"
DEFAULT_SUFFIX = ".clownfish"


class TendiesPyGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x560")
        self.root.minsize(600, 450)
        self.files: list[str] = []
        self.converting = False

        self._build_ui()

    # ---------------- UI 搭建 ----------------
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # 文件区
        ttk.Label(main, text="待转换的 .tendies 文件：").pack(anchor="w")
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)

        # 文件按钮
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="删除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="清空", command=self.clear_files).pack(side=tk.LEFT, padx=6)

        # 选项区
        opt = ttk.LabelFrame(main, text="选项", padding=8)
        opt.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(opt, text="输出后缀：").grid(row=0, column=0, sticky="w")
        self.suffix_var = tk.StringVar(value=DEFAULT_SUFFIX)
        ttk.Entry(opt, textvariable=self.suffix_var, width=14).grid(row=0, column=1, sticky="w", padx=(0, 16))

        ttk.Label(opt, text="输出目录：").grid(row=0, column=2, sticky="w")
        self.outdir_var = tk.StringVar(value="（与源文件相同）")
        self.outdir_label = ttk.Label(opt, textvariable=self.outdir_var, foreground="gray")
        self.outdir_label.grid(row=0, column=3, sticky="w", padx=(0, 6))
        ttk.Button(opt, text="选择…", command=self.choose_outdir, width=8).grid(row=0, column=4, sticky="w")
        self.outdir_path: str | None = None

        # 转换按钮 + 进度
        action = ttk.Frame(main)
        action.pack(fill=tk.X, pady=(0, 6))
        self.convert_btn = ttk.Button(action, text="开始转换", command=self.start_convert)
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 日志区
        ttk.Label(main, text="转换日志：").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(main, height=12, state=tk.DISABLED,
                                             font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN,
                  anchor="w").pack(side=tk.BOTTOM, fill=tk.X)

    # ---------------- 日志与状态（线程安全） ----------------
    def log_msg(self, msg: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {msg}"
        def _update():
            self.log.config(state=tk.NORMAL)
            self.log.insert(tk.END, line + "\n")
            self.log.see(tk.END)
            self.log.config(state=tk.DISABLED)
        self.root.after(0, _update)

    def set_status(self, msg: str):
        self.root.after(0, lambda: self.status_var.set(msg))

    def set_progress(self, value: float, maximum: float):
        def _update():
            self.progress.config(maximum=maximum, value=value)
        self.root.after(0, _update)

    # ---------------- 文件管理 ----------------
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择 .tendies 文件",
            filetypes=[("Tendies 壁纸", "*.tendies"), ("所有文件", "*.*")])
        added = 0
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert(tk.END, os.path.basename(p))
                added += 1
        self.set_status(f"共 {len(self.files)} 个文件" + (f"（本次新增 {added}）" if added else ""))

    def remove_selected(self):
        for i in sorted(self.listbox.curselection(), reverse=True):
            del self.files[i]
            self.listbox.delete(i)
        self.set_status(f"共 {len(self.files)} 个文件")

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        self.set_status("就绪")

    def choose_outdir(self):
        d = filedialog.askdirectory(title="选择输出目录（取消则与源文件相同）")
        if d:
            self.outdir_path = d
            self.outdir_var.set(d)
            self.outdir_label.config(foreground="black")
        else:
            self.outdir_path = None
            self.outdir_var.set("（与源文件相同）")
            self.outdir_label.config(foreground="gray")

    # ---------------- 转换 ----------------
    def start_convert(self):
        if self.converting:
            return
        if not self.files:
            messagebox.showwarning("提示", "请先添加 .tendies 文件")
            return
        suffix = self.suffix_var.get().strip() or DEFAULT_SUFFIX
        self.converting = True
        self.convert_btn.config(state=tk.DISABLED)
        self.set_progress(0, len(self.files))
        threading.Thread(target=self._convert_all, args=(suffix,), daemon=True).start()

    def _convert_one(self, path: str, suffix: str) -> str:
        """返回 'ok' / 'skip' / 'fail'，日志已输出。"""
        name = os.path.basename(path)
        self.log_msg(f"正在转换：{name}")
        work = tempfile.mkdtemp(prefix="tendiespy_")
        try:
            with zipfile.ZipFile(path) as z:
                conv.safe_extract(z, work)

            # 步骤1：格式转换（Clownfish + 景深）
            converted = conv.convert_tree(work)
            if not converted:
                has_descriptor = any(True for _ in conv.iter_descriptor_dirs(work))
                if has_descriptor:
                    self.log_msg("  - 已是新格式，跳过")
                else:
                    self.log_msg("  - 未找到壁纸描述结构，跳过（可能不是有效的 .tendies）")
                return "skip"
            for item in converted:
                planes = item.get("planes")
                self.log_msg(f"  转换平面：{planes}")

            # 步骤2：重命名为官方 Clownfish 文件布局
            for item in conv.rename_descriptors_to_skeleton(work):
                self.log_msg(f"  重命名：{item.get('wallpaper')}")

            # 步骤3：打包（跳过 macOS 垃圾）
            base = os.path.splitext(os.path.basename(path))[0]
            out_dir = self.outdir_path or os.path.dirname(path)
            out = os.path.join(out_dir, base + suffix + ".tendies")
            if os.path.exists(out):
                self.log_msg(f"  ! 输出文件已存在，将覆盖：{os.path.basename(out)}")
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
                for dirpath, _dirs, names in os.walk(work):
                    rel_dir = os.path.relpath(dirpath, work)
                    if rel_dir.split(os.sep)[0].lower() == "__macosx":
                        continue
                    for n in names:
                        if n.startswith("._") or n == ".DS_Store":
                            continue
                        full = os.path.join(dirpath, n)
                        archive.write(full, os.path.relpath(full, work))
            self.log_msg(f"  ✓ 完成 → {os.path.basename(out)}")
            return "ok"
        except Exception as e:  # noqa: BLE001 - 批量转换中单文件失败不中断整体
            self.log_msg(f"  ✗ 出错：{e}")
            return "fail"
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _convert_all(self, suffix: str):
        ok = fail = skip = 0
        total = len(self.files)
        for idx, path in enumerate(list(self.files), start=1):
            self.set_status(f"转换中 ({idx}/{total})：{os.path.basename(path)}")
            result = self._convert_one(path, suffix)
            if result == "ok":
                ok += 1
            elif result == "skip":
                skip += 1
            else:
                fail += 1
            self.set_progress(idx, total)
        self.set_status(f"完成：成功 {ok} 个，跳过 {skip} 个，失败 {fail} 个")
        self.log_msg(f"—— 全部完成：成功 {ok}，跳过 {skip}，失败 {fail} ——")
        def _done():
            self.converting = False
            self.convert_btn.config(state=tk.NORMAL)
            if fail == 0:
                messagebox.showinfo("完成", f"转换完成：成功 {ok} 个，跳过 {skip} 个！")
            else:
                messagebox.showwarning("完成", f"成功 {ok} 个，跳过 {skip} 个，失败 {fail} 个，详见日志。")
        self.root.after(0, _done)


def main():
    root = tk.Tk()
    # Windows 高分屏清晰度
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = TendiesPyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
