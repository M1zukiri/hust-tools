# -*- coding: utf-8 -*-
"""
ncm2music.py — 网易云音乐 .ncm 文件转换器（零依赖，Python 3.6+）

用法：
  1. 直接双击运行（无参数）→ 打开图形界面，添加文件后点击“开始转换”。
  2. 命令行：python ncm2music.py <文件或文件夹...> [-o 输出目录]
  3. 也可以把 .ncm 文件直接拖到本脚本图标上进行转换。

输出为原始的 mp3 / flac 文件，可在任意播放器中播放。
"""

import base64
import binascii
import json
import os
import struct
import sys

# ============================================================
# 纯 Python AES-128（仅用于解密几 KB 的密钥/元数据块，速度足够）
# ============================================================

_SBOX = (
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
)

_INV_SBOX = (
    0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
    0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
    0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
    0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
    0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
    0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
    0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
    0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
    0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
    0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
    0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
    0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
    0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
    0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
    0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
    0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
)

_RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


def _gmul(a, b):
    """GF(2^8) 乘法"""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


class _AES128:
    """AES-128 ECB 解密（状态按列优先排列，state[4*c + r]）"""

    def __init__(self, key):
        assert len(key) == 16
        w = [list(key[i * 4:(i + 1) * 4]) for i in range(4)]
        for i in range(4, 44):
            temp = list(w[i - 1])
            if i % 4 == 0:
                temp = temp[1:] + temp[:1]                      # RotWord
                temp = [_SBOX[b] for b in temp]                 # SubWord
                temp[0] ^= _RCON[i // 4 - 1]
            w.append([a ^ b for a, b in zip(w[i - 4], temp)])
        self._w = w

    def _add_round_key(self, s, rnd):
        for c in range(4):
            for r in range(4):
                s[4 * c + r] ^= self._w[rnd * 4 + c][r]

    @staticmethod
    def _inv_shift_rows(s):
        for r in range(1, 4):
            row = [s[4 * c + r] for c in range(4)]
            for c in range(4):
                s[4 * c + r] = row[(c - r) % 4]

    @staticmethod
    def _inv_mix_columns(s):
        for c in range(4):
            a0, a1, a2, a3 = s[4 * c], s[4 * c + 1], s[4 * c + 2], s[4 * c + 3]
            s[4 * c]     = _gmul(a0, 14) ^ _gmul(a1, 11) ^ _gmul(a2, 13) ^ _gmul(a3, 9)
            s[4 * c + 1] = _gmul(a0, 9)  ^ _gmul(a1, 14) ^ _gmul(a2, 11) ^ _gmul(a3, 13)
            s[4 * c + 2] = _gmul(a0, 13) ^ _gmul(a1, 9)  ^ _gmul(a2, 14) ^ _gmul(a3, 11)
            s[4 * c + 3] = _gmul(a0, 11) ^ _gmul(a1, 13) ^ _gmul(a2, 9)  ^ _gmul(a3, 14)

    def decrypt_block(self, block):
        s = list(block)
        self._add_round_key(s, 10)
        for rnd in range(9, 0, -1):
            self._inv_shift_rows(s)
            s = [_INV_SBOX[b] for b in s]
            self._add_round_key(s, rnd)
            self._inv_mix_columns(s)
        self._inv_shift_rows(s)
        s = [_INV_SBOX[b] for b in s]
        self._add_round_key(s, 0)
        return bytes(s)


def _aes_ecb_decrypt(key, data):
    aes = _AES128(key)
    out = b"".join(aes.decrypt_block(data[i:i + 16]) for i in range(0, len(data), 16))
    pad = out[-1]
    if 1 <= pad <= 16:
        out = out[:-pad]
    return out


# ============================================================
# NCM 解密核心
# ============================================================

_CORE_KEY = bytes((0x68, 0x7A, 0x48, 0x52, 0x41, 0x6D, 0x73, 0x6F,
                   0x35, 0x6B, 0x49, 0x6E, 0x62, 0x61, 0x78, 0x57))
_META_KEY = bytes((0x23, 0x31, 0x34, 0x6C, 0x6A, 0x6B, 0x5F, 0x21,
                   0x5C, 0x5D, 0x26, 0x30, 0x55, 0x3C, 0x27, 0x28))

NCM_MAGIC = b"CTENFDAM"


class NcmError(Exception):
    pass


def _build_key_box(key):
    box = list(range(256))
    j = 0
    n = len(key)
    for i in range(256):
        j = (j + box[i] + key[i % n]) & 0xFF
        box[i], box[j] = box[j], box[i]
    # 生成 256 字节周期的密钥流模板（音频数据按此循环异或）
    ks = bytes(box[(box[t] + box[(box[t] + t) & 0xFF]) & 0xFF]
               for t in [((i + 1) & 0xFF) for i in range(256)])
    return ks


def _xor_stream(data, ks):
    """用周期为 256 的密钥流对 data 异或（大整数运算，速度快）"""
    n = len(data)
    if n == 0:
        return data
    stream = ks * (n // 256) + ks[:n % 256]
    return (int.from_bytes(data, "big") ^ int.from_bytes(stream, "big")).to_bytes(n, "big")


def _parse_meta(meta_bytes):
    meta_bytes = bytes(b ^ 0x63 for b in meta_bytes)
    if meta_bytes[:22] == b"163 key(Don't modify):":
        meta_bytes = meta_bytes[22:]
    try:
        encrypted = base64.b64decode(meta_bytes)
    except binascii.Error:
        return {}
    plain = _aes_ecb_decrypt(_META_KEY, encrypted)
    if plain[:6] == b"music:":
        plain = plain[6:]
    try:
        meta = json.loads(plain.decode("utf-8", errors="replace"))
    except ValueError:
        return {}
    if isinstance(meta, dict) and "music" in meta and isinstance(meta["music"], dict):
        meta = meta["music"]
    return meta if isinstance(meta, dict) else {}


def read_ncm(path):
    """解析 ncm 文件，返回 (音频数据 bytes, 元数据 dict)"""
    with open(path, "rb") as f:
        if f.read(8) != NCM_MAGIC:
            raise NcmError("不是有效的 ncm 文件（文件头不匹配）")
        f.seek(2, os.SEEK_CUR)

        # --- 密钥块 ---
        key_len = struct.unpack("<I", f.read(4))[0]
        key_data = bytes(b ^ 0x64 for b in f.read(key_len))
        key = _aes_ecb_decrypt(_CORE_KEY, key_data)
        if key[:17] == b"neteasecloudmusic":
            key = key[17:]
        if not key:
            raise NcmError("解密密钥失败")
        ks = _build_key_box(key)

        # --- 元数据块 ---
        meta = {}
        meta_len = struct.unpack("<I", f.read(4))[0]
        if meta_len:
            meta = _parse_meta(f.read(meta_len))

        # --- CRC + 间隔 + 封面 ---
        f.seek(4 + 5, os.SEEK_CUR)
        cover_len = struct.unpack("<I", f.read(4))[0]
        if cover_len:
            f.seek(cover_len, os.SEEK_CUR)

        # --- 音频数据（分块异或，控制内存占用） ---
        chunks = []
        while True:
            chunk = f.read(16 * 1024 * 1024)  # 16 MB，且为 256 的整数倍
            if not chunk:
                break
            chunks.append(_xor_stream(chunk, ks))
        return b"".join(chunks), meta


_INVALID_CHARS = '\\/:*?"<>|'


def _sanitize(name):
    return "".join("_" if c in _INVALID_CHARS else c for c in name).strip() or "unknown"


def detect_format(audio, meta):
    if audio[:4] == b"fLaC":
        return "flac"
    if audio[:3] == b"ID3" or (audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0):
        return "mp3"
    fmt = str(meta.get("format", "")).lower()
    return fmt if fmt in ("mp3", "flac") else "mp3"


def make_output_name(meta, fallback, fmt):
    title = meta.get("musicName") or meta.get("name") or fallback
    artists = meta.get("artist") or []
    names = [a[0] for a in artists if isinstance(a, (list, tuple)) and a]
    artist = " / ".join(names)
    base = f"{artist} - {title}" if artist else str(title)
    return _sanitize(base) + "." + fmt


def _unique_path(out_path):
    if not os.path.exists(out_path):
        return out_path
    stem, ext = os.path.splitext(out_path)
    i = 1
    while os.path.exists(f"{stem} ({i}){ext}"):
        i += 1
    return f"{stem} ({i}){ext}"


def convert_file(src, out_dir=None):
    """转换单个 ncm 文件，返回输出文件路径"""
    audio, meta = read_ncm(src)
    if not audio:
        raise NcmError("解密结果为空")
    fmt = detect_format(audio, meta)
    name = make_output_name(meta, os.path.splitext(os.path.basename(src))[0], fmt)
    out_dir = out_dir or os.path.dirname(os.path.abspath(src))
    os.makedirs(out_dir, exist_ok=True)
    out_path = _unique_path(os.path.join(out_dir, name))
    with open(out_path, "wb") as f:
        f.write(audio)
    return out_path


def collect_ncm_files(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                files.extend(os.path.join(root, n) for n in names
                             if n.lower().endswith(".ncm"))
        elif p.lower().endswith(".ncm") and os.path.isfile(p):
            files.append(p)
    return files


# ============================================================
# 图形界面
# ============================================================

def _enable_drop(root, on_files):
    """让窗口支持拖入文件/文件夹（Win32 DragAcceptFiles + WM_DROPFILES，仅 Windows）。

    对整个控件树子类化窗口过程，因此拖到列表框、按钮等任何位置都有效。
    注意：窗口过程回调里不能直接调用 tkinter（会导致解释器崩溃），
    拖入的路径先放入队列，由 root.after 轮询器取出后交给 on_files 处理。
    任何一步失败都会静默降级为“不支持拖拽”，不影响其余功能。
    """
    try:
        import ctypes
        from ctypes import wintypes

        GWLP_WNDPROC = -4
        WM_DROPFILES = 0x0233
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT,
                                           ctypes.c_size_t, ctypes.c_ssize_t]
        user32.CallWindowProcW.restype = ctypes.c_ssize_t
        shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wintypes.UINT,
                                           wintypes.LPWSTR, wintypes.UINT]
        shell32.DragQueryFileW.restype = wintypes.UINT
        shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
        shell32.DragFinish.argtypes = [ctypes.c_void_p]

        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT,
                                     ctypes.c_size_t, ctypes.c_ssize_t)
        keep_alive = []  # 防止回调对象被垃圾回收
        pending = []     # 拖入的路径队列（由轮询器消费）

        def handle_drop(hdrop):
            count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
            for i in range(count):
                n = shell32.DragQueryFileW(hdrop, i, None, 0)
                buf = ctypes.create_unicode_buffer(n + 1)
                shell32.DragQueryFileW(hdrop, i, buf, n + 1)
                pending.append(buf.value)
            shell32.DragFinish(hdrop)

        def subclass(hwnd):
            old_proc = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)

            def proc(h, msg, wp, lp, _old=old_proc):
                if msg == WM_DROPFILES:
                    handle_drop(wp)
                    return 0
                return user32.CallWindowProcW(_old, h, msg, wp, lp)

            cb = WNDPROC(proc)
            keep_alive.append(cb)
            user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(cb, ctypes.c_void_p))
            shell32.DragAcceptFiles(hwnd, True)

        def walk(widget):
            yield widget
            for child in widget.winfo_children():
                yield from walk(child)

        for widget in walk(root):
            subclass(widget.winfo_id())

        def poll():
            if pending:
                on_files(list(pending))
                pending.clear()
            root.after(100, poll)

        poll()
    except Exception:  # noqa: BLE001
        pass


