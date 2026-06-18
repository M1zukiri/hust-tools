
using System.IO;

namespace GalExtractor.Core
{
    /// <summary>
    /// Represents a single entry/file within a game archive
    /// </summary>
    public interface IArchiveEntry
    {
        /// <summary>
        /// The name/path of the file within the archive
        /// </summary>
        string Name { get; }

        /// <summary>
        /// The size of the file in bytes
        /// </summary>
        long Size { get; }

        /// <summary>
        /// The offset/position of the file data within the archive
        /// </summary>
        long Offset { get; }

        /// <summary>
        /// Additional metadata about the file (optional)
        /// </summary>
        object? Metadata { get; }

        /// <summary>
        /// Extracts the file content to the specified stream
        /// </summary>
        /// <param name="stream">The stream to write the extracted file to</param>
        /// <param name="archiveStream">The archive stream to read from</param>
        void ExtractToStream(Stream stream, Stream archiveStream);
    }
}
