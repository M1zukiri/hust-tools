
using System.Collections.Generic;
using System.IO;

namespace GalExtractor.Core
{
    /// <summary>
    /// Interface for implementing game archive parsers
    /// </summary>
    public interface IGameArchive
    {
        /// <summary>
        /// The name of the engine this parser handles (e.g., "Ren'Py", "Kirikiri")
        /// </summary>
        string EngineName { get; }

        /// <summary>
        /// The file extensions this parser can handle (e.g., ".rpa", ".xp3")
        /// </summary>
        string[] SupportedExtensions { get; }

        /// <summary>
        /// Attempts to open and determine if the file can be parsed by this engine
        /// </summary>
        /// <param name="stream">The file stream to check</param>
        /// <returns>True if this parser can handle the file, false otherwise</returns>
        bool TryOpen(Stream stream);

        /// <summary>
        /// Parses the Table of Contents and returns a list of all entries in the archive
        /// </summary>
        /// <param name="stream">The archive stream to read from</param>
        /// <returns>A list of archive entries</returns>
        IList<IArchiveEntry> ReadTOC(Stream stream);

        /// <summary>
        /// Extracts a specific file entry to a stream
        /// </summary>
        /// <param name="entry">The entry to extract</param>
        /// <param name="archiveStream">The archive stream to read from</param>
        /// <param name="outputStream">The stream to write the extracted file to</param>
        void ExtractFile(IArchiveEntry entry, Stream archiveStream, Stream outputStream);
    }
}
