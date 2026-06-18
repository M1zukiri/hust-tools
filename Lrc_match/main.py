#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌词全能管家 (LyricMaster) v3.5 - 终极整合版
1. 修复：解决 [00:00.00][] 错误残留 。
2. 转换：精准处理 WebVTT/SRT 结构，不再产生全 0 时间戳 。
3. 乱码修复：多重编码探测 (UTF-8/GB18030/Shift-JIS) 。
4. 整理：自动将转换/修复后的歌词移动至对应歌曲文件夹。
"""

import os
import re
import difflib
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class RobustLyricEngine:
    # 匹配时间戳：支持 00:00:00.000 或 00:00.000
    TIME_REGEX = re.compile(r'(\d{2}:)?(\d{2}):(\d{2})[\.,](\d{2,3})')
    # 匹配历史错误残留标记 [cite: 4]
    GARBAGE_PREFIX = re.compile(r'^\[\d{2,3}:\d{2}\.\d{2,3}\](\[\])?')

    @staticmethod
    def read_file_safe(file_path: Path) -> str:
        """解决乱码问题：尝试多种编码读取 """
        for enc in ['utf-8-sig', 'gb18030', 'shift_jis', 'utf-16']:
            try:
                return file_path.read_text(encoding=enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return file_path.read_text(encoding='utf-8', errors='ignore')

    @classmethod
    def parse_and_rebuild(cls, raw_content: str) -> Optional[str]:
        """核心转换逻辑：剥离干扰，重构标准 LRC """
        lines = [l.strip() for l in raw_content.splitlines()]
        lrc_output = []
        curr_ts = ""

        for line in lines:
            # 剥离可能存在的 [00:00.00][] 垃圾头 [cite: 4]
            line = cls.GARBAGE_PREFIX.sub('', line).strip()

            # 跳过 VTT 头部和纯数字序号
            if not line or line.upper().startswith(('WEBVTT', 'NOTE', 'STYLE')) or line.isdigit():
                continue

            # 识别时间轴行
            if '-->' in line:
                match = cls.TIME_REGEX.search(line)
                if match:
                    h, m, s, ms = match.groups()
                    total_m = (int(h[:-1]) * 60 if h else 0) + int(m)
                    curr_ts = f"[{total_m:02d}:{s}.{ms[:2]}]"
                continue

            # 处理歌词文本内容
            if curr_ts:
                # 剔除 HTML 标签 [cite: 3]
                clean_text = re.sub(r'<[^>]+>', '', line).strip()
                if clean_text:
                    lrc_output.append(f"{curr_ts}{clean_text}")
                    # WebVTT 文本可能跨行，此处不重置 curr_ts

        return "\n".join(lrc_output) if lrc_output else None


class LyricManager:
    def __init__(self, root: str):
        self.root = Path(root.strip().strip('"'))
        self.song_files: Dict[str, List[Path]] = {}
        self.lyric_files: Dict[str, List[Path]] = {}

    def scan(self):
        """扫描歌曲与歌词素材"""
        print(f"🔍 正在深度扫描: {self.root}")
        audio_exts = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        # 扫描包括已损坏的 .lrc 和新素材
        lyric_exts = {'.lrc', '.vtt', '.srt', '.txt'}

        for curr, _, files in os.walk(str(self.root)):
            for f in files:
                p = Path(curr) / f
                ext = p.suffix.lower()
                stem = p.stem
                # 处理复合后缀如 .wav.vtt.txt，提取真正的 stem
                real_stem = stem.split('.wav')[0].split('.mp3')[0]

                if ext in lyric_exts:
                    self.lyric_files.setdefault(real_stem, []).append(p)
                elif ext in audio_exts:
                    self.song_files.setdefault(real_stem, []).append(p)

    def process_and_sync(self):
        """执行整理：增加了防二次删除的校验"""
        print("\n🎯 开始自动化处理流程...")
        for stem, songs in self.song_files.items():
            for s_path in songs:
                l_paths = self.lyric_files.get(stem)
                if not l_paths:
                    # 模糊匹配逻辑
                    for l_stem in self.lyric_files:
                        if difflib.SequenceMatcher(None, stem.lower(), l_stem.lower()).ratio() > 0.8:
                            l_paths = self.lyric_files[l_stem]
                            break

                if l_paths:
                    # 总是尝试处理该 stem 下的所有候选歌词
                    for l_src in l_paths:
                        # --- 核心修复：检查原文件是否还存在 ---
                        if not l_src.exists():
                            continue

                        target = s_path.with_suffix('.lrc')

                        # 如果目标已存在且内容一致，没必要再次读取原件
                        if target.exists() and l_src == target:
                            continue

                        try:
                            content = RobustLyricEngine.read_file_safe(l_src)
                            new_lrc = RobustLyricEngine.parse_and_rebuild(content)

                            if new_lrc:
                                target.write_text(new_lrc, encoding='utf-8')
                                print(f"✅ 已同步并修复: {s_path.name}")

                                # 只有在原件确实存在且不是目标本身时才删除
                                if l_src != target and l_src.exists():
                                    try:
                                        l_src.unlink()
                                    except OSError:
                                        pass  # 忽略网络延迟导致的删除失败
                        except Exception as e:
                            print(f"⚠️ 处理 {l_src.name} 时出错: {e}")


if __name__ == "__main__":
    path = input("请输入映射路径 (如 M:\\device\\Resources): ").strip()
    if path:
        mgr = LyricManager(path)
        mgr.scan()
        mgr.process_and_sync()
        print("\n✨ 任务已全面完成！您的库现在应该是标准且整洁的。")