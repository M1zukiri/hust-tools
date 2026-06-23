using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using GalExtractor.Core;

namespace GalExtractor.Plugins.Circus
{
    /// <summary>
    /// Parser for CIRCUS/DreamSoft engine archive (.arc) files
    /// 
    /// Supports two variants:
    /// 
    /// 1. "PackFile" format (old CIRCUS/Propeller engine)
    ///    Used by: 秽翼的尤斯蒂娅 (Aetas/Propeller)
    ///    - Magic: "PackFile    " (12 bytes + spaces)
    ///    - File count: 4 bytes LE at offset 12
    ///    - Directory: 32-byte entries: [name(16)][offset(4)][size(4)][pad(8)]
    ///    - Data follows the directory
    /// 
    /// 2. "BURIKO ARC20" format (modern CIRCUS BURIKO engine)
    ///    Used by: 巧克甜恋/巧可甜恋 series, 宝石夜乐园, 霞流宝石心
    ///    - Magic: "BURIKO ARC20" (12 bytes)
    ///    - Entry count: 4 bytes LE at offset 12
    ///    - Directory: 128-byte entries: [name at 0, offset at 96, size at 100]
    ///    - Data starts after the directory
    /// </summary>
    public class ArcArchive : IGameArchive
    {
        private const string PackFileMagic = "PackFile    ";  // 12 chars
        private const string BurikoMagic = "BURIKO ARC20";   // 12 chars

        private enum ArcFormat { Unknown, PackFile, Buriko }

        public string EngineName => "CIRCUS";

        public string[] SupportedExtensions => new[] { ".arc" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 16)
                return false;

            long originalPosition = stream.Position;

            try
            {
                byte[] magicBytes = new byte[12];
                stream.Position = originalPosition;
                if (stream.Read(magicBytes, 0, 12) != 12)
                    return false;

                string magic = Encoding.ASCII.GetString(magicBytes);
                return magic == PackFileMagic || magic == BurikoMagic;
            }
            catch
            {
                return false;
            }
            finally
            {
                stream.Position = originalPosition;
            }
        }

        public IList<IArchiveEntry> ReadTOC(Stream stream)
        {
            if (stream == null)
                throw new ArgumentNullException(nameof(stream));

            var entries = new List<IArchiveEntry>();
            long originalPosition = stream.Position;

            try
            {
                byte[] magicBytes = new byte[12];
                stream.Position = originalPosition;
                stream.Read(magicBytes, 0, 12);
                string magic = Encoding.ASCII.GetString(magicBytes);

                var format = DetectFormat(magic);
                switch (format)
                {
                    case ArcFormat.PackFile:
                        ReadPackFileTOC(stream, entries);
                        break;
                    case ArcFormat.Buriko:
                        ReadBurikoTOC(stream, entries);
                        break;
                    default:
                        throw new NotSupportedException($"Unknown ARC format: {magic}");
                }

                return entries;
            }
            finally
            {
                stream.Position = originalPosition;
            }
        }

        private ArcFormat DetectFormat(string magic)
        {
            if (magic == PackFileMagic) return ArcFormat.PackFile;
            if (magic == BurikoMagic) return ArcFormat.Buriko;
            return ArcFormat.Unknown;
        }

        private void ReadPackFileTOC(Stream stream, List<IArchiveEntry> entries)
        {
            using var reader = new BinaryReaderHelper(stream, Encoding.ASCII);

            // Skip magic (12 bytes already read + 4 bytes file count)
            // Actually, stream is at position 12 after reading magic
            int fileCount = reader.ReadInt32(); // 4 bytes at offset 12
            const int entrySize = 32;

            for (int i = 0; i < fileCount; i++)
            {
                long entryStart = 16 + i * entrySize;
                stream.Position = entryStart;

                // Read filename (16 bytes, null-padded ASCII)
                byte[] nameBytes = reader.ReadBytes(16);
                string name = ReadNullTerminatedAscii(nameBytes);

                // Read offset and size
                uint offset = reader.ReadUInt32();
                uint size = reader.ReadUInt32();

                // Skip padding (8 bytes)
                reader.ReadBytes(8);

                entries.Add(new ArchiveEntry(name, size, offset));
            }
        }

        private void ReadBurikoTOC(Stream stream, List<IArchiveEntry> entries)
        {
            using var reader = new BinaryReaderHelper(stream, Encoding.ASCII);

            // Read entry count (4 bytes at offset 12)
            int fileCount = reader.ReadInt32(); // Note: stream is at pos 12 after magic
            const int entrySize = 128;

            // Directory starts at offset 16
            long directoryStart = 16;

            for (int i = 0; i < fileCount; i++)
            {
                long entryStart = directoryStart + i * entrySize;
                stream.Position = entryStart;

                // Read the full 128-byte entry
                byte[] entryData = reader.ReadBytes(entrySize);

                // Extract filename (null-terminated ASCII, starts at offset 0 within entry)
                string name = ReadNullTerminatedAscii(entryData, 0, 96);

                // Extract offset (4 bytes at offset 96 within entry)
                uint offset = BitConverter.ToUInt32(entryData, 96);

                // Extract size (4 bytes at offset 100 within entry)
                uint size = BitConverter.ToUInt32(entryData, 100);

                if (!string.IsNullOrEmpty(name) && size > 0)
                {
                    entries.Add(new ArchiveEntry(name, size, offset));
                }
            }
        }

        public void ExtractFile(IArchiveEntry entry, Stream archiveStream, Stream outputStream)
        {
            if (entry == null)
                throw new ArgumentNullException(nameof(entry));
            if (archiveStream == null)
                throw new ArgumentNullException(nameof(archiveStream));
            if (outputStream == null)
                throw new ArgumentNullException(nameof(outputStream));

            entry.ExtractToStream(outputStream, archiveStream);
        }

        /// <summary>
        /// Reads a null-terminated ASCII string from a byte array
        /// </summary>
        private static string ReadNullTerminatedAscii(byte[] data, int startIndex = 0, int maxLength = 96)
        {
            int end = startIndex;
            while (end < data.Length && end - startIndex < maxLength && data[end] != 0)
                end++;

            if (end <= startIndex)
                return string.Empty;

            return Encoding.ASCII.GetString(data, startIndex, end - startIndex);
        }
    }
}
