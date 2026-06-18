import sys
import os
import json
import time
import subprocess
import importlib.util
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QProgressBar, QFileDialog, 
                             QDialog, QFormLayout, QSpinBox, QCheckBox, 
                             QLineEdit, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices

# ==========================================
# 依赖配置表：定义文件类型与所需Python包的映射
# ==========================================
DEP_CONFIG = [
    {
        "name": "Word (DOCX)", "extensions": [".docx", ".doc"],
        "check_mode": "all", "imports": ["docx"], "pip_packages": ["python-docx"]
    },
    {
        "name": "PowerPoint (PPTX)", "extensions": [".pptx", ".ppt"],
        "check_mode": "all", "imports": ["pptx"], "pip_packages": ["python-pptx"]
    },
    {
        "name": "Excel (XLSX)", "extensions": [".xlsx", ".xls"],
        "check_mode": "all", "imports": ["openpyxl"], "pip_packages": ["openpyxl"]
    },
    {
        "name": "CSV 数据", "extensions": [".csv"],
        "check_mode": "all", "imports": ["pandas"], "pip_packages": ["pandas"]
    },
    {
        "name": "PDF 文档", "extensions": [".pdf"],
        "check_mode": "any", "imports": ["pdfplumber", "fitz", "pypdf"], "pip_packages": ["pdfplumber"]
    },
    {
        "name": "HTML 网页", "extensions": [".html", ".htm"],
        "check_mode": "any", "imports": ["html2text", "bs4"], "pip_packages": ["html2text", "beautifulsoup4"]
    },
    {
        "name": "图片 OCR", "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
        "check_mode": "all", "imports": ["pytesseract", "PIL"], "pip_packages": ["pytesseract", "Pillow"]
    },
    {
        "name": "文本编码检测", "extensions": [".txt", ".md"],
        "check_mode": "all", "imports": ["chardet"], "pip_packages": ["chardet"]
    }
]

# ==========================================
# 全局设置与辅助函数
# ==========================================
SETTINGS_FILE = "settings.json"

