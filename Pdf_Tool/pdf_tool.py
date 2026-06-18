#!/usr/bin/env python3
"""
Pdf_Tool — PDF 页面级处理工具

功能：
  extract   从 PDF 中提取指定页面
  merge     合并多个 PDF
  convert   将图片转换为 PDF

用法：
  python pdf_tool.py extract   <input.pdf>  -p <pages>  [-o output.pdf]
  python pdf_tool.py merge     <file1.pdf> <file2.pdf> ...  [-o output.pdf]
  python pdf_tool.py convert   <img1> <img2> ...  [-o output.pdf] [--fit cover|contain]
  python pdf_tool.py info      <input.pdf>
"""

import argparse
import sys
from pathlib import Path

from pdf_extract import extract_pages, print_info
from pdf_merge import merge_pdfs
from pdf_convert import images_to_pdf, A4_PORTRAIT, A4_LANDSCAPE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf_tool",
        description="PDF 页面级处理工具 — 提取、合并、图片转 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取第 1,3,5-8 页
  python pdf_tool.py extract input.pdf -p 1,3,5-8 -o output.pdf

  # 提取所有页
  python pdf_tool.py extract input.pdf -p all -o output.pdf

  # 合并多个 PDF
  python pdf_tool.py merge a.pdf b.pdf c.pdf -o merged.pdf

  # 图片转 PDF（默认 cover 模式，占满整页）
  python pdf_tool.py convert photo1.jpg photo2.png -o album.pdf

  # 图片转 PDF（contain 模式，完整显示）
  python pdf_tool.py convert photo.jpg -o out.pdf --fit contain

  # 查看 PDF 信息
  python pdf_tool.py info input.pdf
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- extract ---
    p_extract = sub.add_parser("extract", help="从 PDF 中提取指定页面")
    p_extract.add_argument("input", type=str, help="输入的 PDF 文件")
    p_extract.add_argument("-p", "--pages", required=True, type=str,
                           help="页面范围，如 '1,3,5-8' 或 'all'")
    p_extract.add_argument("-o", "--output", type=str, default=None,
                           help="输出 PDF 文件路径（默认: <输入>_extracted.pdf）")

    # --- merge ---
    p_merge = sub.add_parser("merge", help="合并多个 PDF")
    p_merge.add_argument("inputs", type=str, nargs="+",
                         help="要合并的 PDF 文件列表（按顺序）")
    p_merge.add_argument("-o", "--output", type=str, default=None,
                         help="输出 PDF 文件路径（默认: merged.pdf）")

    # --- convert ---
    p_convert = sub.add_parser("convert", help="将图片转换为 PDF")
    p_convert.add_argument("inputs", type=str, nargs="+",
                           help="图片文件路径列表")
    p_convert.add_argument("-o", "--output", type=str, default=None,
                           help="输出 PDF 文件路径（默认: output.pdf）")
    p_convert.add_argument("--fit", choices=["cover", "contain"], default="cover",
                           help="图片适配模式：cover 占满（裁剪），contain 完整（留白）")
    p_convert.add_argument("--page-size", choices=["a4", "a4-landscape"], default="a4",
                           help="页面尺寸（默认 a4 纵向）")
    p_convert.add_argument("--bg", default="white",
                           help="contain 模式的背景颜色（默认 white）")

    # --- info ---
    p_info = sub.add_parser("info", help="查看 PDF 文件信息")
    p_info.add_argument("input", type=str, help="输入的 PDF 文件")

    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "extract":
        src = Path(args.input)
        output = args.output or str(src.with_stem(src.stem + "_extracted"))
        count = extract_pages(src, output, args.pages)
        print(f"[OK] 已提取 {count} 页 -> {output}")

    elif args.command == "merge":
        output = args.output or "merged.pdf"
        merge_pdfs(args.inputs, output)

    elif args.command == "convert":
        output = args.output or "output.pdf"
        page_size = A4_LANDSCAPE if args.page_size == "a4-landscape" else A4_PORTRAIT
        images_to_pdf(
            args.inputs,
            output,
            page_size=page_size,
            fit_mode=args.fit,
            bg_color=args.bg,
        )

    elif args.command == "info":
        print_info(args.input)


if __name__ == "__main__":
    main()
