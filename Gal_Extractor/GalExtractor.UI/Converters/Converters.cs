using System;
using System.Globalization;
using System.IO;
using System.Windows;
using System.Windows.Data;
using System.Windows.Media.Imaging;
using GalExtractor.Core;

namespace GalExtractor.UI.Converters
{
    /// <summary>
    /// Inverts a boolean value (true → false, false → true)
    /// </summary>
    [ValueConversion(typeof(bool), typeof(bool))]
    public class InverseBooleanConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool b)
                return !b;
            return false;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool b)
                return !b;
            return false;
        }
    }

    /// <summary>
    /// Converts a file size in bytes to a human-readable string (KB, MB, GB)
    /// </summary>
    [ValueConversion(typeof(long), typeof(string))]
    public class FileSizeConverter : IValueConverter
    {
        private static readonly string[] SizeUnits = { "B", "KB", "MB", "GB", "TB" };

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            long bytes;
            if (value is long l)
                bytes = l;
            else if (value is int i)
                bytes = i;
            else
                return "0 B";

            if (bytes == 0)
                return "0 B";

            int unitIndex = 0;
            double size = bytes;

            while (size >= 1024 && unitIndex < SizeUnits.Length - 1)
            {
                size /= 1024;
                unitIndex++;
            }

            return $"{size:0.##} {SizeUnits[unitIndex]}";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    /// <summary>
    /// Converts null to Visibility.Collapsed, non-null to Visibility.Visible
    /// </summary>
    [ValueConversion(typeof(object), typeof(Visibility))]
    public class NullToVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value == null ? Visibility.Collapsed : Visibility.Visible;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    /// <summary>
    /// Converts an IArchiveEntry to a BitmapImage for preview (if it's an image file)
    /// </summary>
    [ValueConversion(typeof(IArchiveEntry), typeof(BitmapImage))]
    public class ImagePreviewConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return System.Windows.DependencyProperty.UnsetValue;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    /// <summary>
    /// Returns Visibility.Visible if the selected entry is an image file type
    /// </summary>
    [ValueConversion(typeof(IArchiveEntry), typeof(Visibility))]
    public class ImagePreviewVisibilityConverter : IValueConverter
    {
        private static readonly string[] ImageExtensions = {
            ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tga", ".tiff", ".webp", ".dds"
        };

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is IArchiveEntry entry)
            {
                var ext = Path.GetExtension(entry.Name)?.ToLowerInvariant();
                if (ext != null && Array.IndexOf(ImageExtensions, ext) >= 0)
                    return Visibility.Visible;
            }
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    /// <summary>
    /// Converts an IArchiveEntry to the text content for preview (if it's a text file)
    /// </summary>
    [ValueConversion(typeof(IArchiveEntry), typeof(string))]
    public class TextPreviewConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return System.Windows.DependencyProperty.UnsetValue;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    /// <summary>
    /// Returns Visibility.Visible if the selected entry is a text file type
    /// </summary>
    [ValueConversion(typeof(IArchiveEntry), typeof(Visibility))]
    public class TextPreviewVisibilityConverter : IValueConverter
    {
        private static readonly string[] TextExtensions = {
            ".txt", ".ks", ".tjs", ".json", ".xml", ".yaml", ".yml",
            ".csv", ".ini", ".cfg", ".lua", ".py", ".rb", ".bat", ".sh",
            ".html", ".htm", ".css", ".js", ".md", ".log"
        };

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is IArchiveEntry entry)
            {
                var ext = Path.GetExtension(entry.Name)?.ToLowerInvariant();
                if (ext != null && Array.IndexOf(TextExtensions, ext) >= 0)
                    return Visibility.Visible;
            }
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
