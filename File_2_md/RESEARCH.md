# 文件转Markdown方案研究报告

## 概述

本报告研究了当前常见的文件格式转Markdown方案，为File2MD项目的设计提供参考。

## 研究背景

### 问题陈述

- LLM原生支持的知识库主要为Markdown格式
- 工作中常用文件格式为.doc(x)、.ppt(x)、.pdf等
- 格式不匹配导致工作文件难以直接导入LLM

### 核心需求

1. **格式保留** - 保留文档结构（标题、列表、表格等）
2. **LLM就绪** - 输出适合LLM处理的格式
3. **批量处理** - 支持大量文件自动化转换
4. **可扩展性** - 易于添加新的格式支持

## 现有方案分析

### 1. 微软 MarkItDown

**简介**: 微软开源的文档转Markdown工具，专为LLM工作流设计

**支持格式**:
- PDF, PowerPoint, Word, Excel
- 图片（带OCR）, HTML, 音频转录
- CSV, JSON, XML等文本格式

**特点**:
- 专为LLM输入优化
- 内存处理，不创建临时文件
- 支持插件扩展
- 提供MCP服务器集成

**优点**:
- 简洁的API设计
- 良好的格式保留
- 活跃的社区支持

**缺点**:
- 复杂布局处理一般
- 依赖较多

**参考**: https://github.com/microsoft/markitdown

---

### 2. Pandoc

**简介**: 通用文档转换工具，支持多种格式互转

**支持格式**:
- 输入: Markdown, HTML, DOCX, ODT, EPUB等
- 输出: Markdown, HTML, PDF, DOCX等

**Python接口**: pypandoc

```python
import pypandoc
output = pypandoc.convert_file('document.docx', 'md')
```

**特点**:
- 高度可定制
- 模板系统
- 过滤器支持

**优点**:
- 功能强大
- 格式支持广泛
- 高质量输出

**缺点**:
- 需要安装pandoc二进制
- 配置复杂
- 速度较慢

**参考**: https://pandoc.org/

---

### 3. IBM Docling

**简介**: IBM研究院开源的文档解析框架

**支持格式**:
- PDF, DOCX, PPTX, XLSX, HTML
- 图片, 音频

**特点**:
- 布局理解（标题、段落、表格、图表）
- 语义分组
- 多种导出格式（Markdown, HTML, JSON, DocTags）
- 本地执行（隐私保护）
- OCR支持

**Granite-Docling-258M**:
- 258M参数的VLM模型
- 端到端文档转换
- 保留布局、表格、公式、代码

**优点**:
- 学术研究级精度
- 科学文档处理优秀
- 表格和公式识别准确

**缺点**:
- 安装复杂
- 资源需求高
- 处理速度较慢

**参考**: https://github.com/docling/docling

---

### 4. 专用PDF转换工具

#### pdfplumber
- 基于pdfminer.six
- 精确的表格提取
- 布局分析
- 适合结构化PDF

```python
import pdfplumber
with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

#### PyMuPDF (fitz)
- 速度快
- 功能丰富
- 支持渲染

#### Marker
- 开源PDF转Markdown专用工具
- 适合批量处理
- GPU加速支持

---

### 5. Office文档处理

#### python-docx
- 纯Python实现
- 读取DOCX文件
- 访问段落、表格、样式

```python
from docx import Document
doc = Document("document.docx")
for para in doc.paragraphs:
    print(para.text)
