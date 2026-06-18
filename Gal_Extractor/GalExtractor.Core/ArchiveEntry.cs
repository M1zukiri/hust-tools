
using System.IO;

namespace GalExtractor.Core
{
    /// <summary>
    /// Base implementation of IArchiveEntry
    /// </summary>
    public class ArchiveEntry : IArchiveEntry
    {
        public string Name { get; }
        public long Size { get; }
        public long Offset { get; }
        public object? Metadata { get; }

        public ArchiveEntry(string name, long size, long offset, object? metadata = null)
        {
            Name = name;
            Size = size;
            Offset = offset;
            Metadata = metadata;
        }

        public virtual void ExtractToStream(Stream outputStream, Stream archiveStream)
        {
            if (outputStream == null)
                throw new ArgumentNullException(nameof(outputStream));

            if (archiveStream == null)
                throw new ArgumentNullException(nameof(archiveStream));

            // Save the current position
            long originalPosition = archiveStream.Position;

            try
            {
                // Seek to the file data in the archive
                archiveStream.Seek(Offset, SeekOrigin.Begin);

                // Create a buffer to copy data
                byte[] buffer = new byte[4096];
                int bytesRead;

                // Copy data from archive to output stream
                long bytesRemaining = Size;
                while (bytesRemaining > 0 && 
                       (bytesRead = archiveStream.Read(buffer, 0, (int)Math.Min(buffer.Length, bytesRemaining))) > 0)
                {
                    outputStream.Write(buffer, 0, bytesRead);
                    bytesRemaining -= bytesRead;
                }
            }
            finally
            {
                // Restore the original position
                archiveStream.Position = originalPosition;
            }
        }
    }
}
