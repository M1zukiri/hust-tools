#!/usr/bin/env python3
import argparse
import time
import traceback
from pathlib import Path
import image_converter
import audio_converter
import video_converter

from base_converter import CONVERTERS


def find_converter(src_ext: str, dst_ext: str):
    src_ext, dst_ext = src_ext.lower(), dst_ext.lower()
    for cls in CONVERTERS:
        if cls.can_handle(src_ext, dst_ext):
            return cls
    return None

def convert_all(src_ext: str, dst_ext: str, folder: Path):
    total = success = failed = 0
    start = time.time()

    out_dir = folder / f"converted_{int(start)}"
    out_dir.mkdir(exist_ok=True)

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() == f".{src_ext}":
            total += 1
            dst_file = out_dir / f"{file.stem}.{dst_ext}"
            cls = find_converter(src_ext, dst_ext)
            try:
                cls(file, dst_file).convert()
                success += 1
                print(f"[成功] {file.name} -> {dst_file.name}")
            except Exception as e:
                failed += 1
                print(f"[失败] {file.name} 原因：{e}")
                traceback.print_exc()

    elapsed = time.time() - start
    print("========== 处理完成 ==========")
    print(f"总文件数：{total}")
    print(f"成功：{success}")
    print(f"失败：{failed}")
    print(f"耗时：{elapsed:.2f} 秒")
    print(f"输出目录：{out_dir}")

def main():
    parser = argparse.ArgumentParser(description="万能格式转换器")
    parser.add_argument("src", help="源后缀，如 mp4")
    parser.add_argument("dst", help="目标后缀，如 mp3")
    parser.add_argument("--dir", default=".", help="待处理目录，默认当前目录")
    args = parser.parse_args()

    print([cls.__name__ for cls in CONVERTERS])
    folder = Path(args.dir).expanduser().resolve()
    if not folder.is_dir():
        print(f"目录不存在：{folder}")
        exit(2)

    if find_converter(args.src, args.dst) is None:
        print(f"不支持 {args.src} -> {args.dst}")
        exit(3)

    convert_all(args.src, args.dst, folder)

if __name__ == "__main__":
    main()