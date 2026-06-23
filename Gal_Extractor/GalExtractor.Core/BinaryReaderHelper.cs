using System.IO;
using System.Text;

namespace GalExtractor.Core
{
    /// <summary>
    /// Helper class for reading binary data with different endianness
    /// </summary>
    public class BinaryReaderHelper : BinaryReader
    {
        private readonly bool _isLittleEndian;

        public BinaryReaderHelper(Stream input, bool isLittleEndian = true) : base(input, Encoding.UTF8, true)
        {
            _isLittleEndian = isLittleEndian;
        }

        public BinaryReaderHelper(Stream input, Encoding encoding, bool isLittleEndian = true) : base(input, encoding, true)
        {
            _isLittleEndian = isLittleEndian;
        }

        public override short ReadInt16()
        {
            var data = base.ReadBytes(2);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToInt16(data, 0);
        }

        public override int ReadInt32()
        {
            var data = base.ReadBytes(4);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToInt32(data, 0);
        }

        public override long ReadInt64()
        {
            var data = base.ReadBytes(8);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToInt64(data, 0);
        }

        public override ushort ReadUInt16()
        {
            var data = base.ReadBytes(2);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToUInt16(data, 0);
        }

        public override uint ReadUInt32()
        {
            var data = base.ReadBytes(4);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToUInt32(data, 0);
        }

        public override ulong ReadUInt64()
        {
            var data = base.ReadBytes(8);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToUInt64(data, 0);
        }

        public override float ReadSingle()
        {
            var data = base.ReadBytes(4);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToSingle(data, 0);
        }

        public override double ReadDouble()
        {
            var data = base.ReadBytes(8);
            if (!_isLittleEndian)
                System.Array.Reverse(data);
            return System.BitConverter.ToDouble(data, 0);
        }

        /// <summary>
        /// Reads a null-terminated string
        /// </summary>
        /// <param name="encoding">The encoding to use, defaults to UTF-8</param>
        /// <returns>The read string</returns>
        public string ReadNullTerminatedString(Encoding? encoding = null)
        {
            encoding ??= Encoding.UTF8;
            var bytes = new List<byte>();
            byte b;

            while ((b = ReadByte()) != 0)
            {
                bytes.Add(b);
            }

            return encoding.GetString(bytes.ToArray());
        }

        /// <summary>
        /// Reads a fixed-length string
        /// </summary>
        /// <param name="length">The length of the string in bytes</param>
        /// <param name="encoding">The encoding to use, defaults to UTF-8</param>
        /// <param name="trimNull">Whether to trim null characters from the end</param>
        /// <returns>The read string</returns>
        public string ReadFixedLengthString(int length, Encoding? encoding = null, bool trimNull = true)
        {
            encoding ??= Encoding.UTF8;
            var bytes = ReadBytes(length);

            if (trimNull)
            {
                var nullIndex = System.Array.IndexOf(bytes, (byte)0);
                if (nullIndex >= 0)
                {
                    System.Array.Resize(ref bytes, nullIndex);
                }
            }

            return encoding.GetString(bytes);
        }
    }
}
