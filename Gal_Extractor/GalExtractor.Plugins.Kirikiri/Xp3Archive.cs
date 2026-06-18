
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GalExtractor.Core;

namespace GalExtractor.Plugins.Kirikiri
{
    /// <summary>
    /// Parser for Kirikiri archive (.xp3) files
    /// </summary>
    public class Xp3Archive : IGameArchive
    {
        public string EngineName => "Kirikiri";

        public string[] SupportedExtensions => new[] { ".xp3" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 11)
                return false;

            // Save the current position
            long originalPosition = stream.Position;

            try
            {
                // Read the header to check if it's an XP3 file
                using var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                // XP3 files start with "XP3
 
gS"
                var header = reader.ReadBytes(11);

                return header.Length >= 11 && 
                       header[0] == 0x58 && // 'X'
                       header[1] == 0x50 && // 'P'
                       header[2] == 0x33 && // '3'
                       header[3] == 0x0D && // ''
                       header[4] == 0x0A && // '
'
                       header[5] == 0x20 && // ' '
                       header[6] == 0x0A && // '
'
                       header[7] == 0x1A && // Ctrl+Z
                       header[8] == 0x8B && // 0x8B
                       header[9] == 0x67 && // 'g'
                       header[10] == 0x53;  // 'S'
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

                // Skip the header
                reader.ReadBytes(11);

                // Check if there's an additional header
                if (reader.ReadByte() == 1)
                {
                    // Skip the additional header
                    int headerSize = reader.ReadInt32();
                    reader.ReadBytes(headerSize);
                }

                // Read the file index
                long indexOffset = reader.ReadInt64();
                long indexSize = reader.ReadInt64();

                // Jump to the index
                stream.Position = indexOffset;

                // Read the index chunk
                long indexChunkSize = reader.ReadInt64();
                if (reader.ReadBytes(4).SequenceEqual(new byte[] { 0x41, 0x64, 0x70, 0x65 })) // "Adpe"
                {
                    // Read the number of files
                    int fileCount = reader.ReadInt32();

                    for (int i = 0; i < fileCount; i++)
                    {
                        // Read file info
                        int fileInfoSize = reader.ReadInt32();
                        long fileStartPos = stream.Position;

                        // Read encryption flag
                        bool isEncrypted = reader.ReadByte() != 0;

                        // Read original size
                        long originalSize = reader.ReadInt64();

                        // Read compressed size
                        long compressedSize = reader.ReadInt64();

                        // Read file name length and name
                        short nameLength = reader.ReadInt16();
                        string fileName = reader.ReadFixedLengthString(nameLength);

                        // Read file offset
                        long fileOffset = reader.ReadInt64();

                        // Add the entry
                        entries.Add(new Xp3ArchiveEntry(
                            fileName,
                            originalSize,
                            fileOffset,
                            compressedSize,
                            isEncrypted
                        ));

                        // Skip any remaining data in the file info
                        stream.Position = fileStartPos + fileInfoSize;
                    }
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

            // Special handling for XP3 entries
            if (entry is Xp3ArchiveEntry xp3Entry)
            {
                ExtractXp3File(xp3Entry, archiveStream, outputStream);
            }
            else
            {
                // Use the default implementation
                entry.ExtractToStream(outputStream, archiveStream);
            }
        }

        private void ExtractXp3File(Xp3ArchiveEntry entry, Stream archiveStream, Stream outputStream)
        {
            // Save the current position
            long originalPosition = archiveStream.Position;

            try
            {
                // Seek to the file data in the archive
                archiveStream.Seek(entry.Offset, SeekOrigin.Begin);

                // Read the file chunk header
                using var reader = new BinaryReaderHelper(archiveStream);

                // Skip the chunk size
                reader.ReadInt64();

                // Check if it's a "File" chunk
                if (reader.ReadBytes(4).SequenceEqual(new byte[] { 0x46, 0x69, 0x6C, 0x65 })) // "File"
                {
                    // Read the segment count
                    int segmentCount = reader.ReadInt32();

                    for (int i = 0; i < segmentCount; i++)
                    {
                        // Read segment info
                        bool isCompressed = reader.ReadByte() != 0;

                        // Read segment size
                        long segmentSize = reader.ReadInt64();

                        // Read the segment data
                        byte[] segmentData = reader.ReadBytes((int)segmentSize);

                        if (isCompressed)
                        {
                            // Decompress the segment
                            using (var compressedStream = new MemoryStream(segmentData))
                            using (var decompressionStream = new System.IO.Compression.DeflateStream(compressedStream, System.IO.Compression.CompressionMode.Decompress))
                            {
                                decompressionStream.CopyTo(outputStream);
                            }
                        }
                        else
                        {
                            // Write the segment data as-is
                            outputStream.Write(segmentData, 0, segmentData.Length);
                        }
                    }
                }
            }
            finally
            {
                // Restore the original position
                archiveStream.Position = originalPosition;
            }
        }
    }

    /// <summary>
    /// Represents a file entry in an XP3 archive
    /// </summary>
    public class Xp3ArchiveEntry : ArchiveEntry
    {
        public long CompressedSize { get; }
        public bool IsEncrypted { get; }

        public Xp3ArchiveEntry(string name, long size, long offset, long compressedSize, bool isEncrypted)
            : base(name, size, offset)
        {
            CompressedSize = compressedSize;
            IsEncrypted = isEncrypted;
        }
    }
}