```

#### python-pptx
- PowerPoint处理
- 幻灯片遍历
- 形状和文本提取

#### openpyxl
- Excel读写
- 单元格访问
- 公式支持

---

### 6. OCR解决方案

#### Tesseract + pytesseract
- 开源OCR引擎
- 多语言支持
- 需要安装二进制

```python
import pytesseract
from PIL import Image
text = pytesseract.image_to_string("image.png", lang="chi_sim+eng")
```

#### EasyOCR
- 基于PyTorch
- 80+语言支持
- 无需预训练模型

#### PaddleOCR
- 百度开源
- 中文识别优秀
- 轻量级模型

---

### 7. HTML转换

#### html2text
- 简洁的HTML转Markdown
- 可配置选项

```python
import html2text
h = html2text.HTML2Text()
md = h.handle("<h1>Title</h1>")
```

#### BeautifulSoup
- 灵活的HTML解析
- 自定义转换逻辑

---

## 技术方案对比

| 工具/库 | 格式支持 | 精度 | 速度 | 易用性 | 依赖 |
|---------|----------|------|------|--------|------|
| MarkItDown | 广泛 | 中 | 快 | 高 | 中 |
| Pandoc | 极广 | 高 | 慢 | 中 | 高 |
| Docling | 广泛 | 极高 | 慢 | 低 | 高 |
| pdfplumber | PDF | 高 | 中 | 高 | 低 |
| PyMuPDF | PDF | 中 | 极快 | 高 | 中 |
| python-docx | DOCX | 高 | 快 | 高 | 低 |
| python-pptx | PPTX | 高 | 快 | 高 | 低 |
| openpyxl | XLSX | 高 | 快 | 高 | 低 |
| Tesseract | 图片 | 高 | 慢 | 中 | 高 |
| html2text | HTML | 中 | 快 | 高 | 低 |

## 设计决策

### 架构选择

**策略模式 + 注册表模式**
- 每个格式独立转换器
- 运行时自动选择
- 易于扩展

### 依赖策略

**核心依赖最小化**
- 只包含最常用的库
- 其他作为可选依赖
- 优雅降级处理

### 多后端支持

**PDF处理**
- 优先: pdfplumber（表格准确）
- 备选: PyMuPDF（速度快）
- 回退: pypdf（纯Python）

**HTML处理**
- 优先: html2text（简洁）
- 备选: BeautifulSoup（灵活）

**OCR处理**
- 优先: Tesseract（成熟）
- 备选: EasyOCR/PaddleOCR

## 最佳实践

### 1. 格式保留

```python
# 保留标题层级
def _paragraph_to_markdown(self, para):
    style_name = para.style.name.lower()
    if 'heading 1' in style_name:
        return f"# {para.text}"
    # ...
```

### 2. 表格处理

```python
# 统一表格转换接口
def _table_to_markdown(self, table):
    rows = [...]
    return '| ' + ' | '.join(rows[0]) + ' |'
```

### 3. 错误处理

```python
try:
    result = converter.convert(file_path)
except ImportError as e:
    # 依赖缺失
    logger.error(f"缺少依赖: {e}")
except Exception as e:
    # 其他错误
    logger.error(f"转换失败: {e}")
```

### 4. 批量处理

```python
# 使用生成器减少内存
for file_path in Path('./docs').glob('*.pdf'):
    result = converter.convert(file_path)
    yield result
```

## 未来趋势

### 1. VLM-based转换
- 视觉语言模型直接理解文档
- Granite-Docling等方案
- 更高的结构保留度

### 2. 端到端解决方案
- 文档理解 + 转换一体化
- 更少的手动规则
- 更好的复杂布局处理

### 3. 边缘部署
- 模型小型化
- 本地运行保护隐私
- 实时处理能力

## 结论

File2MD项目采用以下策略：

1. **模块化设计** - 每个格式独立转换器
2. **多后端支持** - 根据场景选择最优方案
3. **渐进增强** - 基础功能无依赖，高级功能可选
4. **LLM优化** - 输出格式针对LLM输入优化

这种设计平衡了功能丰富性、易用性和可维护性。

## 参考资源

- [MarkItDown GitHub](https://github.com/microsoft/markitdown)
- [Pandoc 文档](https://pandoc.org/)
- [Docling GitHub](https://github.com/docling/docling)
- [pdfplumber 文档](https://github.com/jsvine/pdfplumber)
- [python-docx 文档](https://python-docx.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
