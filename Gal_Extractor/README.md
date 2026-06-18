# Gal_Extractor — GalGame 资源提取器

提取 Kirikiri（XP3）和 Ren'Py（RPA）引擎的 GalGame 封包资源。

## 调用方法

```bash
# 在项目目录下直接运行（需 .NET SDK）
dotnet run --project GalExtractor.UI
```

## 项目结构

```
Gal_Extractor/
├── GalExtractor.sln                        # 解决方案文件
├── GalExtractor.Core/                      # 核心库
│   ├── GalExtractor.Core.csproj
│   ├── ArchiveEntry.cs                     # 封包条目模型
│   ├── BinaryReaderHelper.cs               # 二进制读取辅助
│   ├── IArchiveEntry.cs                    # 封包条目接口
│   ├── IGameArchive.cs                     # 游戏封包接口
│   └── PluginManager.cs                    # 插件管理器
├── GalExtractor.Plugins.Kirikuri/          # Kirikiri（XP3）插件
│   ├── GalExtractor.Plugins.Kirikiri.csproj
│   └── Xp3Archive.cs                       # XP3 封包解析器
├── GalExtractor.Plugins.RenPy/             # Ren'Py（RPA）插件
│   ├── GalExtractor.Plugins.RenPy.csproj
│   └── RpaArchive.cs                       # RPA 封包解析器
├── GalExtractor.UI/                        # WPF 用户界面
│   ├── GalExtractor.UI.csproj
│   ├── App.xaml / App.xaml.cs              # 应用入口
│   ├── MainWindow.xaml / MainWindow.xaml.cs# 主窗口
│   ├── ViewModels/
│   │   ├── MainWindowViewModel.cs          # 主视图模型
│   │   ├── ViewModelBase.cs                # 视图模型基类
│   │   └── RelayCommand.cs                 # 命令辅助
│   └── Views/                              # 视图文件
├── README.md                               # 本文档
└── .vscode/settings.json                   # VS Code 配置
```

## 技术栈

- **语言**: C# (.NET)
- **框架**: WPF (Windows Presentation Foundation)
- **架构**: 插件式设计，可扩展更多游戏引擎

## 依赖

- [.NET SDK](https://dotnet.microsoft.com/download)（建议 .NET 6+）
- Windows 系统（WPF 界面）

## 支持的引擎

| 引擎 | 封包格式 | 插件 |
|------|---------|------|
| Kirikiri (吉里吉里) | .xp3 | `GalExtractor.Plugins.Kirikiri` |
| Ren'Py | .rpa | `GalExtractor.Plugins.RenPy` |
