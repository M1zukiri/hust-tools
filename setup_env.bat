@echo off
title hust-tools 环境自动配置
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ROOT=%~dp0"

REM ---- pip 包列表 ----
set "CORE_PKGS=pillow pydub numpy matplotlib requests"
set "FFMPEG_PKG=ffmpeg-python"
set "PDF_PKGS=pypdf"
set "FILE2MD_CORE=python-docx python-pptx openpyxl pdfplumber html2text beautifulsoup4 chardet"

REM ---- 全局计数 ----
set /a TOTAL_INSTALLED=0, TOTAL_ALREADY=0, TOTAL_FAILED=0

REM =============================================
REM  主入口：跳过了函数定义
REM =============================================
goto :main

REM =============================================
REM  辅助函数
REM =============================================

:info
    echo [..] %*
    exit /b 0

:ok
    echo [OK] %*
    exit /b 0

:warn
    echo [!!] %*
    exit /b 0

:fail
    echo [XX] %*
    exit /b 0

REM ---- pip 包：检测 -> 缺失则安装 ----
REM 返回: 0=已安装 | 1=新安装成功 | 2=安装失败
:pip_ensure
    set "pkg=%~1"
    pip show "%pkg%" >nul 2>&1
    if not errorlevel 1 (
        set /a TOTAL_ALREADY+=1
        exit /b 0
    )
    call :info "安装 %pkg% ..."
    pip install "%pkg%" --quiet
    if errorlevel 1 (
        set /a TOTAL_FAILED+=1
        call :fail "%pkg% 安装失败"
        call :info "可稍后手动执行: pip install %pkg%"
        exit /b 2
    )
    set /a TOTAL_INSTALLED+=1
    call :ok "%pkg% 安装完成"
    exit /b 1

REM ---- 阶段标题 ----
:phase
    set "phase_name=%~1"
    set "phase_desc=%~2"
    set /a P_TOTAL=0, P_OK=0, P_FAIL=0
    echo.
    echo ========================================
    echo   %phase_name%
    if not "%phase_desc%"=="" echo   %phase_desc%
    echo ========================================
    exit /b 0

:phase_result
    set /a "P_TOTAL=P_OK+P_FAIL"
    if %P_FAIL% gtr 0 (
        call :warn "阶段结果: %P_OK% 成功, %P_FAIL% 失败"
    ) else (
        call :ok   "阶段结果: %P_OK% 个包就绪"
    )
    exit /b 0

REM ---- 检测基础环境 ----
:check_python
    where python >nul 2>&1
    if errorlevel 1 (
        call :fail "未找到 Python，请先安装 Python 3.8+ (https://python.org/downloads)"
        exit /b 1
    )
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    call :ok "Python %PY_VER%"
    exit /b 0

:check_pip
    python -m pip --version >nul 2>&1
    if errorlevel 1 (
        call :fail "pip 不可用，请检查 Python 安装"
        exit /b 1
    )
    exit /b 0

REM ---- ffmpeg 检测与安装 ----
:check_ffmpeg
    where ffmpeg >nul 2>&1
    if not errorlevel 1 (
        call :ok "ffmpeg (系统 PATH 中可用)"
        exit /b 0
    )
    pip show imageio-ffmpeg >nul 2>&1
    if not errorlevel 1 (
        call :warn "ffmpeg 可通过 imageio-ffmpeg 使用"
        exit /b 1
    )
    exit /b 2

:install_ffmpeg
    call :info "安装 ffmpeg ..."
    call :info "尝试通过 imageio-ffmpeg 安装..."
    pip install imageio-ffmpeg --quiet
    if errorlevel 1 goto :ffmpeg_winget
    pip show imageio-ffmpeg >nul 2>&1
    if errorlevel 1 goto :ffmpeg_winget
    call :ok "imageio-ffmpeg 安装成功"
    exit /b 1

    :ffmpeg_winget
    call :info "尝试通过 winget 安装系统级 ffmpeg (需管理员权限)..."
    winget install "FFmpeg (Shared)" 2>nul
    if errorlevel 1 (
        call :fail "ffmpeg 自动安装失败"
        call :warn "请手动安装任一方式:"
        call :warn "  (推荐) pip install imageio-ffmpeg"
        call :warn "  winget install ffmpeg"
        call :warn "  或下载 https://ffmpeg.org/download.html 并加入 PATH"
        exit /b 2
    )
    call :ok "ffmpeg 安装成功"
    exit /b 1


