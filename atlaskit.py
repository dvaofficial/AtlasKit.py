import struct
import zlib
import sys
import logging

"""
This script is a fork of arkit.py - created by https://github.com/projekt-umbrella
"""

__author__ = "DVA"
__contact__ = "me[at]dva.gg"
__copyright__ = "Copyright 2024, DVA.gg"
__version__ = "0.0.0.1"
__status__ = "Alpha"
__date__ = "11 November 2024"
__license__ = "GPL v3.0"

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class UnpackException(Exception):
    pass


class SignatureUnpackException(UnpackException):
    pass


class CorruptUnpackException(UnpackException):
    pass


def unpack(src, dst):

    #Unpacks Atlas's Steam Workshop *.z archives.

    # Open source file in binary read mode and destination file in binary write mode
    try:
        with open(src, 'rb') as f:
            sigver, = struct.unpack('q', f.read(8))

            # Validate signature and version
            if sigver != 2653586369:
                raise SignatureUnpackException(f"Invalid signature: {sigver}")

            # Read sizes from header
            size_unpacked_chunk, = struct.unpack('q', f.read(8))
            size_packed, = struct.unpack('q', f.read(8))
            size_unpacked, = struct.unpack('q', f.read(8))

            logging.info("Archive is valid. Sizes - Unpacked Chunk: %s, Full Packed: %s, Full Unpacked: %s",
                         size_unpacked_chunk, size_packed, size_unpacked)

            # Build compression index
            compression_index = []
            size_indexed = 0
            while size_indexed < size_unpacked:
                compressed, = struct.unpack('q', f.read(8))
                uncompressed, = struct.unpack('q', f.read(8))
                compression_index.append((compressed, uncompressed))
                size_indexed += uncompressed

            if size_unpacked != size_indexed:
                raise CorruptUnpackException("Header-Index mismatch.")

            # Decompress data
            data = bytearray()
            for idx, (compressed, uncompressed) in enumerate(compression_index):
                compressed_data = f.read(compressed)
                uncompressed_data = zlib.decompress(compressed_data)

                if len(uncompressed_data) != uncompressed:
                    raise CorruptUnpackException(f"Uncompressed size mismatch at index {idx}")

                data.extend(uncompressed_data)

        # Write data to destination
        with open(dst, 'wb') as out_file:
            out_file.write(data)

        logging.info("Archive has been successfully extracted to %s.", dst)

    except (OSError, struct.error, zlib.error) as e:
        logging.critical("An error occurred: %s", e)
        raise UnpackException("File processing error") from e
