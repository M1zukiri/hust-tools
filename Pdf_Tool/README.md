# Pdf_Tool — PDF 页面级处理工具

轻量级 PDF 页面处理工具，支持页面提取、多文件合并、图片转 PDF。

## 快速调用

```bash
# 提取指定页面
python pdf_tool.py extract input.pdf -p 1,3,5-8 -o output.pdf

# 提取所有页
python pdf_tool.py extract input.pdf -p all -o output.pdf

# 合并多个 PDF
python pdf_tool.py merge a.pdf b.pdf c.pdf -o merged.pdf

# 图片转 PDF（默认 cover 占满整页）
python pdf_tool.py convert photo1.jpg photo2.png -o album.pdf

# 图片转 PDF（contain 完整显示，留白边）
python pdf_tool.py convert photo.png -o out.pdf --fit contain

# 查看 PDF 信息
python pdf_tool.py info input.pdf
```

---

## 功能详解

### 1. extract — 页面提取

从 PDF 中提取指定的单个页面或页面范围。

```bash
python pdf_tool.py extract <input.pdf> -p <pages> [-o output.pdf]
```

**参数：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `input` | 是 | 输入 PDF 文件路径 |
| `-p, --pages` | 是 | 页面范围，支持格式：`1,3,5-8`、`1-3,7,10-12`、`all` |
| `-o, --output` | 否 | 输出路径（默认: `<输入>_extracted.pdf`） |

---

### 2. merge — PDF 合并

将多个 PDF 按指定顺序拼接为一个完整的 PDF。

```bash
python pdf_tool.py merge <file1.pdf> <file2.pdf> ... [-o output.pdf]
```

**参数：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `inputs` | 是 | 要合并的 PDF 文件列表（空格分隔） |
| `-o, --output` | 否 | 输出路径（默认: `merged.pdf`） |

---

### 3. convert — 图片转 PDF

将常见图片格式转换为 PDF，支持 `cover`（缩放占满整页）和 `contain`（完整显示）两种适配模式。

```bash
python pdf_tool.py convert <img1> <img2> ... [-o output.pdf] [--fit cover|contain] [--page-size a4|a4-landscape]
```

**参数：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `inputs` | 是 | 图片文件列表（空格分隔） |
| `-o, --output` | 否 | 输出路径（默认: `output.pdf`） |
| `--fit` | 否 | 适配模式：`cover`（裁剪占满，默认）、`contain`（完整留白） |
| `--page-size` | 否 | 页面尺寸：`a4`（纵向，默认）、`a4-landscape`（横向） |
| `--bg` | 否 | contain 模式的背景颜色（默认 `white`） |

**支持的图片格式：** jpg, jpeg, png, bmp, gif, tiff, webp

---

### 4. info — PDF 信息查看

查看 PDF 文件的页数等基本信息。

```bash
python pdf_tool.py info <input.pdf>
```

---

## 项目结构

```
Pdf_Tool/
├── pdf_tool.py          # CLI 主入口（命令解析与调度）
├── pdf_extract.py       # 页面提取模块
│   ├── parse_page_spec()    解析页面范围字符串
│   ├── extract_pages()      执行提取
│   └── print_info()         打印 PDF 信息
├── pdf_merge.py         # PDF 合并模块
│   └── merge_pdfs()         执行合并
├── pdf_convert.py       # 图片转 PDF 模块
│   ├── _cover_fit()         计算 cover 裁剪参数
│   ├── _contain_fit()       计算 contain 缩放参数
│   └── images_to_pdf()      执行转换
├── requirements.txt     # 依赖声明
└── README.md            # 本文档
```

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## Python API 调用

除 CLI 外，各模块也可作为 Python 库导入使用：

```python
from pdf_extract import extract_pages
from pdf_merge import merge_pdfs
from pdf_convert import images_to_pdf

# 提取
extract_pages("input.pdf", "output.pdf", "1,3,5-8")

# 合并
merge_pdfs(["a.pdf", "b.pdf"], "merged.pdf")

# 图片转 PDF
images_to_pdf(["img1.jpg", "img2.png"], "out.pdf", fit_mode="cover")
```
