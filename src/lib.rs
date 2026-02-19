use ::zlib_rs::{Deflate, DeflateFlush, Inflate, InflateFlush, ReturnCode, Status};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

pyo3::import_exception!(zlib, error);

/// Compute an Adler-32 checksum of data.
#[pyfunction]
#[pyo3(signature = (data, value = 1))]
fn adler32(data: &[u8], value: u32) -> u32 {
    ::zlib_rs::adler32::adler32(value, data)
}

/// Compute a CRC-32 checksum of data.
#[pyfunction]
#[pyo3(signature = (data, value = 0))]
fn crc32(data: &[u8], value: u32) -> u32 {
    ::zlib_rs::crc32::crc32(value, data)
}

/// Returns a bytes object containing compressed data.
#[pyfunction]
#[pyo3(signature = (data, level = -1))]
fn compress(py: Python<'_>, data: &[u8], level: i32) -> PyResult<Py<PyBytes>> {
    let config = ::zlib_rs::DeflateConfig::new(level);
    let bound = ::zlib_rs::compress_bound(data.len());
    let mut output = vec![0u8; bound];

    let (compressed, rc) = ::zlib_rs::compress_slice(&mut output, data, config);
    match rc {
        ReturnCode::Ok | ReturnCode::StreamEnd => {
            let size = compressed.len();
            Ok(PyBytes::new(py, &output[..size]).unbind())
        }
        _ => Err(PyErr::new::<error, _>(format!(
            "Error while compressing: {:?}",
            rc
        ))),
    }
}

/// Returns a bytes object containing decompressed data.
///
/// Uses progressive buffer growth to handle unknown output sizes efficiently.
#[pyfunction]
#[pyo3(signature = (data, wbits = 15, bufsize = 16384))]
fn decompress(py: Python<'_>, data: &[u8], wbits: i32, bufsize: usize) -> PyResult<Py<PyBytes>> {
    let config = ::zlib_rs::InflateConfig { window_bits: wbits };

    // Try with initial buffer size, grow if needed
    let initial_size = bufsize.max(data.len() * 4);
    let mut output = vec![0u8; initial_size];

    let (decompressed, rc) = ::zlib_rs::decompress_slice(&mut output, data, config);
    match rc {
        ReturnCode::Ok | ReturnCode::StreamEnd => {
            let size = decompressed.len();
            Ok(PyBytes::new(py, &output[..size]).unbind())
        }
        ReturnCode::BufError => {
            // Buffer was too small, retry with larger buffer
            let mut size = initial_size * 4;
            loop {
                output.resize(size, 0);
                let (decompressed, rc) = ::zlib_rs::decompress_slice(&mut output, data, config);
                match rc {
                    ReturnCode::Ok | ReturnCode::StreamEnd => {
                        let len = decompressed.len();
                        return Ok(PyBytes::new(py, &output[..len]).unbind());
                    }
                    ReturnCode::BufError => {
                        size *= 2;
                        if size > 256 * 1024 * 1024 {
                            return Err(PyErr::new::<error, _>("Decompressed data is too large"));
                        }
                    }
                    _ => {
                        return Err(PyErr::new::<error, _>(format!(
                            "Error while decompressing: {:?}",
                            rc
                        )));
                    }
                }
            }
        }
        _ => Err(PyErr::new::<error, _>(format!(
            "Error while decompressing: {:?}",
            rc
        ))),
    }
}

/// Determine whether wbits indicates a zlib header is present.
#[inline(always)]
fn parse_wbits(wbits: i32) -> (bool, u8) {
    if wbits < 0 {
        (false, (-wbits).min(15) as u8)
    } else if wbits > 15 {
        (true, (wbits - 16).max(8).min(15) as u8)
    } else {
        (true, wbits.max(8).min(15) as u8)
    }
}

/// Streaming compression object.
#[pyclass]
struct Compress {
    inner: Deflate,
    /// Reusable scratch buffer to avoid per-call allocations.
    buf: Vec<u8>,
}

