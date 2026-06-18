
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
    /// </summary>
    public class RpaArchive : IGameArchive
    {
        public string EngineName => "Ren'Py";

        public string[] SupportedExtensions => new[] { ".rpa", ".rpi", ".rpb" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 20)
                return false;

            // Save the current position
            long originalPosition = stream.Position;

            try
            {
                // Read the header to check if it's an RPA file
                using var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                // RPA 3.0+ files start with "RPA-3.0 "
                // RPA 2.0 files start with "RPA-2.0 "
                // Older RPA files start with "RPA-1.0"
                var header = reader.ReadFixedLengthString(20);

                return header.StartsWith("RPA-");
            }
            catch
            {
                return false;
            }
            finally
            {
                // Restore the original position
                stream.Position = originalPosition;
            }
        }

        public IList<IArchiveEntry> ReadTOC(Stream stream)
        {
            if (stream == null)
                throw new ArgumentNullException(nameof(stream));

            var entries = new List<IArchiveEntry>();

            // Save the current position
            long originalPosition = stream.Position;

            try
            {
                using var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                // Read the header
                var header = reader.ReadFixedLengthString(20);
                int version = 0;
                long offset = 0;
                int key = 0;
                bool isEncrypted = false;

                if (header.StartsWith("RPA-3.0"))
                {
                    // RPA 3.0 format
                    version = 3;
                    offset = reader.ReadUInt32();
                    key = reader.ReadUInt32();
                    if (key != 0)
                        isEncrypted = true;
                }
                else if (header.StartsWith("RPA-2.0"))
                {
                    // RPA 2.0 format
                    version = 2;
                    offset = reader.ReadUInt32();
                    key = reader.ReadUInt32();
                    if (key != 0)
                        isEncrypted = true;
                }
                else if (header.StartsWith("RPA-1.0"))
                {
                    // RPA 1.0 format
                    version = 1;
                    offset = reader.ReadUInt32();
                }
                else
                {
                    throw new NotSupportedException("Unsupported RPA version");
                }

                // Jump to the table of contents
                stream.Position = offset;

                // Read the TOC
                if (version == 1)
                {
                    // RPA 1.0 format - simple pickle format
                    ReadTOCv1(reader, entries, key, isEncrypted);
                }
                else if (version == 2 || version == 3)
                {
                    // RPA 2.0/3.0 format - zlib compressed pickle
                    ReadTOCv2v3(reader, entries, key, isEncrypted, version);
                }

                return entries;
            }
            finally
            {
                // Restore the original position
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

            // Use the default implementation
            entry.ExtractToStream(outputStream, archiveStream);
        }

        private void ReadTOCv1(BinaryReaderHelper reader, List<IArchiveEntry> entries, int key, bool isEncrypted)
        {
            // RPA 1.0 has a simple pickle format
            // This is a simplified implementation
            // In a real implementation, you would need to parse the pickle format

            // For demonstration purposes, we'll use a simple approach
            // In reality, you would need to implement a proper pickle parser

            // Read the number of entries
            int numEntries = reader.ReadUInt32();

            for (int i = 0; i < numEntries; i++)
            {
                // Read file name length and name
                int nameLength = reader.ReadUInt32();
                string name = reader.ReadFixedLengthString(nameLength);

                // Read file offset and length
                long offset = reader.ReadUInt32();
                int length = reader.ReadUInt32();

                // Add the entry
                entries.Add(new ArchiveEntry(name, length, offset));
            }
        }

        private void ReadTOCv2v3(BinaryReaderHelper reader, List<IArchiveEntry> entries, int key, bool isEncrypted, int version)
        {
            // RPA 2.0/3.0 uses zlib compressed pickle format
            // This is a simplified implementation
            // In a real implementation, you would need to decompress and parse the pickle format

            // For demonstration purposes, we'll use a simple approach
            // In reality, you would need to implement a proper pickle parser

            // Read the compressed data length
            int compressedLength = reader.ReadUInt32();

            // Read the compressed data
            byte[] compressedData = reader.ReadBytes(compressedLength);

            // Decompress the data
            byte[] decompressedData;
            using (var compressedStream = new MemoryStream(compressedData))
            using (var decompressionStream = new System.IO.Compression.DeflateStream(compressedStream, System.IO.Compression.CompressionMode.Decompress))
            using (var resultStream = new MemoryStream())
            {
                decompressionStream.CopyTo(resultStream);
                decompressedData = resultStream.ToArray();
            }

            // Parse the pickle data
            // This is a simplified implementation
            // In reality, you would need to implement a proper pickle parser

            // For demonstration purposes, we'll assume a simple format
            // In reality, the pickle format is more complex

            using var dataStream = new MemoryStream(decompressedData);
            using var dataReader = new BinaryReaderHelper(dataStream);

            // Read the number of entries
            int numEntries = dataReader.ReadUInt32();

            for (int i = 0; i < numEntries; i++)
            {
                // Read file name length and name
                int nameLength = dataReader.ReadUInt32();
                string name = dataReader.ReadFixedLengthString(nameLength);

                // Read file offset and length
                long offset = dataReader.ReadUInt32();
                int length = dataReader.ReadUInt32();

                // Add the entry
                entries.Add(new ArchiveEntry(name, length, offset));
            }
        }
    }
}
