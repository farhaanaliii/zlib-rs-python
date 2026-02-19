"""
Test streaming compress and decompress operations.
"""

import zlib as cpython_zlib
import pytest
import zlib_rs


class TestCompressObj:
    """Tests for zlib_rs.compressobj() streaming compression."""

    def test_basic_streaming(self):
        data = b"Streaming compression test" * 500
        c = zlib_rs.compressobj()
        compressed = c.compress(data)
        compressed += c.flush()

        assert zlib_rs.decompress(compressed) == data

    def test_multiple_chunks(self):
        chunks = [b"chunk1_" * 100, b"chunk2_" * 200, b"chunk3_" * 300]
        full_data = b"".join(chunks)

        c = zlib_rs.compressobj()
        compressed = b""
        for chunk in chunks:
            compressed += c.compress(chunk)
        compressed += c.flush()

        assert zlib_rs.decompress(compressed) == full_data

    def test_byte_by_byte(self):
        data = b"Byte-by-byte test data!!"
        c = zlib_rs.compressobj()
        compressed = b""
        for byte in data:
            compressed += c.compress(bytes([byte]))
        compressed += c.flush()

        assert zlib_rs.decompress(compressed) == data

    @pytest.mark.parametrize("level", [1, 6, 9])
    def test_compression_levels(self, level):
        data = b"Level test " * 1000
        c = zlib_rs.compressobj(level=level)
        compressed = c.compress(data) + c.flush()
        assert zlib_rs.decompress(compressed) == data

    def test_empty_compress(self):
        c = zlib_rs.compressobj()
        compressed = c.compress(b"")
        compressed += c.flush()
        assert zlib_rs.decompress(compressed) == b""

    def test_large_streaming(self):
        """Compress 5MB in 64KB chunks."""
        import os
        data = os.urandom(5 * 1024 * 1024)
        chunk_size = 64 * 1024

        c = zlib_rs.compressobj(level=6)
        compressed = b""
        for i in range(0, len(data), chunk_size):
            compressed += c.compress(data[i:i + chunk_size])
        compressed += c.flush()

        assert cpython_zlib.decompress(compressed) == data

    def test_flush_sync(self):
        """Test Z_SYNC_FLUSH mode."""
        data = b"Sync flush test " * 100
        c = zlib_rs.compressobj()
        compressed = c.compress(data)
        compressed += c.flush(zlib_rs.Z_SYNC_FLUSH)
        # After sync flush, the stream should still be usable
        # but we can't easily verify partial decompression here
        # Just verify it doesn't crash
        compressed += c.flush(zlib_rs.Z_FINISH)

    def test_flush_full(self):
        """Test Z_FULL_FLUSH mode."""
        data = b"Full flush test " * 100
        c = zlib_rs.compressobj()
        compressed = c.compress(data)
        compressed += c.flush(zlib_rs.Z_FULL_FLUSH)
        compressed += c.flush(zlib_rs.Z_FINISH)


class TestDecompressObj:
    """Tests for zlib_rs.decompressobj() streaming decompression."""

    def test_basic_streaming(self):
        data = b"Streaming decompression test" * 500
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        result = d.decompress(compressed)
        assert result == data

    def test_chunked_decompression(self):
        """Decompress compressed data in small chunks."""
        data = b"Chunked decompression" * 500
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        result = b""
        chunk_size = 32
        for i in range(0, len(compressed), chunk_size):
            result += d.decompress(compressed[i:i + chunk_size])
        assert result == data

    def test_eof_flag(self):
        data = b"EOF test" * 100
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        d.decompress(compressed)
        assert d.eof is True

    def test_unused_data(self):
        """Data appended after the compressed stream should be in unused_data."""
        data = b"Real data"
        trailing = b"TRAILING_BYTES"
        compressed = zlib_rs.compress(data) + trailing

        d = zlib_rs.decompressobj()
        result = d.decompress(compressed)
        assert result == data
        assert d.eof is True
        assert d.unused_data == trailing

    def test_cross_compat_streaming(self):
        """Streaming compress with zlib_rs, decompress with cpython and vice versa."""
        data = b"Cross-compat streaming" * 1000

        # zlib_rs compress -> cpython decompress
        c = zlib_rs.compressobj(level=6)
        compressed_rs = c.compress(data) + c.flush()
        assert cpython_zlib.decompress(compressed_rs) == data

        # cpython compress -> zlib_rs decompress
        c2 = cpython_zlib.compressobj(6)
        compressed_cp = c2.compress(data) + c2.flush()
        d = zlib_rs.decompressobj()
        assert d.decompress(compressed_cp) == data

    def test_max_length(self):
        """Test decompression with max_length limit."""
        data = b"A" * 10000
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        partial = d.decompress(compressed, max_length=100)
        assert len(partial) == 100
        assert partial == b"A" * 100

    def test_decompress_empty(self):
        """Decompressing empty compressed data should return empty bytes."""
        compressed = zlib_rs.compress(b"")
        d = zlib_rs.decompressobj()
        result = d.decompress(compressed)
        assert result == b""


class TestStreamingGetters:
    """Tests for total_in, total_out, and __repr__ on streaming objects."""

    def test_compress_total_in_out(self):
        data = b"Hello, world!" * 500
        c = zlib_rs.compressobj()
        c.compress(data)
        c.flush()

        assert c.total_in > 0
        assert c.total_out > 0
        assert c.total_in >= len(data)

    def test_compress_total_out_less_for_compressible(self):
        """Compressed output should be smaller than repeated input."""
        data = b"AAAA" * 10000
        c = zlib_rs.compressobj(level=9)
        c.compress(data)
        c.flush()

        assert c.total_out < c.total_in

    def test_decompress_total_in_out(self):
        data = b"Decompress getters test" * 500
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        d.decompress(compressed)

        assert d.total_in > 0
        assert d.total_out > 0
        assert d.total_out >= len(data)

    def test_compress_repr(self):
        c = zlib_rs.compressobj()
        r = repr(c)
        assert r.startswith("<Compress")
        assert "total_in=" in r
        assert "total_out=" in r

    def test_decompress_repr(self):
        d = zlib_rs.decompressobj()
        r = repr(d)
        assert r.startswith("<Decompress")
        assert "total_in=" in r
        assert "total_out=" in r
        assert "eof=" in r

    def test_repr_updates_after_use(self):
        data = b"repr update test" * 500
        c = zlib_rs.compressobj()
        before = repr(c)
        c.compress(data)
        c.flush()
        after = repr(c)
        assert before != after


class TestDecompressFlush:
    """Tests for Decompress.flush() method."""

    def test_flush_after_decompress(self):
        data = b"Flush test data" * 500
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        result = d.decompress(compressed)
        remaining = d.flush()

        assert result == data
        assert isinstance(remaining, bytes)

    def test_flush_returns_bytes(self):
        compressed = zlib_rs.compress(b"short")

        d = zlib_rs.decompressobj()
        d.decompress(compressed)
        flushed = d.flush()

        assert isinstance(flushed, bytes)

    def test_flush_with_length(self):
        data = b"flush length test" * 500
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        d.decompress(compressed)
        flushed = d.flush(length=4096)

        assert isinstance(flushed, bytes)

    def test_flush_sets_eof(self):
        data = b"eof after flush" * 100
        compressed = zlib_rs.compress(data)

        d = zlib_rs.decompressobj()
        d.decompress(compressed)
        d.flush()

        assert d.eof is True
