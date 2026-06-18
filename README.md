# Python_Tools 工具集索引

> 日常 Python 小工具集合。每个工具目录下均有详细文档。

---

## 快速调用（一条命令）

| # | 工具 | 一句话用途 | 调用命令 |
|---|------|-----------|----------|
| 1 | **Eye_map** | 生成正弦波眼图 | `python eyemap.py` |
| 2 | **File_2_md** | 各类文件转 Markdown | `python file2md.py <文件路径>` |
| 3 | **File_converter** | 图片/音频/视频格式互转 | `python converter_cli.py <源后缀> <目标后缀>` |
| 4 | **Gal_Extractor** | 提取 GalGame 封包资源 | `dotnet run`（需 .NET SDK） |
| 5 | **Location** | 地图关键词模糊定位 | `python main.py`（需高德 API Key） |
| 6 | **Lrc_match** | 歌词修复/格式转换/乱码修复 | `python main.py` |
| 7 | **Png_2_Gif** | 水平精灵图分割为 GIF 动画 | 修改 `Png_2_Gif.py` 中 input.png 路径后运行 |
| 8 | **Tree_maker** | 生成目录树结构文本 | `python tree_maker.py -d <深度>` |
| 9 | **Pdf_Tool** | PDF 页面提取/合并/图片转 PDF | `python pdf_tool.py <extract|merge|convert> ...` |

---

## 详细文档

> 每个工具目录内均有 `README.md`，包含完整的调用方法、参数说明、项目结构及使用示例。
> 点击下方目录名进入对应工具的详细文档：

- [Eye_map/](./Eye_map/README.md) — 眼图生成
- [File_2_md/](./File_2_md/README.md) — 文件转 Markdown
- [File_converter/](./File_converter/README.md) — 万能格式转换器
- [Gal_Extractor/](./Gal_Extractor/README.md) — GalGame 资源提取
- [Location/](./Location/README.md) — 模糊定位引擎
- [Lrc_match/](./Lrc_match/README.md) — 歌词全能管家
- [Png_2_Gif/](./Png_2_Gif/README.md) — PNG 序列帧转 GIF
- [Tree_maker/](./Tree_maker/README.md) — 目录树生成器
- [Pdf_Tool/](./Pdf_Tool/README.md) — PDF 页面处理工具（提取/合并/图片转 PDF）
