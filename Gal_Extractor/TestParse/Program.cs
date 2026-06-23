using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GalExtractor.Core;
using GalExtractor.Plugins.Kirikiri;

class Program
{
    // Only use 4+ byte signatures to reduce false positives
    static readonly (byte[] sig, string ext, int minSize)[] Signatures = {
        (new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A }, "png", 100),   // PNG - 8 byte sig
        (new byte[] { 0xFF, 0xD8, 0xFF }, "jpg", 500),                                   // JPEG - 3 byte sig
        (new byte[] { 0x4F, 0x67, 0x67, 0x53 }, "ogg", 1000),                           // OGG - 4 byte sig
        (new byte[] { 0x52, 0x49, 0x46, 0x46 }, "wav", 100),                            // RIFF/WAV - 4 byte sig
        (new byte[] { 0x1A, 0x45, 0xDF, 0xA3 }, "mkv", 1000),                           // MKV/WebM - 4 byte sig
    };

    // BMP validation: check BITMAPFILEHEADER for real BM magic with size sanity
    static bool IsValidBmp(byte[] data)
    {
        if (data.Length < 30) return false;
        uint bfSize = BitConverter.ToUInt32(data, 2);
        uint bfOffBits = BitConverter.ToUInt32(data, 10);
        int biWidth = BitConverter.ToInt32(data, 18);
        int biHeight = BitConverter.ToInt32(data, 22);
        ushort biBitCount = BitConverter.ToUInt16(data, 28);
        // Validate: reasonable dimensions, matching file size, valid bit count
        return biWidth > 0 && biWidth < 10000 && 
               Math.Abs(biHeight) > 0 && Math.Abs(biHeight) < 10000 &&
               (biBitCount == 1 || biBitCount == 4 || biBitCount == 8 || biBitCount == 16 || biBitCount == 24 || biBitCount == 32) &&
               (bfSize >= data.Length * 0.5 && bfSize <= data.Length * 1.5);
    }

    static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("Usage: extract <path-to-xp3> <output-dir>");
            return 1;
        }

        string filePath = args[0];
        string outputDir = args[1];

        if (!File.Exists(filePath))
        {
            Console.Error.WriteLine($"File not found: {filePath}");
            return 1;
        }

        Directory.CreateDirectory(outputDir);
        Console.WriteLine($"Extracting: {filePath}");
        Console.WriteLine($"Output to:  {outputDir}");
        Console.WriteLine();

        // Method 1: Plugin-based extraction
        var pm = new PluginManager();
        pm.LoadPlugins(typeof(Xp3Archive).Assembly);
        using var stream = File.OpenRead(filePath);
        var parser = pm.FindParser(stream);
        if (parser != null)
        {
            var entries = parser.ReadTOC(stream);
            if (entries.Count > 0)
            {
                Console.WriteLine($"Found {entries.Count} indexed entries (thumbnails).");
                ExtractEntries(filePath, outputDir, entries);
                Console.WriteLine($"\nNote: These are LOW-RES thumbnails. Full images require format-specific parsing.");
                return 0;
            }
        }

        // Method 2: Smart carving with validation
        Console.WriteLine("Carving with signature validation...");
        int carved = SmartCarve(filePath, outputDir);
        Console.WriteLine($"\nDone: {carved} valid files extracted.");
        return carved > 0 ? 0 : 1;
    }

    static void ExtractEntries(string filePath, string outputDir, IList<IArchiveEntry> entries)
    {
        int ok = 0;
        for (int i = 0; i < entries.Count; i++)
        {
            var entry = entries[i];
            string name = SanitizePath(entry.Name);
            if (string.IsNullOrEmpty(name)) name = $"entry_{i:D4}.jpg";
            string outPath = Path.Combine(outputDir, name);
            try
            {
                using var fs = File.OpenRead(filePath);
                using var os = File.Create(outPath);
                fs.Seek(entry.Offset, SeekOrigin.Begin);
                var buf = new byte[65536];
                long rem = entry.Size;
                while (rem > 0)
                {
                    int n = fs.Read(buf, 0, (int)Math.Min(buf.Length, rem));
                    if (n <= 0) break;
                    os.Write(buf, 0, n);
                    rem -= n;
                }
                Console.Write("."); ok++;
            }
            catch { Console.Write("X"); }
        }
        Console.WriteLine($"\nExtracted {ok} thumbnail files to {outputDir}");
    }

    static int SmartCarve(string filePath, string outputDir)
    {
        byte[] data = File.ReadAllBytes(filePath);
        int count = 0;

        for (int i = 0; i < data.Length - 8; i++)
        {
            foreach (var (sig, ext, minSize) in Signatures)
            {
                if (i + sig.Length > data.Length) continue;
                bool match = true;
                for (int s = 0; s < sig.Length; s++)
                    if (data[i + s] != sig[s]) { match = false; break; }
                if (!match) continue;

                // Find end boundary
                int end = FindNextSig(data, i + sig.Length, out _);
                if (end < 0 || end - i > 50_000_000)
                    end = Math.Min(i + 10_000_000, data.Length);

                int fileLen = end - i;
                if (fileLen < minSize) continue; // Skip too-small files (false positives)

                // For JPEG, validate it has FF D9 end marker
                if (ext == "jpg")
                {
                    int d9pos = Array.IndexOf(data, (byte)0xD9, i + 2, Math.Min(fileLen - 2, 500000));
                    if (d9pos < 0 || data[d9pos - 1] != 0xFF) continue; // Not valid JPEG
                    end = d9pos + 1; // Cut at FF D9
                }

                string name = $"{ext}_{count:D5}.{ext}";
                string outPath = Path.Combine(outputDir, name);
                File.WriteAllBytes(outPath, data[i..end]);
                Console.Write("."); count++;
                i = end - 1;
                break;
            }
        }
        return count;
    }

    static int FindNextSig(byte[] data, int start, out string foundExt)
    {
        foundExt = null;
        for (int i = start; i < data.Length - 2; i++)
        {
            foreach (var (sig, ext, _) in Signatures)
            {
                if (i + sig.Length > data.Length) continue;
                bool match = true;
                for (int s = 0; s < sig.Length; s++)
                    if (data[i + s] != sig[s]) { match = false; break; }
                if (match) { foundExt = ext; return i; }
            }
        }
        return -1;
    }

    static string SanitizePath(string path)
    {
        if (string.IsNullOrEmpty(path)) return path;
        var inv = Path.GetInvalidFileNameChars();
        var c = path.ToCharArray();
        for (int i = 0; i < c.Length; i++)
            if (Array.IndexOf(inv, c[i]) >= 0) c[i] = '_';
        return new string(c);
    }
}
