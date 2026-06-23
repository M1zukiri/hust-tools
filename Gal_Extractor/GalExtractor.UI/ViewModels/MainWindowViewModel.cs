
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using GalExtractor.Core;
using GalExtractor.UI.Commands;
using GalExtractor.Plugins.Circus;
using GalExtractor.Plugins.Kirikiri;
using GalExtractor.Plugins.Noa;
using GalExtractor.Plugins.RenPy;
using Microsoft.Win32;

namespace GalExtractor.UI.ViewModels
{
    public class MainWindowViewModel : ViewModelBase
    {
        private readonly PluginManager _pluginManager;
        private string? _filePath;
        private IGameArchive? _currentParser;
        private ObservableCollection<IArchiveEntry> _fileEntries;
        private IArchiveEntry? _selectedEntry;
        private string _logText;
        private bool _isBusy;
        private string _statusText;

        public MainWindowViewModel()
        {
            _pluginManager = new PluginManager();
            _fileEntries = new ObservableCollection<IArchiveEntry>();
            _logText = string.Empty;
            _statusText = "Ready";

            // Load plugins from all referenced plugin assemblies
            _pluginManager.LoadPlugins(
                typeof(Xp3Archive).Assembly,
                typeof(ArcArchive).Assembly,
                typeof(NoaArchive).Assembly,
                typeof(RpaArchive).Assembly
            );

            // Initialize commands
            OpenFileCommand = new RelayCommand(OpenFile);
            ExtractAllCommand = new RelayCommand(ExtractAll, CanExtract);
            ExtractSelectedCommand = new RelayCommand(ExtractSelected, CanExtractSelected);
        }

        #region Properties

        public string? FilePath
        {
            get => _filePath;
            private set
            {
                _filePath = value;
                OnPropertyChanged();
            }
        }

        public IGameArchive? CurrentParser
        {
            get => _currentParser;
            private set
            {
                _currentParser = value;
                OnPropertyChanged();
            }
        }

        public ObservableCollection<IArchiveEntry> FileEntries
        {
            get => _fileEntries;
            private set
            {
                _fileEntries = value;
                OnPropertyChanged();
            }
        }

        public IArchiveEntry? SelectedEntry
        {
            get => _selectedEntry;
            set
            {
                _selectedEntry = value;
                OnPropertyChanged();
            }
        }

        public string LogText
        {
            get => _logText;
            private set
            {
                _logText = value;
                OnPropertyChanged();
            }
        }

        public bool IsBusy
        {
            get => _isBusy;
            private set
            {
                _isBusy = value;
                OnPropertyChanged();
            }
        }

        public string StatusText
        {
            get => _statusText;
            private set
            {
                _statusText = value;
                OnPropertyChanged();
            }
        }

        #endregion

        #region Commands

        public ICommand OpenFileCommand { get; }
        public ICommand ExtractAllCommand { get; }
        public ICommand ExtractSelectedCommand { get; }

        #endregion

        #region Command Methods

        private async void OpenFile()
        {
            var dialog = new OpenFileDialog
            {
                Title = "Open Game Archive",
                Filter = CreateFileFilter()
            };

            if (dialog.ShowDialog() == true)
            {
                await OpenArchiveAsync(dialog.FileName);
            }
        }

        private async void ExtractAll()
        {
            if (string.IsNullOrEmpty(FilePath) || CurrentParser == null)
                return;

            var dialog = new OpenFolderDialog
            {
                Title = "Select Output Directory"
            };

            if (dialog.ShowDialog() == true)
            {
                await ExtractAllAsync(dialog.FolderName);
            }
        }

        private async void ExtractSelected()
        {
            if (SelectedEntry == null || string.IsNullOrEmpty(FilePath) || CurrentParser == null)
                return;

            var dialog = new SaveFileDialog
            {
                Title = "Save File",
                FileName = Path.GetFileName(SelectedEntry.Name),
                Filter = "All files (*.*)|*.*"
            };

            if (dialog.ShowDialog() == true)
            {
                await ExtractFileAsync(SelectedEntry, dialog.FileName);
            }
        }

        #endregion

        #region Private Methods

        private string CreateFileFilter()
        {
            var extensions = _pluginManager.GetSupportedExtensions();
            var filter = "All supported files|" + string.Join(";", extensions.Select(e => "*" + e));

            foreach (var parser in _pluginManager.Parsers)
            {
                filter += "|" + parser.EngineName + " files|" + string.Join(";", parser.SupportedExtensions.Select(e => "*" + e));
            }

            filter += "|All files (*.*)|*.*";
            return filter;
        }

