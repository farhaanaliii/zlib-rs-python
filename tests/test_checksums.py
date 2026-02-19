"""
Test checksum functions: adler32 and crc32.
"""

import zlib as cpython_zlib
import pytest
import zlib_rs


class TestAdler32:
    """Tests for zlib_rs.adler32()."""

    def test_empty_data(self):
        assert zlib_rs.adler32(b"") == cpython_zlib.adler32(b"")

    def test_single_byte(self):
        assert zlib_rs.adler32(b"a") == cpython_zlib.adler32(b"a")

    def test_known_value(self):
        # Known adler32 of "Hello" with default initial value 1
        result = zlib_rs.adler32(b"Hello")
        expected = cpython_zlib.adler32(b"Hello")
        assert result == expected

    def test_matches_cpython(self):
        data = b"The quick brown fox jumps over the lazy dog"
        assert zlib_rs.adler32(data) == cpython_zlib.adler32(data)

    def test_custom_initial_value(self):
        data = b"test data"
        initial = 42
        assert zlib_rs.adler32(data, initial) == cpython_zlib.adler32(data, initial)

    def test_incremental(self):
        """Incremental adler32 should match full computation."""
        data = b"Hello, World!"
        full = zlib_rs.adler32(data)

        # Compute incrementally
        partial = zlib_rs.adler32(data[:5])
        incremental = zlib_rs.adler32(data[5:], partial)

        # Compare with cpython incremental
        cp_partial = cpython_zlib.adler32(data[:5])
        cp_incremental = cpython_zlib.adler32(data[5:], cp_partial)
        assert incremental == cp_incremental

    def test_all_byte_values(self):
        data = bytes(range(256))
        assert zlib_rs.adler32(data) == cpython_zlib.adler32(data)

    def test_large_data(self):
        data = b"x" * (1024 * 1024)  # 1 MB
        assert zlib_rs.adler32(data) == cpython_zlib.adler32(data)

    @pytest.mark.parametrize("size", [1, 10, 100, 1000, 10000, 100000])
    def test_various_sizes(self, size):
        data = b"A" * size
        assert zlib_rs.adler32(data) == cpython_zlib.adler32(data)

    def test_default_value_is_1(self):
        """Default initial value should be 1 (adler32 convention)."""
        data = b"test"
        # Explicitly passing 1 should match default
        assert zlib_rs.adler32(data) == zlib_rs.adler32(data, 1)


class TestCrc32:
    """Tests for zlib_rs.crc32()."""

    def test_empty_data(self):
        assert zlib_rs.crc32(b"") == cpython_zlib.crc32(b"")

    def test_single_byte(self):
        assert zlib_rs.crc32(b"a") == cpython_zlib.crc32(b"a")

    def test_known_value(self):
        result = zlib_rs.crc32(b"Hello")
        expected = cpython_zlib.crc32(b"Hello")
        assert result == expected

    def test_matches_cpython(self):
        data = b"The quick brown fox jumps over the lazy dog"
        assert zlib_rs.crc32(data) == cpython_zlib.crc32(data)

    def test_custom_initial_value(self):
        data = b"test data"
        initial = 0xDEADBEEF
        assert zlib_rs.crc32(data, initial) == cpython_zlib.crc32(data, initial)

    def test_incremental(self):
        """Incremental crc32 should match full computation."""
        data = b"Hello, World!"
        full = zlib_rs.crc32(data)

        partial = zlib_rs.crc32(data[:5])
        incremental = zlib_rs.crc32(data[5:], partial)

        cp_partial = cpython_zlib.crc32(data[:5])
        cp_incremental = cpython_zlib.crc32(data[5:], cp_partial)
        assert incremental == cp_incremental

    def test_all_byte_values(self):
        data = bytes(range(256))
        assert zlib_rs.crc32(data) == cpython_zlib.crc32(data)

    def test_large_data(self):
        data = b"y" * (1024 * 1024)  # 1 MB
        assert zlib_rs.crc32(data) == cpython_zlib.crc32(data)

    @pytest.mark.parametrize("size", [1, 10, 100, 1000, 10000, 100000])
    def test_various_sizes(self, size):
        data = b"B" * size
        assert zlib_rs.crc32(data) == cpython_zlib.crc32(data)

    def test_default_value_is_0(self):
        """Default initial value should be 0 (crc32 convention)."""
        data = b"test"
        assert zlib_rs.crc32(data) == zlib_rs.crc32(data, 0)
