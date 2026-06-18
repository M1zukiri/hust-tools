"""
图片 转 Markdown 转换器
使用OCR技术提取文本
"""

from pathlib import Path
from typing import Optional, Dict, Any

from converter_base import BaseConverter, ConversionResult, ConversionStatus


class ImageConverter(BaseConverter):
    """图片转Markdown转换器（OCR）"""
    
    supported_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp']
    supported_mime_types = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp'
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.language = config.get('language', 'chi_sim+eng') if config else 'chi_sim+eng'
        self.psm_mode = config.get('psm_mode', 6) if config else 6  # 默认假设是统一文本块
    
    def convert(self, file_path: Path, **options) -> ConversionResult:
        """
        将图片转换为Markdown（通过OCR提取文本）
        
        Args:
            file_path: 图片文件路径
            **options: 额外选项
                - language: OCR语言
                - psm_mode: Tesseract页面分割模式
                - backend: OCR后端 ('tesseract', 'easyocr', 'paddleocr')
                
        Returns:
            ConversionResult: 转换结果
        """
        if not self.validate_file(file_path):
            return self._create_error_result(file_path, "文件验证失败", "image")
        
        backend = options.get('backend', 'auto')
        
        # 尝试不同的后端
        backends_to_try = self._get_backends(backend)
        
        errors = []
        for backend_name, backend_func in backends_to_try:
            try:
                result = backend_func(file_path, **options)
                if result.status == ConversionStatus.SUCCESS:
                    return result
            except Exception as e:
                errors.append(f"{backend_name}: {str(e)}")
                continue
        
        return self._create_error_result(
            file_path,
            f"所有OCR后端都失败: {'; '.join(errors)}",
            "image"
        )
    
    def _get_backends(self, preferred: str) -> list:
        """
        获取要尝试的后端列表
        
        Args:
            preferred: 首选后端
            
        Returns:
            list: (名称, 函数)列表
        """
        backends = {
            'tesseract': self._convert_with_tesseract,
            'easyocr': self._convert_with_easyocr,
            'paddleocr': self._convert_with_paddleocr,
        }
        
        if preferred == 'auto':
            # 按优先级排序
            return [
                ('tesseract', backends['tesseract']),
                ('easyocr', backends['easyocr']),
                ('paddleocr', backends['paddleocr']),
            ]
        elif preferred in backends:
            return [(preferred, backends[preferred])]
        else:
            return list(backends.items())
    
    def _convert_with_tesseract(self, file_path: Path, **options) -> ConversionResult:
        """
        使用Tesseract OCR转换图片
        
        Args:
            file_path: 图片文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError(
                "缺少依赖: pytesseract 或 Pillow。"
                "请运行: pip install pytesseract Pillow\n"
                "并确保已安装Tesseract OCR引擎: https://github.com/tesseract-ocr/tesseract"
            )
        
        try:
            # 打开图片
            image = Image.open(str(file_path))
            
            # 配置OCR参数
            lang = options.get('language', self.language)
            psm = options.get('psm_mode', self.psm_mode)
            
            custom_config = f'--psm {psm}'
            
            # 执行OCR
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=custom_config
            )
            
            # 包装为Markdown格式
            md_content = self._format_ocr_result(text, **options)
            
            metadata = self.extract_metadata(file_path)
            metadata['ocr_backend'] = 'tesseract'
            metadata['ocr_language'] = lang
            metadata['image_size'] = image.size
            metadata['image_mode'] = image.mode
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='image',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            raise e
    
    def _convert_with_easyocr(self, file_path: Path, **options) -> ConversionResult:
        """
        使用EasyOCR转换图片
        
        Args:
            file_path: 图片文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            import easyocr
        except ImportError:
            raise ImportError("缺少依赖: easyocr。请运行: pip install easyocr")
        
        try:
            # 初始化reader（首次运行会下载模型）
            lang = options.get('language', self.language)
            # EasyOCR使用语言代码列表
            lang_list = lang.split('+') if '+' in lang else [lang]
            
            reader = easyocr.Reader(lang_list, gpu=False)
            
            # 执行OCR
            results = reader.readtext(str(file_path))
            
            # 提取文本
            texts = [result[1] for result in results]
            text = '\n'.join(texts)
            
            # 包装为Markdown格式
            md_content = self._format_ocr_result(text, **options)
            
            metadata = self.extract_metadata(file_path)
            metadata['ocr_backend'] = 'easyocr'
            metadata['ocr_language'] = lang
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='image',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            raise e
    
    def _convert_with_paddleocr(self, file_path: Path, **options) -> ConversionResult:
        """
        使用PaddleOCR转换图片
        
        Args:
            file_path: 图片文件路径
            **options: 额外选项
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("缺少依赖: paddleocr。请运行: pip install paddleocr")
        
        try:
            # 初始化OCR
            lang = options.get('language', self.language)
            # PaddleOCR语言映射
            lang_map = {
                'chi_sim': 'ch',
                'chi_tra': 'ch',
                'eng': 'en',
                'jpn': 'japan',
                'kor': 'korean',
            }
            paddle_lang = lang_map.get(lang.split('+')[0], 'ch')
            
            ocr = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)
            
            # 执行OCR
            result = ocr.ocr(str(file_path), cls=True)
            
            # 提取文本
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        texts.append(line[1][0])  # 文本内容
            
            text = '\n'.join(texts)
            
            # 包装为Markdown格式
            md_content = self._format_ocr_result(text, **options)
            
            metadata = self.extract_metadata(file_path)
            metadata['ocr_backend'] = 'paddleocr'
            metadata['ocr_language'] = paddle_lang
            
            return ConversionResult(
                content=md_content,
                status=ConversionStatus.SUCCESS,
                source_format='image',
                metadata=metadata,
                errors=[]
            )
            
        except Exception as e:
            raise e
    
    def _format_ocr_result(self, text: str, **options) -> str:
        """
        格式化OCR结果为Markdown
        
        Args:
            text: OCR提取的文本
            **options: 额外选项
            
        Returns:
            str: Markdown格式内容
        """
        if not text.strip():
            return "*（未识别到文本内容）*"
        
        md_parts = []
        
        # 添加OCR标识
        md_parts.append("<!-- OCR提取内容 -->\n")
        
        # 尝试检测并格式化可能的表格
        lines = text.split('\n')
        
        # 简单启发式：如果有多行且包含分隔符，可能是表格
        if len(lines) >= 2:
            # 检查是否可能是表格
            potential_table = self._try_format_table(lines)
            if potential_table:
                md_parts.append(potential_table)
            else:
                md_parts.append(text)
        else:
            md_parts.append(text)
        
        return '\n'.join(md_parts)
    
    def _try_format_table(self, lines: list) -> Optional[str]:
        """
        尝试将文本格式化为Markdown表格
        
        Args:
            lines: 文本行列表
            
        Returns:
            Optional[str]: 表格Markdown或None
        """
        # 简单启发式：如果行之间有规律的分隔符
        # 这里使用简单的检测逻辑
        
        # 检查是否有制表符分隔
        if any('\t' in line for line in lines[:5]):
            rows = []
            for line in lines:
                if line.strip():
                    cells = line.split('\t')
                    rows.append(cells)
            
            if len(rows) >= 2:
                return self._build_markdown_table(rows)
        
        # 检查是否有多个空格分隔（对齐列）
        # 这是一个简化的检测
        
        return None
    
    def _build_markdown_table(self, rows: list) -> str:
        """
        构建Markdown表格
        
        Args:
            rows: 行数据列表
            
        Returns:
            str: Markdown表格
        """
        if not rows or not rows[0]:
            return ""
        
        md_lines = []
        
        # 表头
        header = [str(cell).strip() for cell in rows[0]]
        md_lines.append('| ' + ' | '.join(header) + ' |')
        md_lines.append('|' + '|'.join(['---' for _ in header]) + '|')
        
        # 数据行
        for row in rows[1:]:
            cells = [str(cell).strip() for cell in row]
            # 确保列数一致
            while len(cells) < len(header):
                cells.append("")
            cells = cells[:len(header)]
            
            md_lines.append('| ' + ' | '.join(cells) + ' |')
        
        return '\n'.join(md_lines)