        private async Task OpenArchiveAsync(string filePath)
        {
            IsBusy = true;
            StatusText = "Opening archive...";

            try
            {
                await Task.Run(() =>
                {
                    using var stream = File.OpenRead(filePath);
                    var parser = _pluginManager.FindParser(stream);

                    if (parser == null)
                    {
                        App.Current.Dispatcher.Invoke(() =>
                        {
                            MessageBox.Show("Unsupported archive format.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        });
                        return;
                    }

                    var entries = parser.ReadTOC(stream);

                    App.Current.Dispatcher.Invoke(() =>
                    {
                        FilePath = filePath;
                        CurrentParser = parser;
                        FileEntries.Clear();

                        foreach (var entry in entries)
                        {
                            FileEntries.Add(entry);
                        }

                        StatusText = $"Loaded {FileEntries.Count} files from {Path.GetFileName(filePath)}";
                        Log($"Opened archive: {filePath}");
                        Log($"Engine: {parser.EngineName}");
                        Log($"Files: {FileEntries.Count}");
                    });
                });
            }
            catch (Exception ex)
            {
                App.Current.Dispatcher.Invoke(() =>
                {
                    MessageBox.Show($"Error opening archive: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    StatusText = "Error opening archive";
                });
                Log($"Error: {ex.Message}");
            }
            finally
            {
                IsBusy = false;
            }
        }

        private async Task ExtractAllAsync(string outputDirectory)
        {
            IsBusy = true;
            StatusText = "Extracting files...";

            try
            {
                await Task.Run(() =>
                {
                    if (string.IsNullOrEmpty(FilePath) || CurrentParser == null)
                        return;

                    using var archiveStream = File.OpenRead(FilePath);

                    int extractedCount = 0;
                    int totalCount = FileEntries.Count;

                    foreach (var entry in FileEntries)
                    {
                        var outputPath = Path.Combine(outputDirectory, entry.Name);
                        var outputDir = Path.GetDirectoryName(outputPath);

                        if (!string.IsNullOrEmpty(outputDir) && !Directory.Exists(outputDir))
                        {
                            Directory.CreateDirectory(outputDir);
                        }

                        using var outputStream = File.Create(outputPath);
                        CurrentParser.ExtractFile(entry, archiveStream, outputStream);

                        extractedCount++;

                        App.Current.Dispatcher.Invoke(() =>
                        {
                            StatusText = $"Extracting {extractedCount}/{totalCount} files...";
                        });
                    }

                    App.Current.Dispatcher.Invoke(() =>
                    {
                        StatusText = $"Extracted {extractedCount} files to {outputDirectory}";
                        Log($"Extracted {extractedCount} files to {outputDirectory}");
                    });
                });
            }
            catch (Exception ex)
            {
                App.Current.Dispatcher.Invoke(() =>
                {
                    MessageBox.Show($"Error extracting files: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    StatusText = "Error extracting files";
                });
                Log($"Error: {ex.Message}");
            }
            finally
            {
                IsBusy = false;
            }
        }

        private async Task ExtractFileAsync(IArchiveEntry entry, string outputPath)
        {
            IsBusy = true;
            StatusText = "Extracting file...";

            try
            {
                await Task.Run(() =>
                {
                    if (string.IsNullOrEmpty(FilePath) || CurrentParser == null)
                        return;

                    using var archiveStream = File.OpenRead(FilePath);
                    using var outputStream = File.Create(outputPath);

                    CurrentParser.ExtractFile(entry, archiveStream, outputStream);

                    App.Current.Dispatcher.Invoke(() =>
                    {
                        StatusText = $"Extracted {entry.Name} to {outputPath}";
                        Log($"Extracted {entry.Name} to {outputPath}");
                    });
                });
            }
            catch (Exception ex)
            {
                App.Current.Dispatcher.Invoke(() =>
                {
                    MessageBox.Show($"Error extracting file: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    StatusText = "Error extracting file";
                });
                Log($"Error: {ex.Message}");
            }
            finally
            {
                IsBusy = false;
            }
        }

        private void Log(string message)
        {
            LogText += $"[{DateTime.Now:HH:mm:ss}] {message}" + Environment.NewLine;
        }

        private bool CanExtract()
        {
            return !string.IsNullOrEmpty(FilePath) && CurrentParser != null && FileEntries.Count > 0;
        }

        private bool CanExtractSelected()
        {
            return !string.IsNullOrEmpty(FilePath) && CurrentParser != null && SelectedEntry != null;
        }

        #endregion
    }
}