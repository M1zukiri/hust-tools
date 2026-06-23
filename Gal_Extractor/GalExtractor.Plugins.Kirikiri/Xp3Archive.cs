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
    /// 
    /// Supports both:
    /// - Standard XP3 format (with "Adpe" index, header ends with 0x53/'S')
    /// - Extended XP3 variant (big-endian per-file headers, header ends with 0x01)
    ///   Used by Chinese game repacks. Each file entry has a 32-byte big-endian header
    ///   containing: marker(0x02020004), count(1), data_size, metadata
    /// </summary>
    public class Xp3Archive : IGameArchive
    {
        // XP3 magic header (first 10 bytes are fixed, 11th byte is a version flag)
        // Standard: XP3[0x0D][0x0A][0x20][0x0A][0x1A][0x8B]g + version byte
        // Common version values: 0x53 ('S'), 0x01 (Chinese repacks)
        private static readonly byte[] Xp3MagicPrefix = {
            0x58, 0x50, 0x33, 0x0D, 0x0A, 0x20, 0x0A, 0x1A, 0x8B, 0x67
        };

        // BE entry header magic constant
        private const uint BeEntryMagic = 0x02020004;

        public string EngineName => "Kirikiri";

        public string[] SupportedExtensions => new[] { ".xp3" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 11)
                return false;

            long originalPosition = stream.Position;

            try
            {
                var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                var header = reader.ReadBytes(11);
                // Check first 10 bytes (fixed magic), skip 11th which is a version variant
                return header.Length >= 11 &&
                       header[0] == Xp3MagicPrefix[0] &&
                       header[1] == Xp3MagicPrefix[1] &&
                       header[2] == Xp3MagicPrefix[2] &&
                       header[3] == Xp3MagicPrefix[3] &&
                       header[4] == Xp3MagicPrefix[4] &&
                       header[5] == Xp3MagicPrefix[5] &&
                       header[6] == Xp3MagicPrefix[6] &&
                       header[7] == Xp3MagicPrefix[7] &&
                       header[8] == Xp3MagicPrefix[8] &&
                       header[9] == Xp3MagicPrefix[9];
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
                var reader = new BinaryReaderHelper(stream);
                stream.Position = originalPosition;

                // Read magic
                byte[] magic = reader.ReadBytes(11);
                
                // Check if this is the "Adpe" (standard) variant or the 0x01 (BE variant)
                bool isStandardVariant = (magic[10] == 0x53); // ends with 'S'

                if (isStandardVariant)
                {
                    ReadStandardTOC(stream, reader, entries);
                }
                else
                {
                    ReadExtendedTOC(stream, reader, entries);
                }

                return entries;
            }
            finally
            {
                stream.Position = originalPosition;
            }
        }

        /// <summary>
        /// Reads standard XP3 with "Adpe" index format
        /// </summary>
        private void ReadStandardTOC(Stream stream, BinaryReaderHelper reader, List<IArchiveEntry> entries)
        {
            // Skip additional header if present
            if (reader.ReadByte() == 1)
            {
                int headerSize = reader.ReadInt32();
                reader.ReadBytes(headerSize);
            }

            long indexOffset = reader.ReadInt64();
            long indexSize = reader.ReadInt64();

            stream.Position = indexOffset;

            long indexChunkSize = reader.ReadInt64();
            if (reader.ReadBytes(4).SequenceEqual(new byte[] { 0x41, 0x64, 0x70, 0x65 })) // "Adpe"
            {
                int fileCount = reader.ReadInt32();

                for (int i = 0; i < fileCount; i++)
                {
                    int fileInfoSize = reader.ReadInt32();
                    long fileStartPos = stream.Position;

                    bool isEncrypted = reader.ReadByte() != 0;
                    long originalSize = reader.ReadInt64();
                    long compressedSize = reader.ReadInt64();
                    short nameLength = reader.ReadInt16();
                    string fileName = reader.ReadFixedLengthString(nameLength);
                    long fileOffset = reader.ReadInt64();

                    entries.Add(new Xp3ArchiveEntry(fileName, originalSize, fileOffset, compressedSize, isEncrypted));
                    stream.Position = fileStartPos + fileInfoSize;
                }
            }
        }

        /// <summary>
        /// Reads extended XP3 variant with big-endian 32-byte per-file headers
        /// After the 11-byte magic, there's metadata followed by inline file entries:
        /// [32-byte BE header][JPEG preview data][actual resource data]
        /// 
        /// The BE header structure:
        ///   [0-3]:   marker = 0x02020004
        ///   [4-7]:   count = 1
        ///   [8-11]:  data_size (big-endian) - size of the immediate file data (JPEG)
        ///   [12-15]: padding = 0
        ///   [16-19]: dimension/attribute 1
        ///   [20-23]: unknown, usually 1
        ///   [24-27]: dimension/attribute 2  
        ///   [28-31]: unknown, usually 1
        /// </summary>
        private void ReadExtendedTOC(Stream stream, BinaryReaderHelper reader, List<IArchiveEntry> entries)
        {
            // Scan the file for entries with the big-endian header pattern
            // Each entry starts with a 32-byte big-endian header followed by data
            // We scan for JPEG SOI markers (FF D8) preceded by the BE header pattern
            
            long fileLength = stream.Length;
            long scanPosition = 32; // skip past initial 'az' marker area
            
            int entryIndex = 0;
            byte[] buffer = new byte[4];
            
            while (scanPosition + 32 < fileLength)
            {
                stream.Position = scanPosition;
                
                // Look for FF D8 (JPEG SOI marker) preceded by 32 bytes
                int readCount = stream.Read(buffer, 0, 1);
                if (readCount < 1)
                    break;
                    
                if (buffer[0] == 0xFF)
                {
                    if (stream.ReadByte() == 0xD8 && scanPosition >= 32)
                    {
                        // Check if the 32 bytes before this position form a valid BE header
                        long headerPos = scanPosition - 32;
                        stream.Position = headerPos;
                        
                        byte[] header = new byte[32];
                        if (stream.Read(header, 0, 32) == 32)
                        {
                            uint marker = ReadBigEndianUInt32(header, 0);
                            uint count = ReadBigEndianUInt32(header, 4);
                            uint dataSize = ReadBigEndianUInt32(header, 8);
                            
                            if (marker == BeEntryMagic && count == 1 && dataSize > 0 && dataSize < fileLength)
                            {
                                // Found a valid entry! Extract name and size
                                // The JPEG data starts at scanPosition and has dataSize bytes
                                // After that, there may be additional data
                                uint dim1 = ReadBigEndianUInt32(header, 16);
                                uint dim2 = ReadBigEndianUInt32(header, 24);
                                
                                // Generate a name for this entry
                                string entryName = GenerateEntryName(entryIndex, scanPosition, dataSize, dim1, dim2);
                                
                                entries.Add(new Xp3ArchiveEntry(
                                    entryName,
                                    dataSize,  // original size (JPEG data size)
                                    (long)scanPosition,  // offset
                                    dataSize,  // compressed = same (no compression info here)
                                    false
                                ));
                                
                                entryIndex++;
                                
                                // Skip past this entry's JPEG data to continue scanning
                                scanPosition = scanPosition + dataSize;
                                continue;
                            }
                        }
                    }
                }
                
                scanPosition++;
            }
        }

        /// <summary>
        /// Generates a descriptive name for an entry based on its position and attributes
        /// </summary>
        private string GenerateEntryName(int index, long offset, uint dataSize, uint dim1, uint dim2)
        {
            // Determine file extension based on magic bytes (we read the actual data)
            // But since we're just building the TOC, use a generic name
            string ext = "dat";
            if (dataSize >= 2)
            {
                // Check file type by extension or position
                ext = "jpg"; // Most entries in this variant are JPEG previews
            }
            
            return $"entry_{index:D4}_{offset:D8}.{ext}";
        }

        /// <summary>
        /// Reads a 32-bit unsigned integer in big-endian from a byte array
        /// </summary>
        private static uint ReadBigEndianUInt32(byte[] data, int offset)
        {
            return (uint)((data[offset] << 24) | (data[offset + 1] << 16) | 
                          (data[offset + 2] << 8) | data[offset + 3]);
        }

        public void ExtractFile(IArchiveEntry entry, Stream archiveStream, Stream outputStream)
        {
            if (entry == null)
                throw new ArgumentNullException(nameof(entry));

            if (archiveStream == null)
                throw new ArgumentNullException(nameof(archiveStream));

            if (outputStream == null)
                throw new ArgumentNullException(nameof(outputStream));

            // Use the default implementation (ArchiveEntry.ExtractToStream)
            entry.ExtractToStream(outputStream, archiveStream);
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