#[pymethods]
impl Compress {
    /// Feed data into the compression object; returns a bytes object.
    #[pyo3(signature = (data))]
    fn compress(&mut self, py: Python<'_>, data: &[u8]) -> PyResult<Py<PyBytes>> {
        let needed = ::zlib_rs::compress_bound(data.len()) + 64;
        if self.buf.len() < needed {
            self.buf.resize(needed, 0);
        }

        let old_total_out = self.inner.total_out();

        match self
            .inner
            .compress(data, &mut self.buf, DeflateFlush::NoFlush)
        {
            Ok(_) => {
                let written = (self.inner.total_out() - old_total_out) as usize;
                Ok(PyBytes::new(py, &self.buf[..written]).unbind())
            }
            Err(e) => Err(PyErr::new::<error, _>(format!(
                "Error while compressing: {:?}",
                e
            ))),
        }
    }

    /// Returns a bytes object containing any remaining compressed data.
    #[pyo3(signature = (mode = 4))]
    fn flush(&mut self, py: Python<'_>, mode: i32) -> PyResult<Py<PyBytes>> {
        let flush_mode = match mode {
            0 => DeflateFlush::NoFlush,
            1 => DeflateFlush::PartialFlush,
            2 => DeflateFlush::SyncFlush,
            3 => DeflateFlush::FullFlush,
            4 => DeflateFlush::Finish,
            _ => return Err(PyValueError::new_err("Invalid flush mode")),
        };

        if self.buf.len() < 32768 {
            self.buf.resize(32768, 0);
        }

        let mut all_output = Vec::with_capacity(4096);

        loop {
            let old_total_out = self.inner.total_out();
            match self.inner.compress(&[], &mut self.buf, flush_mode) {
                Ok(status) => {
                    let written = (self.inner.total_out() - old_total_out) as usize;
                    all_output.extend_from_slice(&self.buf[..written]);

                    if status == Status::StreamEnd
                        || (written < self.buf.len() && flush_mode != DeflateFlush::Finish)
                    {
                        break;
                    }
                }
                Err(e) => {
                    return Err(PyErr::new::<error, _>(format!(
                        "Error while flushing: {:?}",
                        e
                    )))
                }
            }
        }

        Ok(PyBytes::new(py, &all_output).unbind())
    }
}

/// Streaming decompression object.
#[pyclass]
struct Decompress {
    inner: Inflate,
    /// Reusable scratch buffer to avoid per-call allocations.
    buf: Vec<u8>,
    #[pyo3(get)]
    unused_data: Py<PyBytes>,
    #[pyo3(get)]
    unconsumed_tail: Py<PyBytes>,
    #[pyo3(get)]
    eof: bool,
}

#[pymethods]
impl Decompress {
    /// Decompress data; returns a bytes object.
    #[pyo3(signature = (data, max_length = 0))]
    fn decompress(
        &mut self,
        py: Python<'_>,
        data: &[u8],
        max_length: usize,
    ) -> PyResult<Py<PyBytes>> {
        // Ensure scratch buffer is large enough
        let buf_size = (data.len() * 4).max(32768);
        if self.buf.len() < buf_size {
            self.buf.resize(buf_size, 0);
        }

        let mut all_output = Vec::with_capacity(data.len() * 2);
        let mut input_offset = 0;

        self.unconsumed_tail = PyBytes::new(py, &[]).unbind();

        while input_offset < data.len() || all_output.is_empty() {
            let old_total_out = self.inner.total_out();
            let old_total_in = self.inner.total_in();
            let input = &data[input_offset..];

            match self
                .inner
                .decompress(input, &mut self.buf, InflateFlush::NoFlush)
            {
                Ok(status) => {
                    let written = (self.inner.total_out() - old_total_out) as usize;
                    let consumed = (self.inner.total_in() - old_total_in) as usize;

                    all_output.extend_from_slice(&self.buf[..written]);
                    input_offset += consumed;

                    if max_length > 0 && all_output.len() >= max_length {
                        all_output.truncate(max_length);
                        if input_offset < data.len() {
                            self.unconsumed_tail = PyBytes::new(py, &data[input_offset..]).unbind();
                        }
                        break;
                    }

                    if status == Status::StreamEnd {
                        self.eof = true;
                        if input_offset < data.len() {
                            let current_unused = self.unused_data.bind(py).as_bytes();
                            let mut new_unused = Vec::from(current_unused);
                            new_unused.extend_from_slice(&data[input_offset..]);
                            self.unused_data = PyBytes::new(py, &new_unused).unbind();
                        }
                        break;
                    }
                    if written < self.buf.len() && input.is_empty() {
                        break;
                    }
                }
                Err(e) => {
                    return Err(PyErr::new::<error, _>(format!(
                        "Error while decompressing: {:?}",
                        e
                    )))
                }
            }
        }

        Ok(PyBytes::new(py, &all_output).unbind())
    }
}

