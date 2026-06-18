#!/usr/bin/env python3
"""
图片转 PDF 模块
将常见图片格式转换为 PDF，图片缩放占满一整页。
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image


# A4 页面尺寸（磅），1 英寸 = 72 磅
A4_PORTRAIT: Tuple[float, float] = (595.28, 841.89)
A4_LANDSCAPE: Tuple[float, float] = (841.89, 595.28)


def _cover_fit(
    img_width: int,
    img_height: int,
    page_width: float,
    page_height: float,
) -> Tuple[float, float, float, float, float]:
    """
    计算 Cover 模式下的缩放和裁剪参数。
    图片缩放至完全覆盖页面（超出部分裁剪），不留空白。

    Returns:
        (scale, dw, dh, sx, sy)
        - scale: 缩放比例
        - dw: 缩放后图片宽度（磅）
        - dh: 缩放后图片高度（磅）
        - sx: 源图片裁剪起始 x
        - sy: 源图片裁剪起始 y
    """
    # 计算宽高比
    img_ratio = img_width / img_height
    page_ratio = page_width / page_height

    if img_ratio > page_ratio:
        # 图片更宽：按高度缩放，宽度裁剪
        scale = page_height / img_height
        dw = img_width * scale
        dh = page_height
        sx = (dw - page_width) / 2 / scale  # 水平居中裁剪（像素）
        sy = 0
    else:
        # 图片更高（或等比例）：按宽度缩放，高度裁剪
        scale = page_width / img_width
        dw = page_width
        dh = img_height * scale
        sx = 0
        sy = (dh - page_height) / 2 / scale  # 垂直居中裁剪（像素）

    return scale, dw, dh, sx, sy


def _contain_fit(
    img_width: int,
    img_height: int,
    page_width: float,
    page_height: float,
) -> Tuple[float, float, float, float]:
    """
    计算 Contain 模式下的缩放和居中参数。
    图片完整显示在页面内，保持宽高比，可能留有白边。

    Returns:
        (scale, dw, dh, paste_x, paste_y)
    """
    scale = min(page_width / img_width, page_height / img_height)
    dw = img_width * scale
    dh = img_height * scale
    paste_x = (page_width - dw) / 2
    paste_y = (page_height - dh) / 2
    return scale, dw, dh, paste_x, paste_y


def images_to_pdf(
    image_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    page_size: Tuple[float, float] = A4_PORTRAIT,
    fit_mode: str = "cover",
    bg_color: str = "white",
) -> int:
    """
    将多张图片按顺序转换为 PDF，每张图片占一页。

    Args:
        image_paths: 图片文件路径列表。
        output_path: 输出 PDF 文件路径。
        page_size:   页面尺寸（磅），默认 A4 纵向 (595.28, 841.89)。
        fit_mode:    "cover" 缩放占满整页（裁剪超出部分）；
                     "contain" 完整显示（可能留白边）。
        bg_color:    背景颜色，仅 contain 模式生效。

    Returns:
        生成的页数。

    Raises:
        FileNotFoundError: 图片文件不存在。
        ValueError:        图片格式不支持。
    """
    output_path = Path(output_path)
    page_width, page_height = page_size
    images: List[Image.Image] = []

    supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

    for img_path in image_paths:
        img_path = Path(img_path)
        if not img_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {img_path}")

        ext = img_path.suffix.lower()
        if ext not in supported_formats:
            raise ValueError(f"不支持的图片格式: {ext}，支持: {supported_formats}")

        img = Image.open(img_path).convert("RGB")
        w, h = img.size

        if fit_mode == "cover":
            scale, dw, dh, sx, sy = _cover_fit(w, h, page_width, page_height)
            # 裁剪源图片
            crop_box = (
                int(sx),
                int(sy),
                int(sx + page_width / scale),
                int(sy + page_height / scale),
            )
            cropped = img.crop(crop_box)
            # 缩放到页面尺寸
            resized = cropped.resize((int(page_width), int(page_height)), Image.LANCZOS)
            images.append(resized)

        elif fit_mode == "contain":
            scale, dw, dh, px, py = _contain_fit(w, h, page_width, page_height)
            resized = img.resize((int(dw), int(dh)), Image.LANCZOS)
            canvas = Image.new("RGB", (int(page_width), int(page_height)), bg_color)
            canvas.paste(resized, (int(px), int(py)))
            images.append(canvas)

        else:
            raise ValueError(f"不支持的适配模式: '{fit_mode}'，可选: cover, contain")

        print(f"  [OK] {img_path.name}  ({w}x{h} -> {int(page_width)}x{int(page_height)})")

    if not images:
        raise ValueError("没有有效的图片可供转换。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        str(output_path),
        save_all=True,
        append_images=images[1:],
        resolution=72.0,
    )

    print(f"\n[OK] 转换完成: 共 {len(images)} 页 -> {output_path.name}")
    return len(images)