def run_gui():
    import threading
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("NCM 音乐转换器")
    root.geometry("640x430")

    file_list = tk.Listbox(root, selectmode=tk.EXTENDED)
    file_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

    out_var = tk.StringVar(value="")  # 空 = 输出到源文件同目录

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill=tk.X, padx=10)

    def add_files():
        for p in filedialog.askopenfilenames(
                title="选择 ncm 文件", filetypes=[("NCM 文件", "*.ncm")]):
            if p not in file_list.get(0, tk.END):
                file_list.insert(tk.END, p)

    def add_folder():
        d = filedialog.askdirectory(title="选择包含 ncm 文件的文件夹")
        if d:
            for p in collect_ncm_files([d]):
                if p not in file_list.get(0, tk.END):
                    file_list.insert(tk.END, p)

    def remove_selected():
        for i in reversed(file_list.curselection()):
            file_list.delete(i)

    def pick_out_dir():
        d = filedialog.askdirectory(title="选择输出目录（取消则输出到源文件同目录）")
        if d:
            out_var.set(d)

    tk.Button(btn_frame, text="添加文件", command=add_files).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="添加文件夹", command=add_folder).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="移除选中", command=remove_selected).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="输出目录…", command=pick_out_dir).pack(side=tk.LEFT, padx=5)
    tk.Label(btn_frame, textvariable=out_var, fg="gray").pack(side=tk.LEFT)

    progress = ttk.Progressbar(root, mode="determinate")
    progress.pack(fill=tk.X, padx=10, pady=5)
    status = tk.Label(
        root, anchor="w",
        text="可把 ncm 文件或文件夹直接拖入窗口（留空输出目录 = 与源文件同目录）")
    status.pack(fill=tk.X, padx=10)

    convert_btn = tk.Button(root, text="开始转换", font=("", 11, "bold"))
    convert_btn.pack(pady=8)

    def worker(files, out_dir):
        ok, fail = 0, 0
        for i, path in enumerate(files, 1):
            root.after(0, status.config, {"text": f"[{i}/{len(files)}] {os.path.basename(path)}"})
            try:
                out = convert_file(path, out_dir)
                ok += 1
                root.after(0, status.config,
                           {"text": f"[{i}/{len(files)}] 完成 → {os.path.basename(out)}"})
            except Exception as e:  # noqa: BLE001
                fail += 1
                root.after(0, status.config,
                           {"text": f"[{i}/{len(files)}] 失败：{os.path.basename(path)}（{e}）"})
            root.after(0, progress.config, {"value": i})
        root.after(0, lambda: (
            messagebox.showinfo("转换完成", f"成功 {ok} 个，失败 {fail} 个。"),
            convert_btn.config(state=tk.NORMAL)))

    def start():
        files = list(file_list.get(0, tk.END))
        if not files:
            messagebox.showwarning("提示", "请先添加 ncm 文件")
            return
        progress.config(maximum=len(files), value=0)
        convert_btn.config(state=tk.DISABLED)
        threading.Thread(target=worker, args=(files, out_var.get() or None),
                         daemon=True).start()

    convert_btn.config(command=start)

    def on_dropped(paths):
        added = 0
        for p in collect_ncm_files(paths):
            if p not in file_list.get(0, tk.END):
                file_list.insert(tk.END, p)
                added += 1
        status.config(text=f"已添加 {added} 个 ncm 文件" if added
                      else "拖入的内容中没有 ncm 文件")

    _enable_drop(root, on_dropped)
    root.mainloop()


# ============================================================
# 命令行入口
# ============================================================

def main(argv):
    args = list(argv)
    out_dir = None
    if "-o" in args:
        i = args.index("-o")
        if i + 1 >= len(args):
            print("错误：-o 后需要输出目录")
            return 2
        out_dir = args[i + 1]
        del args[i:i + 2]

    if not args:
        run_gui()
        return 0

    files = collect_ncm_files(args)
    if not files:
        print("没有找到 .ncm 文件")
        return 1

    ok = fail = 0
    for i, path in enumerate(files, 1):
        try:
            out = convert_file(path, out_dir)
            ok += 1
            print(f"[{i}/{len(files)}] OK  {os.path.basename(path)}  ->  {out}")
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"[{i}/{len(files)}] 失败  {os.path.basename(path)}: {e}")
    print(f"完成：成功 {ok} 个，失败 {fail} 个")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
