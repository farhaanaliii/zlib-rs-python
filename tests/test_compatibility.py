import sys
import zlib as original_zlib
try:
    import zlib_rs as zlib
    print("Using zlib-rs")
except ImportError:
    print("zlib-rs not installed, using mock for demonstration")
    zlib = original_zlib

def test_basic():
    data = b"Hello world" * 1000
    compressed = zlib.compress(data)
    decompressed = zlib.decompress(compressed)
    assert data == decompressed
    print("Basic compress/decompress: OK")

def test_streaming():
    data = b"Streaming data example" * 500
    c_obj = zlib.compressobj(level=6)
    compressed = c_obj.compress(data[:100])
    compressed += c_obj.compress(data[100:])
    compressed += c_obj.flush()
    
    d_obj = zlib.decompressobj()
    decompressed = d_obj.decompress(compressed)
    assert data == decompressed
    print("Streaming compress/decompress: OK")

def test_checksums():
    data = b"Checksum test"
    assert zlib.adler32(data) == original_zlib.adler32(data)
    assert zlib.crc32(data) == original_zlib.crc32(data)
    print("Checksums: OK")

if __name__ == "__main__":
    try:
        test_basic()
        test_streaming()
        test_checksums()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
