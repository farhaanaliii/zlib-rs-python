"""
Test one-shot compress and decompress operations.
"""

import os
import zlib as cpython_zlib
import pytest
import zlib_rs


class TestCompress:
    """Tests for zlib_rs.compress()."""

    def test_basic_roundtrip(self):
        data = b"Hello, world!"
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_empty_data(self):
        compressed = zlib_rs.compress(b"")
        assert zlib_rs.decompress(compressed) == b""

    def test_single_byte(self):
        data = b"\x42"
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_repeated_bytes(self):
        data = b"\x00" * 100000
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data
        # Highly compressible data should be much smaller
        assert len(compressed) < len(data) // 10

    @pytest.mark.parametrize("level", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_all_compression_levels(self, level):
        data = b"Test data for compression level " * 100
        compressed = zlib_rs.compress(data, level)
        assert zlib_rs.decompress(compressed) == data

    def test_default_level(self):
        data = b"Default compression level test" * 500
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_no_compression_level_zero(self):
        data = b"No compression" * 100
        compressed = zlib_rs.compress(data, 0)
        assert zlib_rs.decompress(compressed) == data
        # Level 0 output should be larger than or roughly equal to input
        # (it adds headers but doesn't compress)

    def test_best_speed(self):
        data = b"Speed test" * 10000
        compressed = zlib_rs.compress(data, 1)
        assert zlib_rs.decompress(compressed) == data

    def test_best_compression(self):
        data = b"Compression test" * 10000
        compressed = zlib_rs.compress(data, 9)
        assert zlib_rs.decompress(compressed) == data

    def test_large_data(self):
        data = os.urandom(1024 * 1024)  # 1 MB random data
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed, bufsize=len(data) * 2) == data

    def test_binary_data(self):
        data = bytes(range(256)) * 100
        compressed = zlib_rs.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_unicode_encoded(self):
        text = "Hello, \u4e16\u754c! \U0001f600 Multilingual test \u00e9\u00e0\u00fc\u00f1"
        data = text.encode("utf-8")
        compressed = zlib_rs.compress(data)
        result = zlib_rs.decompress(compressed)
        assert result.decode("utf-8") == text


class TestDecompress:
    """Tests for zlib_rs.decompress()."""

    def test_decompress_cpython_compressed(self):
        """Data compressed by CPython zlib should decompress correctly."""
        data = b"Cross-implementation compatibility" * 500
        compressed = cpython_zlib.compress(data)
        assert zlib_rs.decompress(compressed) == data

    def test_compress_for_cpython_decompress(self):
        """Data compressed by zlib_rs should decompress in CPython."""
        data = b"Reverse compatibility test" * 500
        compressed = zlib_rs.compress(data)
        assert cpython_zlib.decompress(compressed) == data

    @pytest.mark.parametrize("level", [1, 6, 9])
    def test_cross_compat_all_levels(self, level):
        data = b"Level compatibility " * 1000
        # zlib_rs -> cpython
        assert cpython_zlib.decompress(zlib_rs.compress(data, level)) == data
        # cpython -> zlib_rs
        assert zlib_rs.decompress(cpython_zlib.compress(data, level)) == data

    def test_decompress_with_bufsize(self):
        data = b"Buffer size test" * 1000
        compressed = zlib_rs.compress(data)
        result = zlib_rs.decompress(compressed, bufsize=len(data) * 2)
        assert result == data

    def test_decompress_small_bufsize_grows(self):
        """Decompression should handle small initial bufsize by growing."""
        data = b"X" * 50000
        compressed = zlib_rs.compress(data)
        result = zlib_rs.decompress(compressed, bufsize=64)
        assert result == data