/// Returns a compression object.
#[pyfunction]
#[pyo3(signature = (level = -1, method = 8, wbits = 15, mem_level = 8, strategy = 0, zdict = None))]
fn compressobj(
    level: i32,
    method: i32,
    wbits: i32,
    mem_level: i32,
    strategy: i32,
    zdict: Option<&[u8]>,
) -> PyResult<Compress> {
    if method != 8 {
        return Err(PyValueError::new_err("Only DEFLATED method is supported"));
    }

    let _ = mem_level;
    let _ = strategy;

    let (zlib_header, window_bits) = parse_wbits(wbits);
    let mut inner = Deflate::new(level, zlib_header, window_bits);

    if let Some(dict) = zdict {
        inner
            .set_dictionary(dict)
            .map_err(|e| PyErr::new::<error, _>(format!("Error setting dictionary: {:?}", e)))?;
    }

    Ok(Compress {
        inner,
        buf: Vec::with_capacity(32768),
    })
}

/// Returns a decompression object.
#[pyfunction]
#[pyo3(signature = (wbits = 15, zdict = None))]
fn decompressobj(py: Python<'_>, wbits: i32, zdict: Option<&[u8]>) -> PyResult<Decompress> {
    let (zlib_header, window_bits) = parse_wbits(wbits);
    let mut inner = Inflate::new(zlib_header, window_bits);

    if let Some(dict) = zdict {
        inner
            .set_dictionary(dict)
            .map_err(|e| PyErr::new::<error, _>(format!("Error setting dictionary: {:?}", e)))?;
    }

    Ok(Decompress {
        inner,
        buf: Vec::with_capacity(32768),
        unused_data: PyBytes::new(py, &[]).unbind(),
        unconsumed_tail: PyBytes::new(py, &[]).unbind(),
        eof: false,
    })
}

