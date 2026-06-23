using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GalExtractor.Core;

namespace GalExtractor.Plugins.Noa
{
    public class NoaArchive : IGameArchive
    {
        private static readonly byte[] DirEntryMarker = Encoding.ASCII.GetBytes("DirEntry");

        public string EngineName => "YU-RIS";

        public string[] SupportedExtensions => new[] { ".noa" };

        public bool TryOpen(Stream stream)
        {
            if (stream == null || !stream.CanRead || stream.Length < 8) return false;
            long pos = stream.Position;
            try
            {
                byte[] magic = new byte[5];
                stream.Position = pos;
                stream.Read(magic, 0, 5);
                return magic[0] == 'E' && magic[1] == 'n' && magic[2] == 't' && magic[3] == 'i' && magic[4] == 's';
            }
            catch { return false; }
            finally { stream.Position = pos; }
        }

        public IList<IArchiveEntry> ReadTOC(Stream stream)
        {
            var entries = new List<IArchiveEntry>();
            long origPos = stream.Position;
            try
            {
                int dirOff = FindBytes(stream, DirEntryMarker);
                if (dirOff < 0) return entries;

                // Skip DirEntry + FAT header prefix
                int scan = dirOff + 8;
                var seen = new HashSet<string>();

                for (int tries = 0; tries < 100000 && scan < stream.Length - 16; tries++)
                {
                    byte[] hdr = new byte[4];
                    stream.Position = scan;
                    if (stream.Read(hdr, 0, 4) != 4) break;

                    int nameLen = BitConverter.ToInt32(hdr, 0);
                    if (nameLen < 1 || nameLen > 60) { scan += 1; continue; }

                    byte[] nameBytes = new byte[nameLen];
                    if (stream.Read(nameBytes, 0, nameLen) != nameLen) break;
                    if (!nameBytes.All(b => b >= 0x20 && b < 0x7F)) { scan += 1; continue; }
                    if (!nameBytes.Contains((byte)'.')) { scan += 1; continue; }

                    string name = Encoding.ASCII.GetString(nameBytes);
                    int afterName = scan + 4 + nameLen;
                    int aligned = (afterName + 3) & ~3;

                    stream.Position = aligned;
                    byte[] data = new byte[8];
                    if (stream.Read(data, 0, 8) != 8) break;

                    uint offset = BitConverter.ToUInt32(data, 0);
                    uint size = BitConverter.ToUInt32(data, 4);

                    if (offset + size <= stream.Length && size > 0 && size < 500_000_000 && seen.Add(name))
                    {
                        entries.Add(new ArchiveEntry(name, size, offset));
                        scan = aligned + 8;
                    }
                    else
                    {
                        scan = aligned + 8;
                    }
                }
                return entries;
            }
            finally { stream.Position = origPos; }
        }

        private static int FindBytes(Stream stream, byte[] pattern)
        {
            byte[] buf = new byte[512];
            int read = stream.Read(buf, 0, (int)Math.Min(512, stream.Length));
            for (int i = 0; i <= read - pattern.Length; i++)
            {
                bool ok = true;
                for (int j = 0; j < pattern.Length; j++)
                    if (buf[i + j] != pattern[j]) { ok = false; break; }
                if (ok) return i + pattern.Length;
            }
            return -1;
        }

        public void ExtractFile(IArchiveEntry entry, Stream archiveStream, Stream outputStream)
        {
            entry.ExtractToStream(outputStream, archiveStream);
        }
    }
}
