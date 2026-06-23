using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GalExtractor.Core;

namespace GalExtractor.Plugins.RenPy
{
    /// <summary>
    /// Parser for Ren'Py archive (.rpa) files
    /// ⚠ EXPERIMENTAL — This is a simplified placeholder implementation.
    /// Ren'Py uses Python pickle serialization for its TOC, which this code
    /// does NOT fully implement. Most real .rpa files will NOT parse correctly.
    /// </summary>
    public class RpaArchive : IGameArchive
    {
        public string EngineName => "Ren'Py";

        public string[] SupportedExtensions => new[] { ".rpa", ".rpi", ".rpb" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 20)
                return false;

            long originalPosition = stream.Position;

            try
            {
                using var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                var header = reader.ReadFixedLengthString(20);
                return header.StartsWith("RPA-");
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
                using var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                var header = reader.ReadFixedLengthString(20);
                int version = 0;
                uint offset = 0;
                uint key = 0;
                bool isEncrypted = false;

                if (header.StartsWith("RPA-3.0"))
                {
                    version = 3;
                    offset = reader.ReadUInt32();
                    key = reader.ReadUInt32();
                    if (key != 0)
                        isEncrypted = true;
                }
                else if (header.StartsWith("RPA-2.0"))
                {
                    version = 2;
                    offset = reader.ReadUInt32();
                    key = reader.ReadUInt32();
                    if (key != 0)
                        isEncrypted = true;
                }
                else if (header.StartsWith("RPA-1.0"))
                {
                    version = 1;
                    offset = reader.ReadUInt32();
                }
                else
                {
                    throw new NotSupportedException("Unsupported RPA version");
                }

                stream.Position = offset;

                if (version == 1)
                {
                    ReadTOCv1(reader, entries, (int)key, isEncrypted);
                }
                else if (version == 2 || version == 3)
                {
                    ReadTOCv2v3(reader, entries, (int)key, isEncrypted, version);
                }

                return entries;
            }
            finally
            {
                stream.Position = originalPosition;
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

        private void ReadTOCv1(BinaryReaderHelper reader, List<IArchiveEntry> entries, int key, bool isEncrypted)
        {
            uint numEntries = reader.ReadUInt32();

            for (uint i = 0; i < numEntries; i++)
            {
                uint nameLength = reader.ReadUInt32();
                string name = reader.ReadFixedLengthString((int)nameLength);

                uint fileOffset = reader.ReadUInt32();
                uint length = reader.ReadUInt32();

                entries.Add(new ArchiveEntry(name, (long)length, (long)fileOffset));
            }
        }

        private void ReadTOCv2v3(BinaryReaderHelper reader, List<IArchiveEntry> entries, int key, bool isEncrypted, int version)
        {
            uint compressedLength = reader.ReadUInt32();

            byte[] compressedData = reader.ReadBytes((int)compressedLength);

            byte[] decompressedData;
            using (var compressedStream = new MemoryStream(compressedData))
            using (var decompressionStream = new System.IO.Compression.DeflateStream(compressedStream, System.IO.Compression.CompressionMode.Decompress))
            using (var resultStream = new MemoryStream())
            {
                decompressionStream.CopyTo(resultStream);
                decompressedData = resultStream.ToArray();
            }

            using var dataStream = new MemoryStream(decompressedData);
            using var dataReader = new BinaryReaderHelper(dataStream);

            uint numEntries = dataReader.ReadUInt32();

            for (uint i = 0; i < numEntries; i++)
            {
                uint nameLength = dataReader.ReadUInt32();
                string name = dataReader.ReadFixedLengthString((int)nameLength);

                uint fileOffset = dataReader.ReadUInt32();
                uint length = dataReader.ReadUInt32();

                entries.Add(new ArchiveEntry(name, (long)length, (long)fileOffset));
            }
        }
    }
}
