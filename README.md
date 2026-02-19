> **Notice:** This project was built entirely with AI assistance and is an experimental proof of concept.
> It is not intended for production use. Use at your own risk.

# zlib-rs-python

[![CI](https://github.com/farhaanaliii/zlib-rs-python/actions/workflows/CI.yml/badge.svg)](https://github.com/farhaanaliii/zlib-rs-python/actions/workflows/CI.yml)
[![PyPI](https://img.shields.io/pypi/v/zlib-rs.svg)](https://pypi.org/project/zlib-rs/)
[![Python Versions](https://img.shields.io/pypi/pyversions/zlib-rs.svg)](https://pypi.org/project/zlib-rs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A high-performance, memory-safe Python binding for the [zlib-rs](https://github.com/trifectatechfoundation/zlib-rs) Rust crate. Up to **22x faster** than CPython's built-in `zlib` module.

## Features

- **High Performance** -- Up to 22x faster compression and 17x faster checksums compared to CPython's built-in zlib (see [benchmarks](#benchmarks)).
- **Memory Safe** -- Built on top of `zlib-rs`, a memory-safe, pure-Rust implementation of the zlib compression algorithm.
- **Drop-in Compatible** -- Follows the standard Python `zlib` API. Swap imports and go.
- **Cross-Platform** -- Builds and runs on Linux, macOS, and Windows with no C dependencies.
- **Zero C Dependencies** -- No system zlib headers or C compiler required. Everything is compiled from Rust source.

## Installation

### From PyPI

```bash
pip install zlib-rs
```

### From Source

```bash
pip install maturin
git clone https://github.com/farhaanaliii/zlib-rs-python.git
cd zlib-rs-python
maturin develop --release
```

## Quick Start

```python
import zlib_rs as zlib

# One-shot compression
data = b"Hello, zlib-rs!" * 1000
compressed = zlib.compress(data)
original = zlib.decompress(compressed)
assert data == original

# Streaming compression
compressor = zlib.compressobj(level=6)
compressed = compressor.compress(data)
compressed += compressor.flush()

decompressor = zlib.decompressobj()
result = decompressor.decompress(compressed)
assert data == result

# Checksums
checksum_adler = zlib.adler32(data)
checksum_crc = zlib.crc32(data)
```

### Drop-in Replacement

To use `zlib-rs` globally in an existing project without changing every import:

```python
import sys
import zlib_rs

sys.modules["zlib"] = zlib_rs

# Now any library importing 'zlib' will use 'zlib-rs' instead
import zlib
compressed = zlib.compress(b"transparent replacement")
```

## API Reference

| Function / Class | Description |
|---|---|
| `compress(data, level=-1)` | One-shot compression. Returns compressed bytes. |
| `decompress(data, wbits=15, bufsize=16384)` | One-shot decompression. Returns original bytes. |
| `compressobj(level, method, wbits, ...)` | Create a streaming compression object. |
| `decompressobj(wbits, zdict)` | Create a streaming decompression object. |
| `adler32(data, value=1)` | Compute Adler-32 checksum. |
| `crc32(data, value=0)` | Compute CRC-32 checksum. |

All standard zlib constants are available: `Z_BEST_COMPRESSION`, `Z_BEST_SPEED`, `Z_DEFAULT_COMPRESSION`, `Z_DEFAULT_STRATEGY`, `Z_DEFLATED`, `Z_FINISH`, `Z_NO_FLUSH`, `Z_SYNC_FLUSH`, `MAX_WBITS`, `DEF_MEM_LEVEL`, etc.

## Benchmarks

All benchmarks measured on Windows, Python 3.12, with release optimizations
(`lto = "fat"`, `codegen-units = 1`, `target-cpu=native`).

### One-Shot Compression

| Data Size | Level | CPython zlib | zlib-rs | Speedup |
|-----------|-------|--------------|---------|---------| 
| 1 KB | 1 | 57.2 us | 46.3 us | 1.2x faster |
| 1 KB | 6 | 62.6 us | 20.0 us | 3.1x faster |
| 64 KB | 1 | 155.6 us | 63.2 us | 2.5x faster |
| 64 KB | 6 | 398.1 us | 86.3 us | 4.6x faster |
| 1 MB | 6 | 6.45 ms | 401.4 us | **16.1x faster** |
| 10 MB | 6 | 94.60 ms | 4.22 ms | **22.4x faster** |

### One-Shot Decompression

| Data Size | Level | CPython zlib | zlib-rs | Speedup |
|-----------|-------|--------------|---------|---------| 
| 1 KB | 1 | 4.4 us | 2.3 us | 1.9x faster |
| 64 KB | 9 | 50.5 us | 15.0 us | 3.4x faster |
| 1 MB | 6 | 1.18 ms | 664.0 us | 1.8x faster |
| 10 MB | 1 | 11.99 ms | 5.86 ms | 2.0x faster |

### Checksums

| Operation | Data Size | CPython zlib | zlib-rs | Speedup |
|-----------|-----------|--------------|---------|----------|
| adler32 | 64 KB | 21.0 us | 2.0 us | 10.5x faster |
| crc32 | 64 KB | 41.9 us | 3.2 us | 13.1x faster |
| adler32 | 1 MB | 364.6 us | 33.1 us | 11.0x faster |
| crc32 | 1 MB | 814.8 us | 48.3 us | **16.9x faster** |

### Running Benchmarks

```bash
maturin develop --release
python benchmarks/bench_zlib.py
```

## Development

### Prerequisites

- [Rust](https://rustup.rs/) 1.75 or later
- Python 3.8 or later
- [maturin](https://github.com/PyO3/maturin)

### Setup

```bash
git clone https://github.com/farhaanaliii/zlib-rs-python.git
cd zlib-rs-python
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

pip install maturin pytest
```

### Build

Debug build (fast compile, slow runtime):

```bash
maturin develop
```

Release build (slow compile, fast runtime -- recommended for benchmarks):

```bash
maturin develop --release
```

### Test

```bash
pytest tests/ -v
```

### Dev Scripts

Platform-specific dev scripts are provided in the `scripts/` directory:

| Script | Description |
|---|---|
| `scripts/dev.ps1` | Windows: build, test, and benchmark |
| `scripts/dev.sh` | Linux/macOS: build, test, and benchmark |
| `scripts/release.ps1` | Windows: bump version, tag, and push release |
| `scripts/release.sh` | Linux/macOS: bump version, tag, and push release |

Usage:

```bash
# Windows (PowerShell)
.\scripts\dev.ps1 build     # Build release
.\scripts\dev.ps1 test      # Run tests
.\scripts\dev.ps1 bench     # Run benchmarks
.\scripts\dev.ps1 all       # Build + test + bench

# Linux / macOS
./scripts/dev.sh build
./scripts/dev.sh test
./scripts/dev.sh bench
./scripts/dev.sh all
```

## Project Structure

```
zlib-rs-python/
  src/
    lib.rs             # Rust source -- PyO3 bindings to zlib-rs
  python/
    zlib_rs/
      __init__.py      # Python package entry point
  tests/
    test_compatibility.py  # Basic cross-compat tests
    test_compress.py       # One-shot compress/decompress
    test_streaming.py      # Streaming operations
    test_checksums.py      # adler32/crc32
    test_edge_cases.py     # Edge cases, constants, errors
  benchmarks/
    bench_zlib.py      # Performance comparison vs CPython zlib
  scripts/
    dev.ps1            # Windows dev script
    dev.sh             # Linux/macOS dev script
    release.ps1        # Windows release script
    release.sh         # Linux/macOS release script
  .github/
    workflows/
      CI.yml           # Test + lint on push/PR
      release.yml      # Cross-platform build + PyPI publish on tag
  Cargo.toml           # Rust dependencies and release profile
  pyproject.toml       # Python package metadata (PyPI)
  LICENSE
  README.md
```

## Releasing

Releases are automated via GitHub Actions. To create a new release:

```bash
# Windows
.\scripts\release.ps1 0.2.0

# Linux / macOS
./scripts/release.sh 0.2.0
```

This will:

1. Update version in `Cargo.toml` and `__init__.py`
2. Build and test locally
3. Commit, create a `v0.2.0` tag, and push to GitHub
4. GitHub Actions then builds cross-platform wheels (Linux x86_64/aarch64, Windows x86_64, macOS x86_64/arm64)
5. Tests wheels on all platforms
6. Publishes to [PyPI](https://pypi.org/project/zlib-rs/)
7. Creates a [GitHub Release](https://github.com/farhaanaliii/zlib-rs-python/releases) with all wheel assets

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [zlib-rs](https://github.com/trifectatechfoundation/zlib-rs) -- The underlying Rust zlib implementation by the Trifecta Tech Foundation.
- [PyO3](https://github.com/PyO3/pyo3) -- Rust bindings for Python.
- [maturin](https://github.com/PyO3/maturin) -- Build system for Rust-based Python packages.
