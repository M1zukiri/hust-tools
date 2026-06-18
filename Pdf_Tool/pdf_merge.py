#!/usr/bin/env python3
"""
PDF 合并模块
按指定顺序将多个 PDF 拼接为一个完整的 PDF。
"""

from pathlib import Path
from typing import List, Union

from pypdf import PdfReader, PdfWriter


def merge_pdfs(
    input_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
) -> int:
    """
    按顺序合并多个 PDF 文件为一个。

    Args:
        input_paths:  输入的 PDF 文件路径列表（按此顺序合并）。
        output_path:  输出的 PDF 文件路径。

    Returns:
        合并后的总页数。
    """
    output_path = Path(output_path)
    writer = PdfWriter()
    total_pages = 0

    for i, path in enumerate(input_paths):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        reader = PdfReader(str(path))
        page_count = len(reader.pages)

        if page_count == 0:
            print(f"[警告] 文件为空，已跳过: {path.name}")
            continue

        for page in reader.pages:
            writer.add_page(page)

        total_pages += page_count
        print(f"  [{i+1}/{len(input_paths)}] {path.name}  ({page_count} 页)")

    if total_pages == 0:
        raise ValueError("没有有效的 PDF 页面可供合并。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer.write(str(output_path))
    writer.close()

    print(f"\n[OK] 合并完成: 共 {total_pages} 页 -> {output_path.name}")
    return total_pages