REM =============================================
REM  主流程
REM =============================================
:main

echo =============================================
echo   hust-tools - 环境自动配置脚本
echo   仓库: %ROOT%
echo =============================================
echo.

call :info "检查基础环境..."
call :check_python
if errorlevel 1 (
    echo.
    call :fail "基础环境不满足，无法继续"
    pause
    exit /b 2
)
call :check_pip
if errorlevel 1 (
    echo.
    call :fail "pip 不可用，无法安装依赖"
    pause
    exit /b 2
)

REM ---- [1/4] 核心公共依赖 ----
call :phase "阶段 1/4 - 核心公共依赖" "涉及: File_converter, Pdf_Tool, Png_2_Gif, Eye_map, Location"
for %%p in (%CORE_PKGS%) do (
    call :pip_ensure "%%p"
    if errorlevel 2 (set /a P_FAIL+=1) else (set /a P_OK+=1)
)
call :pip_ensure "%FFMPEG_PKG%"
if errorlevel 2 (set /a P_FAIL+=1) else (set /a P_OK+=1)
call :phase_result

REM ---- [2/4] PDF 工具 ----
call :phase "阶段 2/4 - PDF 工具依赖" "涉及: Pdf_Tool"
for %%p in (%PDF_PKGS%) do (
    call :pip_ensure "%%p"
    if errorlevel 2 (set /a P_FAIL+=1) else (set /a P_OK+=1)
)
call :phase_result

REM ---- [3/4] 文档转换 (File_2_md) ----
call :phase "阶段 3/4 - 文档转 Markdown 工具" "涉及: File_2_md (核心功能，不含 GUI/OCR)"
for %%p in (%FILE2MD_CORE%) do (
    call :pip_ensure "%%p"
    if errorlevel 2 (set /a P_FAIL+=1) else (set /a P_OK+=1)
)
call :phase_result

REM ---- [4/4] ffmpeg (系统级) ----
call :phase "阶段 4/4 - ffmpeg" "涉及: File_converter (视频/音频转换所需)"
call :check_ffmpeg
if errorlevel 2 (
    call :warn "ffmpeg 未安装，开始自动安装..."
    call :install_ffmpeg
    if errorlevel 2 (set /a P_FAIL+=1) else (set /a P_OK+=1)
) else (
    set /a P_OK+=1
)
call :phase_result

REM =============================================
REM  最终报告
REM =============================================

echo.
echo =============================================
echo   配置完成 - 汇总
echo =============================================

set /a "TOTAL=TOTAL_ALREADY+TOTAL_INSTALLED+TOTAL_FAILED"
call :info "总计检查 %TOTAL% 个包:"
echo   已安装 (跳过): %TOTAL_ALREADY%
echo   新安装         : %TOTAL_INSTALLED%
if %TOTAL_FAILED% gtr 0 (
    call :warn "安装失败         : %TOTAL_FAILED% 个"
    call :warn "以上失败可尝试手动安装，不影响其他工具"
) else (
    call :ok "全部安装成功"
)

echo.
echo =============================================
echo   可选组件 (跳过不影响基础功能)
echo =============================================
call :info "File_2_md GUI:  pip install PyQt6"
call :info "File_2_md OCR:   pip install pytesseract easyocr pandas PyMuPDF"
call :warn "Tesseract OCR 引擎:  https://github.com/UB-Mannheim/tesseracht/wiki"

where dotnet >nul 2>&1
if errorlevel 1 (
    call :warn "Gal_Extractor:   .NET SDK 未安装 (https://dotnet.microsoft.com/download)"
) else (
    call :ok  "Gal_Extractor:   .NET SDK 可用"
)

echo.
echo 按任意键退出...
pause >nul
exit /b %TOTAL_FAILED%