#[pymodule]
fn zlib_rs(py: Python<'_>, m: &Bound<'_, pyo3::types::PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(adler32, m)?)?;
    m.add_function(wrap_pyfunction!(crc32, m)?)?;
    m.add_function(wrap_pyfunction!(compress, m)?)?;
    m.add_function(wrap_pyfunction!(decompress, m)?)?;
    m.add_function(wrap_pyfunction!(compressobj, m)?)?;
    m.add_function(wrap_pyfunction!(decompressobj, m)?)?;

    m.add_class::<Compress>()?;
    m.add_class::<Decompress>()?;

    let zlib_mod = py.import("zlib")?;
    let zlib_error = zlib_mod.getattr("error")?;
    m.add("error", zlib_error)?;

    // Constants
    m.add("Z_NO_COMPRESSION", 0)?;
    m.add("Z_BEST_SPEED", 1)?;
    m.add("Z_BEST_COMPRESSION", 9)?;
    m.add("Z_DEFAULT_COMPRESSION", -1)?;

    // Strategies
    m.add("Z_FILTERED", 1)?;
    m.add("Z_HUFFMAN_ONLY", 2)?;
    m.add("Z_RLE", 3)?;
    m.add("Z_FIXED", 4)?;
    m.add("Z_DEFAULT_STRATEGY", 0)?;

    // Methods
    m.add("Z_DEFLATED", 8)?;

    // Flush modes
    m.add("Z_NO_FLUSH", 0)?;
    m.add("Z_PARTIAL_FLUSH", 1)?;
    m.add("Z_SYNC_FLUSH", 2)?;
    m.add("Z_FULL_FLUSH", 3)?;
    m.add("Z_FINISH", 4)?;
    m.add("Z_BLOCK", 5)?;
    m.add("Z_TREES", 6)?;

    m.add("DEF_MEM_LEVEL", 8)?;
    m.add("MAX_WBITS", 15)?;

    m.add("ZLIB_VERSION", "1.2.11")?;
    m.add("ZLIB_RUNTIME_VERSION", "zlib-rs-0.6.2")?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // -----------------------------------------------------------------------
    // parse_wbits
    // -----------------------------------------------------------------------

    #[test]
    fn test_parse_wbits_positive() {
        let (header, bits) = parse_wbits(15);
        assert!(header);
        assert_eq!(bits, 15);
    }

    #[test]
    fn test_parse_wbits_default() {
        let (header, bits) = parse_wbits(15);
        assert!(header);
        assert_eq!(bits, 15);
    }

    #[test]
    fn test_parse_wbits_negative_raw() {
        let (header, bits) = parse_wbits(-15);
        assert!(!header);
        assert_eq!(bits, 15);
    }

    #[test]
    fn test_parse_wbits_negative_small() {
        let (header, bits) = parse_wbits(-9);
        assert!(!header);
        assert_eq!(bits, 9);
    }

    #[test]
    fn test_parse_wbits_gzip_mode() {
        // wbits > 15 indicates gzip
        let (header, bits) = parse_wbits(31);
        assert!(header);
        assert_eq!(bits, 15);
    }

    #[test]
    fn test_parse_wbits_gzip_small() {
        let (header, bits) = parse_wbits(25);
        assert!(header);
        assert_eq!(bits, 9);
    }

    #[test]
    fn test_parse_wbits_clamp_low() {
        let (header, bits) = parse_wbits(1);
        assert!(header);
        assert_eq!(bits, 8); // min is 8
    }

    #[test]
    fn test_parse_wbits_clamp_negative_high() {
        let (header, bits) = parse_wbits(-20);
        assert!(!header);
        assert_eq!(bits, 15); // clamped to 15
    }

    // -----------------------------------------------------------------------
    // Direct zlib-rs roundtrip (no Python)
    // -----------------------------------------------------------------------

    #[test]
    fn test_compress_decompress_roundtrip() {
        let data = b"Hello, world! This is a test of zlib-rs compression.";
        let config = ::zlib_rs::DeflateConfig::new(-1);
        let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len())];

        let compressed_len = {
            let (compressed, rc) = ::zlib_rs::compress_slice(&mut output, data, config);
            assert_eq!(rc, ::zlib_rs::ReturnCode::Ok);
            compressed.len()
        };

        let inflate_config = ::zlib_rs::InflateConfig { window_bits: 15 };
        let mut decompressed = vec![0u8; data.len() * 2];
        let (result, rc) = ::zlib_rs::decompress_slice(
            &mut decompressed,
            &output[..compressed_len],
            inflate_config,
        );
        assert!(rc == ::zlib_rs::ReturnCode::Ok || rc == ::zlib_rs::ReturnCode::StreamEnd);
        assert_eq!(result, data);
    }

    #[test]
    fn test_compress_empty() {
        let data = b"";
        let config = ::zlib_rs::DeflateConfig::new(-1);
        let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len())];

        let compressed_len = {
            let (compressed, rc) = ::zlib_rs::compress_slice(&mut output, data, config);
            assert_eq!(rc, ::zlib_rs::ReturnCode::Ok);
            compressed.len()
        };

        let inflate_config = ::zlib_rs::InflateConfig { window_bits: 15 };
        let mut decompressed = vec![0u8; 256];
        let (result, rc) = ::zlib_rs::decompress_slice(
            &mut decompressed,
            &output[..compressed_len],
            inflate_config,
        );
        assert!(rc == ::zlib_rs::ReturnCode::Ok || rc == ::zlib_rs::ReturnCode::StreamEnd);
        assert_eq!(result, b"");
    }

    #[test]
    fn test_compress_all_levels() {
        let data = b"Test data for all compression levels ".repeat(100);
        for level in 0..=9 {
            let config = ::zlib_rs::DeflateConfig::new(level);
            let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len())];

            let compressed_len = {
                let (compressed, rc) = ::zlib_rs::compress_slice(&mut output, &data, config);
                assert!(
                    rc == ::zlib_rs::ReturnCode::Ok || rc == ::zlib_rs::ReturnCode::StreamEnd,
                    "compress failed at level {}",
                    level
                );
                compressed.len()
            };

            let inflate_config = ::zlib_rs::InflateConfig { window_bits: 15 };
            let mut decompressed = vec![0u8; data.len() * 2];
            let (result, drc) = ::zlib_rs::decompress_slice(
                &mut decompressed,
                &output[..compressed_len],
                inflate_config,
            );
            assert!(
                drc == ::zlib_rs::ReturnCode::Ok || drc == ::zlib_rs::ReturnCode::StreamEnd,
                "decompress failed at level {}",
                level
            );
            assert_eq!(result, &data[..], "roundtrip failed at level {}", level);
        }
    }

    #[test]
    fn test_compress_large_data() {
        let data = vec![0x42u8; 1024 * 1024]; // 1 MB
        let config = ::zlib_rs::DeflateConfig::new(6);
        let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len())];

        let compressed_len = {
            let (compressed, rc) = ::zlib_rs::compress_slice(&mut output, &data, config);
            assert_eq!(rc, ::zlib_rs::ReturnCode::Ok);
            compressed.len()
        };

        let inflate_config = ::zlib_rs::InflateConfig { window_bits: 15 };
        let mut decompressed = vec![0u8; data.len() * 2];
        let (result, drc) = ::zlib_rs::decompress_slice(
            &mut decompressed,
            &output[..compressed_len],
            inflate_config,
        );
        assert!(drc == ::zlib_rs::ReturnCode::Ok || drc == ::zlib_rs::ReturnCode::StreamEnd);
        assert_eq!(result, &data[..]);
    }

    // -----------------------------------------------------------------------
    // Checksum tests
    // -----------------------------------------------------------------------

    #[test]
    fn test_adler32_empty() {
        let result = ::zlib_rs::adler32::adler32(1, b"");
        assert_eq!(result, 1); // adler32 of empty data with init=1 is 1
    }

    #[test]
    fn test_adler32_hello() {
        let result = ::zlib_rs::adler32::adler32(1, b"Hello");
        assert_ne!(result, 0);
        assert_ne!(result, 1);
    }

    #[test]
    fn test_adler32_incremental() {
        let data = b"Hello, World!";
        let full = ::zlib_rs::adler32::adler32(1, data);

        let partial = ::zlib_rs::adler32::adler32(1, &data[..5]);
        let incremental = ::zlib_rs::adler32::adler32(partial, &data[5..]);

        assert_eq!(full, incremental);
    }

    #[test]
    fn test_crc32_empty() {
        let result = ::zlib_rs::crc32::crc32(0, b"");
        assert_eq!(result, 0);
    }

    #[test]
    fn test_crc32_hello() {
        let result = ::zlib_rs::crc32::crc32(0, b"Hello");
        assert_ne!(result, 0);
    }

    #[test]
    fn test_crc32_incremental() {
        let data = b"Hello, World!";
        let full = ::zlib_rs::crc32::crc32(0, data);

        let partial = ::zlib_rs::crc32::crc32(0, &data[..5]);
        let incremental = ::zlib_rs::crc32::crc32(partial, &data[5..]);

        assert_eq!(full, incremental);
    }

    #[test]
    fn test_crc32_all_bytes() {
        let data: Vec<u8> = (0..=255).collect();
        let result = ::zlib_rs::crc32::crc32(0, &data);
        assert_ne!(result, 0);
    }

    // -----------------------------------------------------------------------
    // Streaming (Deflate / Inflate) tests
    // -----------------------------------------------------------------------

    #[test]
    fn test_deflate_inflate_roundtrip() {
        let data = b"Streaming roundtrip test data ".repeat(100);
        let mut deflater = Deflate::new(6, true, 15);
        let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len()) + 128];

        let result = deflater.compress(&data, &mut output, DeflateFlush::Finish);
        assert!(result.is_ok());

        let total_compressed = deflater.total_out() as usize;

        let mut inflater = Inflate::new(true, 15);
        let mut decompressed = vec![0u8; data.len() * 2];

        let result = inflater.decompress(
            &output[..total_compressed],
            &mut decompressed,
            InflateFlush::NoFlush,
        );
        assert!(result.is_ok());

        let total_decompressed = inflater.total_out() as usize;
        assert_eq!(&decompressed[..total_decompressed], &data[..]);
    }

    #[test]
    fn test_deflate_empty() {
        let mut deflater = Deflate::new(6, true, 15);
        let mut output = vec![0u8; 256];

        let result = deflater.compress(b"", &mut output, DeflateFlush::Finish);
        assert!(result.is_ok());

        let total_compressed = deflater.total_out() as usize;

        let mut inflater = Inflate::new(true, 15);
        let mut decompressed = vec![0u8; 256];

        let result = inflater.decompress(
            &output[..total_compressed],
            &mut decompressed,
            InflateFlush::NoFlush,
        );
        assert!(result.is_ok());

        let total_decompressed = inflater.total_out() as usize;
        assert_eq!(total_decompressed, 0);
    }

    #[test]
    fn test_deflate_all_levels() {
        let data = b"Level test ".repeat(200);
        for level in [1, 3, 6, 9] {
            let mut deflater = Deflate::new(level, true, 15);
            let mut output = vec![0u8; ::zlib_rs::compress_bound(data.len()) + 128];

            let result = deflater.compress(&data, &mut output, DeflateFlush::Finish);
            assert!(result.is_ok(), "deflate failed at level {}", level);

            let total = deflater.total_out() as usize;

            let mut inflater = Inflate::new(true, 15);
            let mut decompressed = vec![0u8; data.len() * 2];

            let result =
                inflater.decompress(&output[..total], &mut decompressed, InflateFlush::NoFlush);
            assert!(result.is_ok(), "inflate failed at level {}", level);

            let total_out = inflater.total_out() as usize;
            assert_eq!(
                &decompressed[..total_out],
                &data[..],
                "mismatch at level {}",
                level
            );
        }
    }

    // -----------------------------------------------------------------------
    // Compress bound
    // -----------------------------------------------------------------------

    #[test]
    fn test_compress_bound_zero() {
        let bound = ::zlib_rs::compress_bound(0);
        assert!(bound > 0);
    }

    #[test]
    fn test_compress_bound_increases() {
        let b1 = ::zlib_rs::compress_bound(100);
        let b2 = ::zlib_rs::compress_bound(1000);
        let b3 = ::zlib_rs::compress_bound(10000);
        assert!(b1 < b2);
        assert!(b2 < b3);
    }

    #[test]
    fn test_compress_bound_sufficient() {
        // The bound should always be sufficient for compression output
        for size in [0, 1, 10, 100, 1000, 10000, 100000] {
            let data = vec![0x42u8; size];
            let bound = ::zlib_rs::compress_bound(size);
            let config = ::zlib_rs::DeflateConfig::new(1);
            let mut output = vec![0u8; bound];

            let (_, rc) = ::zlib_rs::compress_slice(&mut output, &data, config);
            assert!(
                rc == ::zlib_rs::ReturnCode::Ok || rc == ::zlib_rs::ReturnCode::StreamEnd,
                "compress_bound insufficient for size {}",
                size
            );
        }
    }
}
