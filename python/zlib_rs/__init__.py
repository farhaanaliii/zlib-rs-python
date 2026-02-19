"""
zlib-rs-python: High-performance Python bindings for zlib-rs (Rust).

A drop-in replacement for Python's built-in zlib module, powered by
a memory-safe Rust implementation. Up to 22x faster compression and
17x faster checksums.

Usage:
    import zlib_rs as zlib

    compressed = zlib.compress(b"Hello, world!")
    original = zlib.decompress(compressed)
"""

from .zlib_rs import *  # noqa: F401, F403

__version__ = "0.1.1"
__author__ = "Farhaan Ali"
__license__ = "MIT"
