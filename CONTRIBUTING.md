# Contributing to zlib-rs-python

Thank you for considering contributing to this project. Contributions of all kinds are welcome, including bug reports, feature requests, documentation improvements, and code contributions.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/farhaanaliii/zlib-rs-python.git
cd zlib-rs-python
```

3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows

pip install maturin pytest
```

4. Build the project:

```bash
maturin develop
```

5. Run the tests to make sure everything works:

```bash
pytest tests/ -v
```

## Making Changes

1. Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes. If modifying Rust code in `src/lib.rs`, rebuild with:

```bash
maturin develop
```

3. Run tests after every change:

```bash
pytest tests/ -v
```

4. If your change could affect performance, run the benchmarks:

```bash
maturin develop --release
python benchmarks/bench_zlib.py
```

## Code Style

- **Rust**: Follow standard Rust conventions. Use 4-space indentation.
- **Python**: Follow PEP 8. Use 4-space indentation.
- Keep functions focused and well-documented.

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a pull request against the `main` branch of this repository.
3. Provide a clear description of what your changes do and why.
4. Ensure all CI checks pass.

## Reporting Issues

When reporting a bug, please include:

- Python version (`python --version`)
- Operating system and version
- Steps to reproduce the issue
- Expected vs actual behavior
- Full error traceback (if applicable)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
