# File2MD — 自适应文件转 Markdown 转换器

将 DOCX、PPTX、XLSX、PDF、HTML、图片（OCR）等多种格式自动转换为 Markdown，便于与 LLM 集成。

> **注意**: 该目录下已有原来的英文 `README.md`，本文档为更简明的中文索引。\
> 原有详细英文文档仍保留在 `README.orig.md` 中。

## 调用方法

```bash
# 转换单个文件
python file2md.py document.docx

# 批量转换到指定输出目录
python file2md.py file1.pdf file2.pptx -o ./output

# 递归转换整个目录
python file2md.py ./docs -r -o ./markdown

# 限制 Excel 行数
python file2md.py data.xlsx --max-rows 100

# GUI 界面
python main_gui.py
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `input` | 输入文件或目录（支持多个） |
| `-o, --output` | 输出目录 |
| `-r, --recursive` | 递归处理子目录 |
| `--max-rows` | Excel 最大行数限制 |
| `--max-cols` | Excel 最大列数限制 |
| `--include-notes` | 包含 PPT 演讲者备注 |
| `--page-range` | PDF 页码范围（如 `1-10`） |
| `--backend` | 指定转换后端 |
| `-v, --verbose` | 详细输出 |

## 支持格式

| 格式 | 扩展名 | 转换器 |
|------|--------|--------|
| Word 文档 | .docx, .doc | `docx_converter.py` |
| PowerPoint | .pptx, .ppt | `pptx_converter.py` |
| Excel 表格 | .xlsx, .xls, .csv | `xlsx_converter.py` |
| PDF 文档 | .pdf | `pdf_converter.py` |
| HTML 网页 | .html, .htm | `html_converter.py` |
| 图片（OCR） | .jpg, .png, .tiff 等 | `image_converter.py` |
| 代码/文本 | .py, .js, .txt 等 | `text_converter.py` |

## 项目结构

```
File_2_md/
├── file2md.py             # CLI 入口 + File2MD 主类
├── main_gui.py            # GUI 界面（Tkinter）
├── converter_base.py      # 转换器基类、注册表、结果模型
├── __init__.py             # 包初始化
├── converters/             # 各格式转换器实现
│   ├── __init__.py
│   ├── docx_converter.py    # Word → Markdown
│   ├── pptx_converter.py   # PPT → Markdown
│   ├── xlsx_converter.py   # Excel → Markdown 表格
│   ├── pdf_converter.py    # PDF → Markdown
│   ├── html_converter.py   # HTML → Markdown
│   ├── image_converter.py  # 图片 OCR → Markdown
│   └── text_converter.py   # 代码/文本 → Markdown
├── examples/               # 使用示例
│   └── basic_usage.py
├── test_data/              # 测试数据
├── settings.json           # 配置文件
├── requirements.txt        # Python 依赖
├── RESEARCH.md             # 技术调研文档
└── README.md               # 本文档
```

## 架构设计

采用**策略模式** + **注册表模式**：
- `BaseConverter` — 抽象转换器基类
- `ConverterRegistry` — 转换器注册与查找
- `File2MD` — 高层统一接口（自动检测文件类型 → 匹配转换器 → 执行转换）
- 新增格式只需实现 `BaseConverter` 子类并注册

## 依赖

```bash
pip install -r requirements.txt
```

核心依赖：`python-docx`, `python-pptx`, `openpyxl`, `Pillow`, `markdownify`, `pdfplumber`

**可选依赖**（按需安装）：

```bash
# PyMuPDF（更快 PDF 解析）
pip install PyMuPDF

# OCR 支持（需额外安装 Tesseract）
pip install pytesseract
```

## Python API 调用

```python
from file2md import File2MD

converter = File2MD()

# 单文件转换
result = converter.convert("document.docx")
print(result.content)  # Markdown 文本

# 批量转换
results = converter.convert_batch(["file1.pdf", "file2.pptx"])
```