def load_settings():
    """加载本地设置"""
    default_settings = {
        "output_dir": str(Path.home() / "Desktop" / "File2MD_Output"),
        "overwrite": True,
        "pdf_extract_tables": True,
        "xlsx_max_rows": 1000,
        "xlsx_max_cols": 50,
        "ocr_language": "chi_sim+eng"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                default_settings.update(json.load(f))
        except Exception:
            pass
    return default_settings

def save_settings(settings):
    """保存设置到本地"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def build_converter_config(settings):
    """将扁平的 GUI 设置转换为 File2MD 支持的嵌套 config 字典"""
    return {
        'pdf': {'extract_tables': settings.get('pdf_extract_tables', True)},
        'xlsx': {
            'max_rows': settings.get('xlsx_max_rows', 1000),
            'max_cols': settings.get('xlsx_max_cols', 50)
        },
        'image': {'language': settings.get('ocr_language', 'chi_sim+eng')}
    }

# ==========================================
# 依赖检查与安装模块
# ==========================================
class DependencyCheckerWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(set, bool)  # missing_exts, installed_anything

    def run(self):
        missing_exts = set()
        installed_anything = False
        
        for item in DEP_CONFIG:
            # 检查模块是否已安装
            if item["check_mode"] == "all":
                ok = all(self.is_installed(m) for m in item["imports"])
            else:
                ok = any(self.is_installed(m) for m in item["imports"])
                
            if not ok:
                installed_anything = True
                self.log_signal.emit(f"⏳ 检测到缺失 [{item['name']}] 依赖，准备安装: {', '.join(item['pip_packages'])}")
                
                # 配置子进程：在 Windows 上隐藏弹出的 CMD 黑色控制台窗口
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                try:
                    cmd = [sys.executable, "-m", "pip", "install"] + item["pip_packages"]
                    result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
                    
                    if result.returncode == 0:
                        self.log_signal.emit(f"✅ [{item['name']}] 依赖安装成功！")
                        # 二次验证
                        verify_ok = all(self.is_installed(m) for m in item["imports"]) if item["check_mode"] == "all" else any(self.is_installed(m) for m in item["imports"])
                        if not verify_ok:
                            missing_exts.update(item["extensions"])
                    else:
                        self.log_signal.emit(f"❌ [{item['name']}] 依赖安装失败！请稍后手动安装。")
                        missing_exts.update(item["extensions"])
                except Exception as e:
                    self.log_signal.emit(f"❌ 安装 [{item['name']}] 时发生系统异常: {str(e)}")
                    missing_exts.update(item["extensions"])
        
        self.finished_signal.emit(missing_exts, installed_anything)

    def is_installed(self, module_name):
        """利用 importlib 检查模块是否存在"""
        try:
            return importlib.util.find_spec(module_name) is not None
        except Exception:
            return False

class DependencyCheckDialog(QDialog):
    """启动时的依赖检查对话框"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File2MD - 环境依赖检查")
        self.setFixedSize(450, 250)
        # 去掉关闭按钮，强制等待检查完成
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        self.missing_exts = set()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel("正在扫描系统转换依赖...")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.lbl_title)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6; font-family: Consolas;")
        layout.addWidget(self.log_console)
        
        self.btn_continue = QPushButton("进入主程序")
        self.btn_continue.setEnabled(False)
        self.btn_continue.clicked.connect(self.accept)
        layout.addWidget(self.btn_continue)
        
        # 延迟100ms启动检查，确保UI先渲染出来
        QTimer.singleShot(100, self.start_check)

    def append_log(self, msg):
        self.log_console.append(msg)
        
    def start_check(self):
        self.worker = DependencyCheckerWorker()
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
    def on_finished(self, missing_exts, installed_anything):
        self.missing_exts = missing_exts
        if not installed_anything:
            # 如果什么都不缺，瞬间关闭窗口进入主程序
            self.accept()
        else:
            self.lbl_title.setText("环境扫描与修补完成。")
            self.append_log("\n==== 处理完毕，请点击进入主程序 ====")
            self.btn_continue.setEnabled(True)


