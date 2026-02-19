"""
Test edge cases, error handling, and module constants.
"""

import zlib as cpython_zlib
import pytest
import zlib_rs


class TestConstants:
    """Verify all zlib constants are exposed."""

    def test_compression_levels(self):
        assert zlib_rs.Z_NO_COMPRESSION == 0
        assert zlib_rs.Z_BEST_SPEED == 1
        assert zlib_rs.Z_BEST_COMPRESSION == 9
        assert zlib_rs.Z_DEFAULT_COMPRESSION == -1

    def test_strategies(self):
        assert zlib_rs.Z_FILTERED == 1
        assert zlib_rs.Z_HUFFMAN_ONLY == 2
        assert zlib_rs.Z_RLE == 3
        assert zlib_rs.Z_FIXED == 4
        assert zlib_rs.Z_DEFAULT_STRATEGY == 0

    def test_flush_modes(self):
        assert zlib_rs.Z_NO_FLUSH == 0
        assert zlib_rs.Z_PARTIAL_FLUSH == 1
        assert zlib_rs.Z_SYNC_FLUSH == 2
        assert zlib_rs.Z_FULL_FLUSH == 3
        assert zlib_rs.Z_FINISH == 4
        assert zlib_rs.Z_BLOCK == 5
        assert zlib_rs.Z_TREES == 6

    def test_other_constants(self):
        assert zlib_rs.Z_DEFLATED == 8
        assert zlib_rs.DEF_MEM_LEVEL == 8
        assert zlib_rs.MAX_WBITS == 15

    def test_version_strings(self):
        assert isinstance(zlib_rs.ZLIB_VERSION, str)
        assert isinstance(zlib_rs.ZLIB_RUNTIME_VERSION, str)


class TestModuleMetadata:
    """Test module-level metadata."""

    def test_version_attribute(self):
        assert hasattr(zlib_rs, "__version__")
        assert isinstance(zlib_rs.__version__, str)

    def test_author_attribute(self):
        assert hasattr(zlib_rs, "__author__")

    def test_license_attribute(self):
        assert hasattr(zlib_rs, "__license__")
        assert zlib_rs.__license__ == "MIT"


class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_compress_all_zeros(self):
        data = b"\x00" * 65536
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_compress_all_ones(self):
        data = b"\xff" * 65536
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_compress_alternating_bytes(self):
        data = (b"\x00\xff") * 32768
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_compress_sequential_bytes(self):
        data = bytes(range(256)) * 256
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_compress_highly_redundant(self):
        """Highly redundant data should achieve very high compression ratio."""
        data = b"AAAA" * 100000
        compressed = zlib_rs.compress(data, 9)
        ratio = len(data) / len(compressed)
        assert ratio > 100  # Should compress extremely well
        assert zlib_rs.decompress(compressed) == data

    def test_compress_random_data(self):
        """Random data should still roundtrip, even if not very compressible."""
        import os
        data = os.urandom(10000)
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_various_data_sizes(self):
        """Test roundtrip with various exact sizes."""
        for size in [0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128,
                     255, 256, 511, 512, 1023, 1024, 4095, 4096, 8191, 8192,
                     16383, 16384, 32767, 32768, 65535, 65536]:
            data = b"X" * size
            compressed = zlib_rs.compress(data)
            assert zlib_rs.decompress(compressed) == data, f"Failed at size {size}"


class TestCompressObjEdgeCases:
    """Edge cases for streaming compression."""

    def test_compressobj_only_flush(self):
        """Calling flush without compress should produce valid empty output."""
        c = zlib_rs.compressobj()
        result = c.flush()
        d = zlib_rs.decompressobj()
        assert d.decompress(result) == b""

    def test_compressobj_many_small_chunks(self):
        """Many tiny chunks should produce valid output."""
        data = b"A" * 500
        c = zlib_rs.compressobj()
        compressed = b""
        for i in range(0, len(data), 5):
            compressed += c.compress(data[i:i + 5])
        compressed += c.flush()

        assert zlib_rs.decompress(compressed) == data

    def test_invalid_flush_mode(self):
        c = zlib_rs.compressobj()
        c.compress(b"test")
        with pytest.raises(ValueError):
            c.flush(99)

    def test_compressobj_method_check(self):
        """Only DEFLATED method (8) should be accepted."""
        with pytest.raises(ValueError):
            zlib_rs.compressobj(method=0)


class TestCrossCompatibility:
    """Ensure full cross-compatibility between zlib_rs and cpython zlib."""

    @pytest.mark.parametrize("level", [1, 6, 9])
    def test_oneshot_cross_compat(self, level):
        data = b"Cross-compat test data " * 500

        # zlib_rs -> cpython
        compressed_rs = zlib_rs.compress(data, level)
        assert cpython_zlib.decompress(compressed_rs) == data

        # cpython -> zlib_rs
        compressed_cp = cpython_zlib.compress(data, level)
        assert zlib_rs.decompress(compressed_cp) == data

    def test_streaming_cross_compat(self):
        data = b"Streaming cross-compat " * 1000

        # zlib_rs stream -> cpython decompress
        c = zlib_rs.compressobj(6)
        compressed = c.compress(data) + c.flush()
        assert cpython_zlib.decompress(compressed) == data

        # cpython stream -> zlib_rs stream decompress
        c2 = cpython_zlib.compressobj(6)
        compressed2 = c2.compress(data) + c2.flush()
        d = zlib_rs.decompressobj()
        assert d.decompress(compressed2) == data

    def test_checksum_cross_compat(self):
        """Checksums should match exactly for any input."""
        test_cases = [
            b"",
            b"a",
            b"Hello, World!",
            bytes(range(256)),
            b"\x00" * 10000,
            b"x" * 100000,
        ]
        for data in test_cases:
            assert zlib_rs.adler32(data) == cpython_zlib.adler32(data), \
                f"adler32 mismatch for data of length {len(data)}"
            assert zlib_rs.crc32(data) == cpython_zlib.crc32(data), \
                f"crc32 mismatch for data of length {len(data)}"
