# Png_2_Gif — PNG 序列帧转 GIF

将水平拼接的精灵图（spritesheet）自动分割为多帧，合成 GIF 动画。

## 调用方法

1. 修改 `Png_2_Gif.py` 中的输入文件路径：
   ```python
   big = Image.open('input.png')   # 改为你的精灵图路径
   ```

2. 运行：
   ```bash
   python Png_2_Gif.py
   ```

3. 输出：`output.gif`

## 工作原理

假设输入图片尺寸为 **6000×300**：
- 水平方向分割为 20 帧，每帧宽度 = 6000 ÷ 20 = **300px**
- 每帧高度保持原图高度 **300px**
- 以 30ms 间隔循环播放

如需调整帧数和速度，修改代码中的常量：
```python
frame_w = W // 20        # 20 → 分割帧数
duration=30              # 30 → 每帧显示毫秒数
loop=0                   # 0 → 无限循环
```

## 项目结构

```
Png_2_Gif/
├── Png_2_Gif.py    # 主程序（约 20 行）
├── input.png       # 输入精灵图
├── output.gif      # 输出 GIF（运行后生成）
└── README.md       # 本文档
```

## 依赖

```bash
pip install Pillow numpy
```