# ==========================================
# 主程序转换模块
# ==========================================
class ConverterWorker(QThread):
    """后台转换线程，防止 UI 假死"""
    progress_signal = pyqtSignal(int, int, str)
    result_signal = pyqtSignal(str, bool, str, str)
    log_signal = pyqtSignal(str) 
    finished_signal = pyqtSignal()

    def __init__(self, file_paths, output_dir, settings):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = Path(output_dir)
        self.settings = settings
        self.is_running = True

    def run(self):
        self.log_signal.emit("初始化转换引擎...")
        config = build_converter_config(self.settings)
        converter = File2MD(config)
        total = len(self.file_paths)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_signal.emit(f"任务开始，共计 {total} 个文件。输出目录: {self.output_dir}")

        for i, file_path in enumerate(self.file_paths):
            if not self.is_running:
                self.log_signal.emit("任务已被用户中断。")
                break
            
            p = Path(file_path)
            self.progress_signal.emit(i + 1, total, p.name)
            self.log_signal.emit(f"正在处理 [{i+1}/{total}]: {p.name} ...")

            base_name = p.stem
            out_file = self.output_dir / f"{base_name}.md"
            
            if not self.settings.get("overwrite", True) and out_file.exists():
                counter = 1
                while (self.output_dir / f"{base_name}_{counter}.md").exists():
                    counter += 1
                out_file = self.output_dir / f"{base_name}_{counter}.md"

            try:
                result = converter.convert(p, output_path=str(out_file))

                if result.success:
                    self.log_signal.emit(f"  ✓ 成功: 已保存至 {out_file.name}")
                    self.result_signal.emit(str(p), True, str(out_file), "")
                else:
                    error_str = " | ".join(result.errors)
                    self.log_signal.emit(f"  ✗ 失败: {error_str}")
                    self.result_signal.emit(str(p), False, error_str, error_str)
            except Exception as e:
                self.log_signal.emit(f"  ✗ 严重异常: {str(e)}")
                self.result_signal.emit(str(p), False, "内部异常", str(e))

        self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class HoverListItemWidget(QWidget):
    """自定义列表项：悬停显示删除按钮 & 支持缺失依赖标红"""
    def __init__(self, file_path, delete_callback, is_missing_dep=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.delete_callback = delete_callback

        # 开启自定义背景色支持
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.label = QLabel(Path(file_path).name)
        
        # 处理依赖缺失状态
        if is_missing_dep:
            # 缺失依赖时，设置浅红底色
            self.setStyleSheet("HoverListItemWidget { background-color: #ffcccc; border-radius: 4px; }")
            self.label.setToolTip(f"{file_path}\n(警告: 缺少该格式所需的转换库，转换大概率会失败)")
            self.label.setStyleSheet("color: #b71c1c;")
        else:
            self.setStyleSheet("HoverListItemWidget { background-color: transparent; }")
            self.label.setToolTip(file_path)

        layout.addWidget(self.label, 1)

        self.del_btn = QPushButton("❌")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setStyleSheet("border: none; color: red;")
        self.del_btn.clicked.connect(self._on_delete)
        self.del_btn.hide()
        layout.addWidget(self.del_btn)

    def _on_delete(self):
        self.delete_callback(self.file_path, self)

    def enterEvent(self, event):
        self.del_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.del_btn.hide()
        super().leaveEvent(event)

class DragDropListWidget(QListWidget):
    """支持拖拽验证的文件列表"""
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # 延迟获取支持的格式，避免循环依赖问题
        self.supported_formats = [] 

    def update_supported_formats(self, formats):
        self.supported_formats = formats

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = Path(path).suffix.lower().lstrip('.')
            if not self.supported_formats or ext in self.supported_formats or not ext:
                files.append(path)
        if files:
            self.files_dropped.emit(files)

class AdvancedSettingsDialog(QDialog):
    """高级设置对话框"""
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级设置")
        self.setMinimumWidth(300)
        self.settings = current_settings.copy()

        layout = QFormLayout(self)

        self.cb_extract_tables = QCheckBox("提取 PDF 表格")
        self.cb_extract_tables.setChecked(self.settings.get("pdf_extract_tables", True))
        layout.addRow("PDF 设置:", self.cb_extract_tables)

        self.spin_max_rows = QSpinBox()
        self.spin_max_rows.setMaximum(100000)
        self.spin_max_rows.setValue(self.settings.get("xlsx_max_rows", 1000))
        layout.addRow("Excel 最大行数:", self.spin_max_rows)

        self.spin_max_cols = QSpinBox()
        self.spin_max_cols.setMaximum(1000)
        self.spin_max_cols.setValue(self.settings.get("xlsx_max_cols", 50))
        layout.addRow("Excel 最大列数:", self.spin_max_cols)

        self.le_ocr_lang = QLineEdit()
        self.le_ocr_lang.setText(self.settings.get("ocr_language", "chi_sim+eng"))
        layout.addRow("OCR 语言:", self.le_ocr_lang)

        btn_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        
        layout.addRow(btn_box)

    def get_settings(self):
        self.settings["pdf_extract_tables"] = self.cb_extract_tables.isChecked()
        self.settings["xlsx_max_rows"] = self.spin_max_rows.value()
        self.settings["xlsx_max_cols"] = self.spin_max_cols.value()
        self.settings["ocr_language"] = self.le_ocr_lang.text()
        return self.settings

class MainWindow(QMainWindow):
    def __init__(self, missing_exts):
        super().__init__()
        self.setWindowTitle("File2MD - 文件转Markdown工具")
        self.resize(850, 650)
        self.settings = load_settings()
        self.worker = None
        self.input_files = []
        self.missing_exts = missing_exts  # 保存缺失依赖的后缀列表
        
        self.success_count = 0
        self.fail_count = 0

        self._init_ui()
        
        # 初始化获取底层支持的格式，赋值给拖拽列表
        try:
            from file2md import get_supported_formats
            self.list_input.update_supported_formats(get_supported_formats())
        except ImportError:
            pass

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 上半部分：分栏布局 (左 中 右)
        top_layout = QHBoxLayout()
        
        # --- 左侧：待转换列表 ---
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("待转换文件 (支持拖拽):"))
        self.list_input = DragDropListWidget()
        self.list_input.files_dropped.connect(self.add_input_files)
        left_layout.addWidget(self.list_input)
        
        btn_add = QPushButton("添加文件")
        btn_add.clicked.connect(self.browse_input_files)
        left_layout.addWidget(btn_add)
        
        top_layout.addLayout(left_layout, 2)

        # --- 中间：转换控制 ---
        mid_layout = QVBoxLayout()
        mid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_convert = QPushButton(">> 转换 >>")
        self.btn_convert.setMinimumHeight(50)
        self.btn_convert.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_convert.clicked.connect(self.start_conversion)
        mid_layout.addWidget(self.btn_convert)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        mid_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("就绪")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mid_layout.addWidget(self.lbl_status)

        top_layout.addLayout(mid_layout, 1)

        # --- 右侧：已转换列表 ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("已转换文件 (点击打开):"))
        self.list_output = QListWidget()
        self.list_output.itemDoubleClicked.connect(self.open_converted_file)
        self.list_output.itemClicked.connect(self.open_converted_file)
        right_layout.addWidget(self.list_output)
        
        top_layout.addLayout(right_layout, 2)

        main_layout.addLayout(top_layout, 3)

        # 2. 中下部分：输出路径与设置
        bottom_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("输出路径:"))
        self.le_output_dir = QLineEdit(self.settings.get("output_dir", ""))
        path_layout.addWidget(self.le_output_dir)
        btn_browse_out = QPushButton("浏览")
        btn_browse_out.clicked.connect(self.browse_output_dir)
        path_layout.addWidget(btn_browse_out)
        bottom_layout.addLayout(path_layout)

        settings_layout = QHBoxLayout()
        self.cb_overwrite = QCheckBox("覆盖同名文件")
        self.cb_overwrite.setChecked(self.settings.get("overwrite", True))
        self.cb_overwrite.stateChanged.connect(self.save_current_settings)
        settings_layout.addWidget(self.cb_overwrite)
        
        settings_layout.addStretch()
        
        btn_advanced = QPushButton("高级设置 ⚙")
        btn_advanced.clicked.connect(self.open_advanced_settings)
        settings_layout.addWidget(btn_advanced)
        bottom_layout.addLayout(settings_layout)

        main_layout.addLayout(bottom_layout)
        
        # 3. 底部：依赖警告 与 日志控制台
        self.lbl_dep_warning = QLabel("⚠ 警告：有缺失的转换依赖，列表标红的部分文件可能无法转换。")
        self.lbl_dep_warning.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.lbl_dep_warning.setVisible(bool(self.missing_exts))
        main_layout.addWidget(self.lbl_dep_warning)

        main_layout.addWidget(QLabel("转换日志:"))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(150)
        self.log_console.setStyleSheet("background-color: #f8f9fa; font-family: Consolas, monospace;")
        self.log_console.setPlaceholderText("系统日志和报错信息将显示在这里...")
        main_layout.addWidget(self.log_console, 1)

    # --- 逻辑控制 ---
    def append_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {msg}")

    def browse_input_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择待转换文件")
        if files:
            self.add_input_files(files)

    def add_input_files(self, files):
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
                
                # 判断当前文件后缀是否属于“缺失依赖”的范畴
                ext = Path(f).suffix.lower()
                is_missing = ext in self.missing_exts
                
                item = QListWidgetItem(self.list_input)
                widget = HoverListItemWidget(f, self.remove_input_file, is_missing_dep=is_missing)
                item.setSizeHint(widget.sizeHint())
                self.list_input.setItemWidget(item, widget)

    def remove_input_file(self, file_path, widget):
        if file_path in self.input_files:
            self.input_files.remove(file_path)
        for i in range(self.list_input.count()):
            item = self.list_input.item(i)
            if self.list_input.itemWidget(item) == widget:
                self.list_input.takeItem(i)
                break

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", self.le_output_dir.text())
        if directory:
            self.le_output_dir.setText(directory)
            self.save_current_settings()

    def open_advanced_settings(self):
        dialog = AdvancedSettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.get_settings()
            self.save_current_settings()

    def save_current_settings(self):
        self.settings["output_dir"] = self.le_output_dir.text()
        self.settings["overwrite"] = self.cb_overwrite.isChecked()
        save_settings(self.settings)

    def start_conversion(self):
        if not self.input_files:
            QMessageBox.warning(self, "提示", "请先添加待转换的文件！")
            return
            
        out_dir = self.le_output_dir.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请设置输出路径！")
            return

        self.save_current_settings()
        self.list_output.clear()
        self.log_console.clear()
        
        self.success_count = 0
        self.fail_count = 0
        
        self.btn_convert.setEnabled(False)
        self.progress_bar.setMaximum(len(self.input_files))
        self.progress_bar.setValue(0)
        
        self.append_log("==== 开始新的转换队列 ====")
        
        # 启动多线程
        from file2md import File2MD # 延迟导入，防止底层缺失导致顶层崩溃
        self.worker = ConverterWorker(self.input_files.copy(), out_dir, self.settings)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.handle_result)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.conversion_finished)
        self.worker.start()

    def update_progress(self, current, total, filename):
        self.progress_bar.setValue(current)
        self.lbl_status.setText(f"正在处理: {filename} ({current}/{total})")

    def handle_result(self, input_path, success, out_path_or_err, error_details):
        item = QListWidgetItem()
        filename = Path(input_path).name
        
        if success:
            self.success_count += 1
            item.setText(f"✅ {filename}")
            item.setForeground(Qt.GlobalColor.darkGreen)
            item.setToolTip(out_path_or_err) 
            item.setData(Qt.ItemDataRole.UserRole, out_path_or_err) 
        else:
            self.fail_count += 1
            item.setText(f"❌ {filename}")
            item.setForeground(Qt.GlobalColor.red)
            item.setToolTip(f"错误: {error_details}")
            item.setData(Qt.ItemDataRole.UserRole, None)
            
        self.list_output.addItem(item)

    def conversion_finished(self):
        self.btn_convert.setEnabled(True)
        total = len(self.input_files)
        status_text = f"任务完成。共 {total} 项文件，成功 {self.success_count} 项，失败 {self.fail_count} 项。"
        self.lbl_status.setText(status_text)
        self.append_log(f"==== {status_text} ====")

    def open_converted_file(self, item):
        out_path = item.data(Qt.ItemDataRole.UserRole)
        if out_path and os.path.exists(out_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(out_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. 弹出检查弹窗（阻塞执行直到窗口关闭）
    dep_dialog = DependencyCheckDialog()
    dep_dialog.exec()
    
    # 获取缺失列表
    missing_exts = dep_dialog.missing_exts
    
    # 2. 检验核心模块是否就绪
    try:
        from file2md import File2MD
    except ImportError as e:
        QMessageBox.critical(None, "致命错误", f"核心文件 file2md.py 导入失败。\n{str(e)}")
        sys.exit(1)

    # 3. 启动主窗口，将缺失列表传入
    window = MainWindow(missing_exts)
    window.show()
    sys.exit(app.exec())