using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GalExtractor.Core;

namespace GalExtractor.Core
{
    /// <summary>
    /// File type classification utilities for extracted game resources.
    /// Detects file type by magic bytes, then falls back to extension.
    /// </summary>
    public static class FileClassifier
    {
        private static readonly Dictionary<string, FileCategory> ExtensionMap = new()
        {
            // Images
            [".png"] = FileCategory.Image, [".jpg"] = FileCategory.Image,
            [".jpeg"] = FileCategory.Image, [".bmp"] = FileCategory.Image,
            [".gif"] = FileCategory.Image, [".tga"] = FileCategory.Image,
            [".tiff"] = FileCategory.Image, [".webp"] = FileCategory.Image,
            [".dds"] = FileCategory.Image, [".tlg"] = FileCategory.Image,
            [".pvr"] = FileCategory.Image,
            // Audio
            [".ogg"] = FileCategory.Audio, [".wav"] = FileCategory.Audio,
            [".mp3"] = FileCategory.Audio, [".wma"] = FileCategory.Audio,
            [".aac"] = FileCategory.Audio, [".m4a"] = FileCategory.Audio,
            [".mid"] = FileCategory.Audio,
            // Video
            [".mp4"] = FileCategory.Video, [".avi"] = FileCategory.Video,
            [".wmv"] = FileCategory.Video, [".mkv"] = FileCategory.Video,
            [".ogv"] = FileCategory.Video, [".mov"] = FileCategory.Video,
            // Script
            [".ks"] = FileCategory.Script, [".tjs"] = FileCategory.Script,
            [".asd"] = FileCategory.Script, [".ksd"] = FileCategory.Script,
            [".kdt"] = FileCategory.Script, [".kep"] = FileCategory.Script,
            [".tpm"] = FileCategory.Script, [".cf"] = FileCategory.Script,
            ["._bp"] = FileCategory.Script, ["._bs"] = FileCategory.Script,
            [".src"] = FileCategory.Script, [".fas"] = FileCategory.Script,
            // Font
            [".ttf"] = FileCategory.Font, [".otf"] = FileCategory.Font,
            [".ttc"] = FileCategory.Font, [".woff"] = FileCategory.Font,
            // Archive
            [".xp3"] = FileCategory.Archive, [".arc"] = FileCategory.Archive,
            [".noa"] = FileCategory.Archive, [".rpa"] = FileCategory.Archive,
            [".pak"] = FileCategory.Archive, [".dat"] = FileCategory.Archive,
        };

        private static readonly (byte[] magic, FileCategory cat)[] MagicSignatures = {
            (new byte[] { 0xFF, 0xD8, 0xFF }, FileCategory.Image),        // JPEG
            (new byte[] { 0x89, 0x50, 0x4E, 0x47 }, FileCategory.Image),  // PNG
            (new byte[] { 0x47, 0x49, 0x46, 0x38 }, FileCategory.Image),  // GIF
            (new byte[] { 0x42, 0x4D }, FileCategory.Image),              // BMP
            (new byte[] { 0x4F, 0x67, 0x67, 0x53 }, FileCategory.Audio),  // OGG
            (new byte[] { 0x52, 0x49, 0x46, 0x46 }, FileCategory.Audio),  // WAV/RIFF
            (new byte[] { 0xFF, 0xFB }, FileCategory.Audio),              // MP3
            (new byte[] { 0xFF, 0xF3 }, FileCategory.Audio),              // MP3
            (new byte[] { 0xFF, 0xF2 }, FileCategory.Audio),              // MP3
            (new byte[] { 0x1A, 0x45, 0xDF, 0xA3 }, FileCategory.Video), // MKV/WebM
            (new byte[] { 0x00, 0x00, 0x00, 0x1C, 0x66, 0x74, 0x79, 0x70 }, FileCategory.Video), // MP4
            (new byte[] { 0x50, 0x4B, 0x03, 0x04 }, FileCategory.Archive), // ZIP
            (new byte[] { 0x1F, 0x8B }, FileCategory.Archive),            // GZIP
        };

        /// <summary>
        /// Classifies a file by reading its magic bytes.
        /// </summary>
        public static FileCategory Classify(Stream stream, string fileName)
        {
            // 1. Try magic bytes
            long origPos = stream.Position;
            try
            {
                byte[] magic = new byte[8];
                stream.Position = 0;
                int read = stream.Read(magic, 0, 8);
                if (read >= 2)
                {
                    foreach (var (sig, category) in MagicSignatures)
                    {
                        if (sig.Length <= read)
                        {
                            bool match = true;
                            for (int i = 0; i < sig.Length; i++)
                                if (magic[i] != sig[i]) { match = false; break; }
                            if (match) return category;
                        }
                    }
                }
            }
            catch { }
            finally { stream.Position = origPos; }

            // 2. Fallback to extension
            if (string.IsNullOrEmpty(fileName))
                return FileCategory.Other;

            string ext = Path.GetExtension(fileName)?.ToLowerInvariant() ?? "";
            return ExtensionMap.TryGetValue(ext, out var cat) ? cat : FileCategory.Other;
        }

        /// <summary>
        /// Gets a human-readable label for a file category.
        /// </summary>
        public static string GetCategoryLabel(FileCategory cat) => cat switch
        {
            FileCategory.Image => "图片",
            FileCategory.Audio => "音频",
            FileCategory.Video => "视频",
            FileCategory.Script => "脚本",
            FileCategory.Font => "字体",
            FileCategory.Archive => "封包",
            _ => "其他"
        };
    }

    public enum FileCategory
    {
        Other,
        Image,
        Audio,
        Video,
        Script,
        Font,
        Archive
    }
}
