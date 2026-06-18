#!/usr/bin/env python3
"""
PDF 页面提取模块
从已有 PDF 中提取指定的页面或页面范围。
"""

import re
from pathlib import Path
from typing import List, Union

from pypdf import PdfReader, PdfWriter


def parse_page_spec(spec: str, total_pages: int) -> List[int]:
    """
    解析页面范围字符串，返回 0-based 页码列表。

    支持格式：
        "1,3,5-8"     → [0, 2, 4, 5, 6, 7]
        "1-3,7,10-12"  → [0, 1, 2, 6, 9, 10, 11]
        "1"            → [0]
        "all"          → [0, 1, ..., total_pages-1]

    Args:
        spec: 页面范围字符串（1-based）。
        total_pages: PDF 总页数。

    Returns:
        0-based 页码列表。
    """
    if spec.strip().lower() == "all":
        return list(range(total_pages))

    pages: List[int] = []
    parts = spec.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        m = re.match(r"^(\d+)(?:\s*-\s*(\d+))?$", part)
        if not m:
            raise ValueError(f"无法解析页面范围: '{part}'")

        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start

        if start < 1 or end > total_pages:
            raise ValueError(
                f"页码超出范围: {start}-{end}，"
                f"PDF 共 {total_pages} 页（1-based）"
            )

        # 转换为 0-based 并展开范围
        pages.extend(range(start - 1, end))

    # 去重并保持顺序
    seen: set[int] = set()
    unique_pages: List[int] = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            unique_pages.append(p)

    return unique_pages


def extract_pages(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    page_spec: str,
) -> int:
    """
    从 PDF 中提取指定页面并保存为新文件。

    Args:
        input_path:  输入的 PDF 文件路径。
        output_path: 输出的 PDF 文件路径。
        page_spec:   页面范围字符串，如 "1,3,5-8" 或 "all"。

    Returns:
        提取的页数。
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    reader = PdfReader(str(input_path))
    total = len(reader.pages)

    if total == 0:
        raise ValueError(f"PDF 文件为空: {input_path}")

    pages = parse_page_spec(page_spec, total)
    writer = PdfWriter()

    for idx in pages:
        writer.add_page(reader.pages[idx])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer.write(str(output_path))
    writer.close()

    return len(pages)


def print_info(input_path: Union[str, Path]) -> int:
    """打印 PDF 文件信息，返回总页数。"""
    input_path = Path(input_path)
    reader = PdfReader(str(input_path))
    total = len(reader.pages)
    print(f"文件: {input_path.name}")
    print(f"总页数: {total}")
    return total
